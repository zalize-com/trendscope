const fmt = n => n >= 1e9 ? (n/1e9).toFixed(1)+"B" : n >= 1e6 ? (n/1e6).toFixed(1)+"M"
             : n >= 1e3 ? (n/1e3).toFixed(1)+"k" : String(n);
const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };

function parseCSV(txt) {
  const rows = []; let f = "", row = [], q = false;
  for (let i = 0; i <= txt.length; i++) {
    const c = txt[i];
    if (q) {
      if (c === '"') { if (txt[i+1] === '"') { f += '"'; i++; } else q = false; }
      else if (c === undefined) {} else f += c;
    } else if (c === '"') q = true;
    else if (c === ',' ) { row.push(f); f = ""; }
    else if (c === '\n' || c === undefined) { row.push(f); f = ""; rows.push(row); row = []; }
    else if (c !== '\r') f += c;
  }
  return rows.filter(r => r.length > 1);
}

let RECS = null;
let LIVE = new Set();
fetch("data/latest-lite.json", {cache:"no-cache"}).then(r=>r.ok?r:Promise.reject()).catch(()=>fetch("data/latest.json",{cache:"no-cache"})).then(r => r.json()).then(snap => {
  for (const its of Object.values(snap.items)) for (const i of its) LIVE.add(i.url);
  if (RECS) paint();
}).catch(() => {});
fetch("docs/api/series.json", {cache:"no-cache"}).then(r => r.json()).then(d => {
  RECS = [];
  for (const [url, it] of Object.entries(d.items)) {
    for (const [date, [score, rank, comments]] of Object.entries(it.days)) {
      RECS.push({title: it.title, url, source: it.source, metric: it.metric,
                 author: it.author, date, score, rank, comments});
    }
  }
  const q0 = new URLSearchParams(location.search).get("q") || "";
  document.getElementById("q").value = q0;
  paint();
  document.getElementById("q").addEventListener("input", paint);
}).catch(() => { document.getElementById("out").innerHTML = "<p id='err'>history unavailable</p>"; });

const CANONS = [
  ["data/hn-canon-monthly.csv", "📜 all-time canon", "canon"],
  ["data/show-hn-monthly.csv", "🚀 Show HN canon", "showhn"],
  ["data/ask-hn-monthly.csv", "❓ Ask HN canon", "askhn"],
];

function paint() {
  const q = document.getElementById("q").value.trim().toLowerCase();
  const out = document.getElementById("out");
  if (!RECS || q.length < 2) { out.innerHTML = ""; return; }
  // group matching items by url
  const hits = {};
  for (const r of RECS) {
    if (!((r.title||"").toLowerCase().includes(q) || (r.url||"").toLowerCase().includes(q)
          || (r.author||"").toLowerCase() === q)) continue;
    const k = r.url || r.title;
    (hits[k] = hits[k] || []).push(r);
  }
  const groups = Object.values(hits);
  if (!groups.length) {
    // Nothing on the recent board — check the monthly archives before giving up.
    Promise.all(CANONS.map(([file]) =>
      fetch(file, {cache:"no-cache"}).then(r => r.text()).then(ct => {
        const rows = parseCSV(ct), h = rows.shift() || [];
        return { rows, i_title: h.indexOf("title"), i_month: h.indexOf("month"),
                 i_rank: h.indexOf("rank"), i_pts: h.indexOf("points"),
                 i_url: h.indexOf("url"), i_hn: h.indexOf("hn_url"),
                 i_cmt: h.indexOf("comments"), i_auth: h.indexOf("author") };
      }).catch(() => null)
    )).then(cs => {
      let html = "";
      cs.forEach((c, ci) => {
        if (!c) return;
        const hits2 = c.rows.filter(r => (r[c.i_title]||"").toLowerCase().includes(q));
        if (!hits2.length) return;
        hits2.sort((a,b) => +b[c.i_pts] - +a[c.i_pts]);
        const [ , label, ] = CANONS[ci];
        html += `<h2>in the archives — ${label}</h2><ol>` +
          hits2.slice(0, 10).map(r =>
            `<li><span class="rk">#${r[c.i_rank]}</span>
             <span class="it"><a href="${r[c.i_url] || r[c.i_hn]}" target="_blank" rel="noopener">${esc(r[c.i_title])}</a>
             <span class="src">${r[c.i_month]}</span></span>
             <span class="sc">${fmt(+r[c.i_pts]||0)} pts${r[c.i_cmt] ? ` · 💬${fmt(+r[c.i_cmt])}` : ""}
             ${r[c.i_auth] ? ` · @${esc(r[c.i_auth])}` : ""} <a class="trj" href="${r[c.i_hn]}">hn</a></span></li>`
          ).join("") + `</ol>`;
      });
      out.innerHTML = html || `<p id="err">no matches in the 10-day history or the archives.
        <a href="canon.html?q=${encodeURIComponent(q)}">search 19 years of HN canon →</a></p>`;
    });
    return;
  }
  out.innerHTML = groups.slice(0, 8).map(rs => {
    rs.sort((a,b) => a.date.localeCompare(b.date));
    const it = rs[rs.length-1];
    const days = rs.length;
    const best = Math.min(...rs.map(r => +r.rank || 99));
    const peak = Math.max(...rs.map(r => +r.score || 0));
    // score sparkline
    const mx = peak || 1;
    const spark = `<svg width="${days*10}" height="18" viewBox="0 0 ${days*10} 18" style="vertical-align:-3px;margin-left:8px">${
      rs.map((r,i) => `<rect x="${i*10}" y="${18-Math.round(14*(+r.score||0)/mx)}" width="8" height="${Math.max(1,Math.round(14*(+r.score||0)/mx))}" fill="var(--accent)"/>`).join("")}</svg>`;
    const cmts = rs.map(r => +r.comments || 0);
    const peakC = Math.max(...cmts);
    const cspark = peakC > 0
      ? `<svg width="${days*10}" height="18" viewBox="0 0 ${days*10} 18" style="vertical-align:-3px;margin-left:8px">${
          cmts.map((c,i) => `<rect x="${i*10}" y="${18-Math.round(14*c/peakC)}" width="8" height="${Math.max(1,Math.round(14*c/peakC))}" fill="var(--orange,#e3a008)"/>`).join("")}</svg>`
      : '<span class="dim">—</span>';
    const live = LIVE.has(it.url) ? ` <span style="color:var(--green);font-size:11px" title="on today's board">● live</span>` : "";
    return `<div class="card">
      <b><a href="${it.url}" target="_blank" rel="noopener">${esc(it.title)}</a>${live}</b>
      <button class="embed-btn" data-t="${esc(it.title)}">embed this story</button>
      <div class="stats">
        <div class="stat"><b>${days}</b><small>days on board</small></div>
        <div class="stat"><b>#${best}</b><small>best rank</small></div>
        <div class="stat"><b>${fmt(peak)}</b><small>peak ${it.metric}</small></div>
        <div class="stat"><b>${spark}</b><small>score/day</small></div>
        <div class="stat"><b>${cspark}</b><small>💬/day</small></div>
      </div>
      <h2>trajectory</h2>
      <ol>${rs.map((r, i) => {
        const prev = i > 0 ? +rs[i-1].score || 0 : null;
        const d = prev === null ? "" : (+r.score || 0) - prev;
        const dstr = prev === null ? '<span class="dim">—</span>'
          : d === 0 ? '<span class="dim">±0</span>'
          : `<span style="color:${d > 0 ? "var(--green)" : "var(--red)"}">${d > 0 ? "+" : "−"}${fmt(Math.abs(d))}</span>`;
        return `<li><span class="rk">#${r.rank}</span>
        <span class="it">${r.date}<a class="src" href="source.html?s=${encodeURIComponent(r.source)}" title="source deep-dive" style="text-decoration:none">${srcName(r.source)}</a></span>
        <span class="sc">${scoreText(r, fmt)} ${dstr}</span></li>`;
      }).join("")}</ol>
    </div>`;
  }).join("") + (groups.length > 8 ? `<p id="err">…and ${groups.length-8} more matches</p>` : "");

  // same-domain siblings for the top hit
  try {
    const topUrl = groups[0] && groups[0][0] && groups[0][0].url;
    const host = topUrl && new URL(topUrl).hostname.replace(/^www\./, "");
    if (host) {
      const sib = {};
      for (const r of RECS) {
        if (!r.url) continue;
        const h = r.url.split("/")[2].replace(/^www\./, "");
        if (h !== host || r.url === topUrl) continue;
        const k = r.url;
        const s = sib[k] ||= { title: r.title, dates: new Set(), score: 0 };
        s.dates.add(r.date); s.score = Math.max(s.score, +r.score || 0);
      }
      const list = Object.entries(sib).map(([u, s]) => ({ u, ...s, days: s.dates.size }))
        .sort((a, b) => b.days - a.days || b.score - a.score).slice(0, 10);
      if (list.length) {
        out.insertAdjacentHTML("beforeend", `<h2>also from ${esc(host)}</h2><ol>` +
          list.map(s => `<li><span class="it"><a href="${esc(s.u)}" target="_blank" rel="noopener">${esc(s.title)}</a>
            <span class="src">${s.days}d</span></span>
            <span class="sc">${fmt(s.score)}</span></li>`).join("") + `</ol>`);
      }
    }
  } catch (e) {}

  // canon cross-check: exact-title match against the three monthly archives
  Promise.all(CANONS.map(([file]) =>
    fetch(file, {cache:"no-cache"}).then(r => r.text()).then(ct => {
      const rows = parseCSV(ct), h = rows.shift() || [];
      return { rows, i_title: h.indexOf("title"), i_month: h.indexOf("month"),
               i_rank: h.indexOf("rank"), i_pts: h.indexOf("points"), i_hn: h.indexOf("hn_url") };
    }).catch(() => null)
  )).then(cs => {
    const cards = out.querySelectorAll(".card");
    groups.slice(0, 8).forEach((rs, gi) => {
      const title = rs[rs.length-1].title.toLowerCase();
      if (!cards[gi]) return;
      cs.forEach((c, ci) => {
        if (!c) return;
        const hits = c.rows.filter(r => (r[c.i_title]||"").toLowerCase() === title);
        if (!hits.length) return;
        hits.sort((a,b) => +b[c.i_pts] - +a[c.i_pts]);
        const h = hits[0], [ , label, ] = CANONS[ci];
        cards[gi].insertAdjacentHTML("beforeend",
          `<p class="muted" style="font-size:12px">${label}:
            <a href="${h[c.i_hn]}">#${h[c.i_rank]} in ${h[c.i_month]}</a> with ${fmt(+h[c.i_pts])} pts</p>`);
      });
    });
  });
}
document.getElementById("out").addEventListener("click", ev => {
  const btn = ev.target.closest(".embed-btn");
  if (!btn) return;
  const src = `https://trendscope.zalize.com/embed.html?mode=item&q=${encodeURIComponent(btn.dataset.t || "")}`;
  const code = `<iframe src="${src}" style="width:100%;max-width:560px;height:180px;border:0" loading="lazy" title="trendscope story trajectory"></iframe>`;
  navigator.clipboard?.writeText(code).then(() => { btn.textContent = "copied iframe code"; setTimeout(() => btn.textContent = "embed this story", 1600); });
});
