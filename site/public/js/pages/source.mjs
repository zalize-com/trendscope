const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
const fmt = n => n >= 1e9 ? (n/1e9).toFixed(1)+"B" : n >= 1e6 ? (n/1e6).toFixed(1)+"M" : n >= 1e3 ? (n/1e3).toFixed(1)+"k" : String(n);
const $ = id => document.getElementById(id);
const S = new URLSearchParams(location.search).get("s") || "hackernews";

function parseCSV(text) {
  const rows = []; let field = "", row = [], inQ = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQ) {
      if (c === '"') { if (text[i+1] === '"') { field += '"'; i++; } else inQ = false; }
      else field += c;
    } else if (c === '"') inQ = true;
    else if (c === ',') { row.push(field); field = ""; }
    else if (c === '\n') { row.push(field); rows.push(row); row = []; field = ""; }
    else if (c !== '\r') field += c;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  return rows;
}

const ser = await fetch("docs/api/series.json", {cache:"no-cache"}).then(r => r.json());
const all = [];
for (const [url, it] of Object.entries(ser.items)) {
  for (const [date, [score, rank, comments]] of Object.entries(it.days)) {
    all.push({source: it.source, date, title: it.title, url, score, metric: it.metric,
              rank, comments, author: it.author});
  }
}
const sources = [...new Set(all.map(r => r.source))].sort();
if (!sources.includes(S)) location.search = "?s=hackernews";

$("srcbar").innerHTML = sources.map(s =>
  `<a class="chip ${s===S?"on":""}" href="?s=${encodeURIComponent(s)}">${esc(srcName(s))}</a>`).join("");

const items = all.filter(r => r.source === S);
const days = [...new Set(items.map(r => r.date))].sort();
const byDay = {}; for (const d of days) byDay[d] = 0;
for (const r of items) byDay[r.date] = (byDay[r.date]||0) + 1;
const byUrl = {};
for (const r of items) {
  const e = byUrl[r.url] ||= { title: r.title, url: r.url, score: 0, metric: r.metric, days: new Set(), best: 99, comments: 0, author: r.author };
  e.score = Math.max(e.score, r.score);
  e.comments = Math.max(e.comments, Number(r.comments)||0);
  e.days.add(r.date);
  if (r.rank && r.rank < e.best) e.best = r.rank;
}
const top = Object.values(byUrl).sort((a,b) => b.score - a.score).slice(0, 30);
const maxPerDay = Math.max(...Object.values(byDay), 1);
const dayCounts = Object.values(byUrl).map(u => u.days.size).sort((a,b) => a-b);
const medDays = dayCounts.length ? dayCounts[Math.floor(dayCounts.length/2)] : 0;
const oneDayPct = dayCounts.length ? Math.round(100*dayCounts.filter(d => d===1).length/dayCounts.length) : 0;

$("stats").innerHTML =
  `<div class="stat"><b>${items.length}</b><small>items tracked</small></div>` +
  `<div class="stat"><b>${days.length}</b><small>days covered</small></div>` +
  `<div class="stat"><b>${Object.keys(byUrl).length}</b><small>unique urls</small></div>` +
  `<div class="stat"><b>${medDays}d</b><small>median days on board</small></div>` +
  `<div class="stat"><b>${oneDayPct}%</b><small>one-day items</small></div>` +
  `<div class="stat"><b>${fmt(top[0]?.score||0)}</b><small>top score</small></div>`;

const bars = days.map(d => `<div class="bar" style="height:${Math.max(2, Math.round(44*byDay[d]/maxPerDay))}px" title="${d}: ${byDay[d]} items"></div>`).join("");
const labels = days.map(d => `<span>${d.slice(5)}</span>`).join("");

$("out").innerHTML =
  `<h2>items per day</h2><div class="bars">${bars}</div><div class="blabels">${labels}</div>` +
  `<h2>top hits (all days)</h2><ol>` +
  top.map((t,i) =>
    `<li><span class="date">${i<3?["①","②","③"][i]:i+1+"."}</span>` +
    `<span class="it"><a href="${t.url}">${esc(t.title.length>85?t.title.slice(0,85)+"…":t.title)}</a>` +
    `<a href="item.html?q=${encodeURIComponent(t.title)}" title="score trajectory" style="color:var(--dim);text-decoration:none;margin-left:4px">⤳</a></span>` +
    `<span class="sc">${t.author?`<a href="author.html?u=${encodeURIComponent(t.author)}" style="color:var(--dim)">@${esc(t.author)}</a> · `:""}${t.days.size>1?t.days.size+"d · ":""}${t.best<99?"#"+t.best+" · ":""}${fmt(t.score)}${t.comments?" · "+t.comments+"💬":""}</span></li>`
  ).join("") + `</ol>`;
