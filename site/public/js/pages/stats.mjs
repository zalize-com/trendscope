const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
const fmt = n => n >= 1e6 ? (n/1e6).toFixed(1)+"M" : n >= 1e3 ? (n/1e3).toFixed(1)+"k" : String(n);


const [ser, stats] = await Promise.all([
  fetch("docs/api/series.json", {cache:"no-cache"}).then(r => r.json()),
  fetch("docs/api/stats.json", {cache:"no-cache"}).then(r => r.json()).catch(() => null),
]);

const perDay = {}, perSrc = {};
let nrows = 0;
for (const it of Object.values(ser.items)) {
  for (const d of Object.keys(it.days)) {
    perDay[d] = (perDay[d] || 0) + 1;
    perSrc[it.source] = (perSrc[it.source] || 0) + 1;
    nrows++;
  }
}
const days = Object.keys(perDay).sort();
const counts = days.map(d => perDay[d]);
let cum = 0; const cums = counts.map(v => cum += v);

const dayUrlMap = {}, perDaySrc = {};
for (const [url, it] of Object.entries(ser.items)) {
  for (const d of Object.keys(it.days)) {
    (dayUrlMap[d] ||= new Set()).add(url);
    (perDaySrc[d] ||= {})[it.source] = (perDaySrc[d][it.source] || 0) + 1;
  }
}

document.getElementById("stats").innerHTML = `
  <div class="stat"><b>${fmt(nrows)}</b><small>total rows</small></div>
  <div class="stat"><b>${days.length}</b><small>days tracked</small></div>
  <div class="stat"><b>${fmt(Math.round(nrows/days.length))}</b><small>rows/day avg</small></div>
  <div class="stat"><b>${Object.keys(perSrc).length}</b><small>sources</small></div>
  ${stats ? `<div class="stat"><b>${fmt(stats.unique_urls)}</b><small>unique urls</small></div>` : ""}`;

const CH_LABELS = days.map(d => d.slice(5));
const CH_GRID = { color: "rgba(139,148,158,.15)" };
const CH_TICK = { color: "#8b949e", font: { size: 10 } };
function lineChart(id, vals, color, fill=false, suffix="") {
  new Chart(document.getElementById(id), {
    type: "line",
    data: { labels: CH_LABELS, datasets: [{ data: vals, borderColor: color,
      backgroundColor: fill ? color.replace(")", ",.15)").replace("rgb", "rgba") : "transparent",
      fill, borderWidth: 2, pointRadius: 2.5, pointBackgroundColor: color, tension: .15 }] },
    options: { responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false },
        tooltip: { callbacks: { label: c => c.parsed.y + suffix } } },
      scales: { x: { grid: { display: false }, ticks: { ...CH_TICK, maxTicksLimit: 10 } },
                y: { grid: CH_GRID, ticks: CH_TICK, beginAtZero: true } } }
  });
}
lineChart("daily", counts, "#58a6ff");
lineChart("cum", cums, "#3fb950", true);

// novelty rate: % of urls on each day never seen on an earlier day
{
  const seen = new Set();
  const nov = days.map(d => {
    const dayUrls = dayUrlMap[d] || new Set();
    const fresh = [...dayUrls].filter(u => !seen.has(u)).length;
    dayUrls.forEach(u => seen.add(u));
    return dayUrls.size ? Math.round(100 * fresh / dayUrls.size) : 0;
  });
  lineChart("nov", nov, "#f0883e", false, "%");
  document.getElementById("nov").insertAdjacentHTML("afterend",
    `<p style="color:#f0883e;font-size:11px;text-align:right;margin:4px 8px 0">latest: ${nov[nov.length-1]}%</p>`);
}

const srcList = Object.entries(perSrc).sort((a,b) => b[1]-a[1]);
const maxS = Math.max(...Object.values(perSrc));
const PALETTE = ["#58a6ff","#7ee2a8","#f0883e","#d2a8ff","#79c0ff","#ffa657","#56d4bc","#ff9bcf","#a5d6ff","#e3b341","#8ddb8c","#f778ba","#76e3ea","#d3a6ff","#ffb86b"];
document.getElementById("srcs").innerHTML = srcList.map(([s, n], i) =>
    `<div class="bar"><span class="nm">${s}</span>
     <span class="fill" style="width:${Math.round(400*n/maxS)}px;background:${PALETTE[i % PALETTE.length]}"></span>
     <span class="v">${fmt(n)}</span></div>`).join("");
// per-source share donut
const totalS = srcList.reduce((a, [,n]) => a + n, 0);
const R = 70, CX = 100, CY = 100, CIRC = 2 * Math.PI * R;
let acc = 0;
document.getElementById("donut").innerHTML =
  srcList.map(([s, n], i) => {
    const frac = n / totalS, len = frac * CIRC;
    const seg = `<circle cx="${CX}" cy="${CY}" r="${R}" fill="none" stroke="${PALETTE[i % PALETTE.length]}"
      stroke-width="26" stroke-dasharray="${len.toFixed(2)} ${(CIRC - len).toFixed(2)}"
      stroke-dashoffset="${(-acc * CIRC).toFixed(2)}" transform="rotate(-90 ${CX} ${CY})"
      ><title>${s} — ${fmt(n)} (${(frac*100).toFixed(1)}%)</title></circle>`;
    acc += frac; return seg;
  }).join("") +
  `<text x="${CX}" y="${CY-4}" fill="var(--fg)" font-size="18" font-weight="600" text-anchor="middle">${srcList.length}</text>` +
  `<text x="${CX}" y="${CY+14}" fill="var(--dim)" font-size="11" text-anchor="middle">sources</text>`;

// stacked source mix per day
{

  const W = 820, H = 220, P = 30;
  const maxTot = Math.max(...days.map(d => perDay[d] || 0), 1);
  const bw = Math.min(60, (W - 2*P) / days.length * 0.7);
  const srcIdx = Object.fromEntries(srcList.map(([s], i) => [s, i]));
  document.getElementById("mix").innerHTML =
    `<line x1="${P}" y1="${H-P}" x2="${W-P}" y2="${H-P}" stroke="var(--border)"/>` +
    days.map((d, di) => {
      const cx = P + (W - 2*P) * (days.length < 2 ? 0.5 : di/(days.length-1));
      let y0 = H - P;
      const segs = srcList.map(([s], si) => {
        const n = (perDaySrc[d] || {})[s] || 0;
        if (!n) return "";
        const h = (H - 2*P) * n / maxTot;
        y0 -= h;
        return `<rect x="${cx - bw/2}" y="${y0}" width="${bw}" height="${h}" fill="${PALETTE[si % PALETTE.length]}"><title>${s}: ${n} (${d})</title></rect>`;
      }).join("");
      return segs + `<text x="${cx}" y="${H-8}" fill="var(--dim)" font-size="10" text-anchor="middle">${d.slice(5)}</text>`;
    }).join("");
}

// attention by weekday: item counts + mean score per weekday (non-rolling sources only)
const ROLLING = new Set(["npm","pypi","crates"]);
const WD = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
const wCount = [0,0,0,0,0,0,0], wScore = [0,0,0,0,0,0,0], wDays = [new Set(),new Set(),new Set(),new Set(),new Set(),new Set(),new Set()];
for (const it of Object.values(ser.items)) {
  if (ROLLING.has(it.source)) continue;
  for (const [d, v] of Object.entries(it.days)) {
    const w = new Date(d + "T00:00:00Z").getUTCDay();
    wCount[w]++; wScore[w] += Number(v[0]) || 0; wDays[w].add(d);
  }
}
const wAvg = wScore.map((s,i) => wDays[i].size ? s/wDays[i].size : 0);
{
  const W = 820, H = 200, P = 30, max = Math.max(...wAvg, 1);
  const bw = (W - 2*P) / 7;
  document.getElementById("wd").innerHTML =
    `<line x1="${P}" y1="${H-P}" x2="${W-P}" y2="${H-P}" stroke="var(--border)"/>` +
    wAvg.map((v,i) => {
      const h = (H - 2*P) * (v/max), xx = P + i*bw + bw*0.15;
      return `<rect x="${xx}" y="${H-P-h}" width="${bw*0.7}" height="${h}" fill="${i===1||i===5?"var(--accent)":"var(--border)"}" rx="3"><title>${WD[i]}: avg score ${fmt(Math.round(v))}, ${wCount[i]} items over ${wDays[i].size} days</title></rect>` +
             `<text x="${xx+bw*0.35}" y="${H-P+14}" fill="var(--dim)" font-size="11" text-anchor="middle">${WD[i]}</text>` +
             `<text x="${xx+bw*0.35}" y="${H-P-h-5}" fill="var(--dim)" font-size="10" text-anchor="middle">${fmt(Math.round(v))}</text>`;
    }).join("");
  const peak = WD[wAvg.indexOf(Math.max(...wAvg))];
  document.getElementById("wd-note").textContent =
    `mean story score by weekday (non-rolling sources) — peak: ${peak}`;
}
