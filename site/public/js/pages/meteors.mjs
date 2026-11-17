const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
const fmt = n => n >= 1e6 ? (n/1e6).toFixed(1)+"M" : n >= 1e3 ? (n/1e3).toFixed(1)+"k" : String(n);
const $ = id => document.getElementById(id);
try {
  const ser = await fetch("docs/api/series.json", {cache:"no-cache"}).then(r => r.json());
  const meteors = [];
  for (const [url, it] of Object.entries(ser.items)) {
    const ds = Object.keys(it.days);
    if (ds.length !== 1) continue;
    const [score, rank, comments] = it.days[ds[0]];
    meteors.push({ url, title: it.title, source: it.source, metric: it.metric,
                   author: it.author, date: ds[0], score, rank, comments });
  }
  const bySrc = {};
  for (const m of meteors) (bySrc[m.source] = bySrc[m.source] || []).push(m);
  for (const v of Object.values(bySrc)) v.sort((a,b) => b.score - a.score);
  const srcs = Object.entries(bySrc).sort((a,b) => b[1].length - a[1].length);
  const total = meteors.length, all = Object.keys(ser.items).length;
  $("stats").innerHTML =
    `<div class="stat"><b>${total}</b><small>meteors (1-day items)</small></div>
     <div class="stat"><b>${(100*total/all).toFixed(0)}%</b><small>of all ${all} tracked urls</small></div>
     <div class="stat"><b>${srcs.length}</b><small>sources</small></div>`;
  const row = m =>
    `<li><span class="it"><a href="${m.url}">${esc(m.title.length>80?m.title.slice(0,80)+"…":m.title)}</a>` +
      `<a href="item.html?q=${encodeURIComponent(m.title)}" style="color:var(--dim);text-decoration:none;margin-left:4px">⤳</a>
       ${m.author ? `<span class="src">@${esc(m.author)}</span>` : ""}</span>
       <span class="sc">${scoreText(m, fmt)} <span class="date">· ${m.date}</span></span></li>`;
  $("out").innerHTML = srcs.map(([s, ms]) =>
    `<h2>${s} — ${ms.length} meteors</h2><ol>` +
    ms.slice(0,5).map(row).join("") + `</ol>`).join("");
} catch (e) { $("err").textContent = "data unavailable: " + e; }
