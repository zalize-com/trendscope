const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
const $ = id => document.getElementById(id);
try {
  const d = await fetch("docs/api/sources.json", {cache:"no-cache"}).then(r => r.json());
  const srcs = Object.entries(d.sources).sort((a,b) => b[1].items - a[1].items);
  const total = srcs.reduce((n,[,v]) => n + v.items, 0);
  $("stats").innerHTML =
    `<div class="stat"><b>${srcs.length}</b><small>sources</small></div>` +
    `<div class="stat"><b>${total}</b><small>items collected</small></div>` +
    `<div class="stat"><b>${d.days_tracked}</b><small>days tracked</small></div>`;
  $("out").innerHTML = "<ol>" + srcs.map(([name, v]) => {
    const t = v.top_item || {};
    return `<li><span class="it"><a href="source.html?s=${encodeURIComponent(name)}"><b>${esc(name)}</b></a>` +
      ` <img src="docs/api/sparkline/${name}.svg" width="90" height="23" style="vertical-align:-4px;opacity:.85" alt="${name} items/day" loading="lazy">` +
      ` · ${v.items} items · ${v.unique_urls} unique · ${v.one_day_pct}% one-day` +
      (t.title ? ` · top: <a href="${esc(t.url)}">${esc(t.title)}</a>` : "") +
      `</span><span class="sc"><a href="source.html?s=${encodeURIComponent(name)}">deep dive →</a></span></li>`;
  }).join("") + "</ol>";
} catch (e) {
  console.error(e);
  const el = document.getElementById("err");
  if (el) el.textContent = "failed to load sources.json";
}
