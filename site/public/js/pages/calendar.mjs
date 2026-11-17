const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
const fmt = n => n >= 1e9 ? (n/1e9).toFixed(1)+"B" : n >= 1e6 ? (n/1e6).toFixed(1)+"M" : n >= 1e3 ? (n/1e3).toFixed(1)+"k" : String(n);

function parseCSV(text) {
  const rows = []; let field = "", row = [], inQ = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQ) {
      if (c === '"') { if (text[i+1] === '"') { field += '"'; i++; } else inQ = false; }
      else field += c;
    } else if (c === '"') inQ = true;
    else if (c === ",") { row.push(field); field = ""; }
    else if (c === "\n") { row.push(field); rows.push(row); row = []; field = ""; }
    else if (c !== "\r") field += c;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  return rows;
}

const ser = await fetch("docs/api/series.json", {cache:"no-cache"}).then(r => r.json());

// per-day winner: highest score among non-rolling sources (downloads skew the view)
const ROLLING = new Set(["npm","pypi","crates"]);
const best = {};
for (const [url, it] of Object.entries(ser.items)) {
  if (ROLLING.has(it.source)) continue;
  for (const [d, [sc]] of Object.entries(it.days)) {
    if (!best[d] || sc > best[d].score)
      best[d] = { score: sc, title: it.title, url,
                  source: it.source, metric: it.metric || "" };
  }
}
const days = Object.keys(best).sort();
const first = days[0], last = days[days.length-1];
// render the month(s) spanning first→last
const months = [...new Set(days.map(d => d.slice(0,7)))];
const grid = document.getElementById("grid");
grid.innerHTML = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"].map(d => `<div class="dow">${d}</div>`).join("");
for (const m of months) {
  const [y, mo] = m.split("-").map(Number);
  const nDays = new Date(y, mo, 0).getDate();
  const firstDow = (new Date(y, mo - 1, 1).getDay() + 6) % 7; // Mon=0
  if (months.indexOf(m) > 0) {
    // spacer row between months
    grid.innerHTML += `<div class="dow" style="grid-column:1/-1;text-align:left;padding:10px 0 2px">
      ${new Date(y, mo - 1).toLocaleString("en", {month: "long", year: "numeric"})}</div>`;
  }
  for (let i = 0; i < firstDow; i++) grid.innerHTML += '<div class="cell empty"></div>';
  for (let d = 1; d <= nDays; d++) {
    const ds = `${m}-${String(d).padStart(2,"0")}`;
    const b = best[ds];
    if (!b) { grid.innerHTML += `<div class="cell none"><div class="d">${d}</div></div>`; continue; }
    grid.innerHTML += `<div class="cell${ds === last ? " today" : ""}">
      <div class="d"><a href="index.html?day=${ds}" title="open the ${ds} snapshot" style="color:var(--dim);text-decoration:none">${d}</a></div>
      <a href="${esc(b.url)}">${esc(b.title.slice(0, 90))}</a>
      <div class="meta"><span class="src">${srcName(b.source)}</span> ${scoreText(b, fmt)}</div></div>`;
  }
}
document.getElementById("sub").innerHTML =
  `Each day's highest-scoring item (packages excluded — download counts skew the view) · ${days.length} days tracked · <code>data/history.csv</code>`;
