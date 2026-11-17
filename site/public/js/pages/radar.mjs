const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
const fmt = n => n >= 1e6 ? (n/1e6).toFixed(1)+"M" : n >= 1e3 ? (n/1e3).toFixed(1)+"k" : String(n);
const $ = id => document.getElementById(id);
try {
  const [nw, ri, cr, ser] = await Promise.all([
    fetch("docs/api/new.json", {cache:"no-cache"}).then(r => r.json()),
    fetch("docs/api/risers.json", {cache:"no-cache"}).then(r => r.json()),
    fetch("docs/api/crossovers.json", {cache:"no-cache"}).then(r => r.json()),
    fetch("docs/api/series.json", {cache:"no-cache"}).then(r => r.json()),
  ]);
  const latest = nw.latest_snapshot;
  const fresh = nw.items.slice().sort((a,b) => (b.score||0)-(a.score||0));
  const hot = ri.single_day_spikes.filter(x => x.date === latest)
    .concat(ri.sustained_climbers.slice(0, 8).map(c => ({title: c.title, url: c.url, source: c.source, delta: c.gain, date: latest})))
    .sort((a,b) => b.delta - a.delta);
  const cross = cr.crossovers;
  const SKIP = new Set(["news.ycombinator.com","github.com","www.npmjs.com","pypi.org","crates.io","dev.to","lobste.rs"]);
  const hostOf = u => { try { return new URL(u).hostname.replace(/^www\./,""); } catch(e) { return ""; } };
  const domFirst = {};
  for (const [url, it] of Object.entries(ser.items)) {
    const h = hostOf(url); if (!h || SKIP.has(h)) continue;
    const first = Object.keys(it.days).sort()[0];
    if (!domFirst[h] || first < domFirst[h].first) domFirst[h] = { first, url, title: it.title, source: it.source };
  }
  const newDoms = Object.entries(domFirst).filter(([,v]) => v.first === latest)
    .sort((a,b) => a[0].localeCompare(b[0]));

  $("stats").innerHTML =
    `<div class="stat"><b>${latest}</b><small>latest snapshot</small></div>
     <div class="stat"><b class="up">${nw.new_items}</b><small>first-seen items today</small></div>
     <div class="stat"><b>${hot.length}</b><small>heating up today</small></div>
     <div class="stat"><b>${cross.length}</b><small>crossovers (all time)</small></div>
     <div class="stat"><b>${newDoms.length}</b><small>new domains today</small></div>`;

  const row = (e, badge) =>
    `<li><span class="it"><a href="${e.url}">${esc(e.title.length>80?e.title.slice(0,80)+"…":e.title)}</a><span class="src">${srcName(e.source)}</span>
     <a href="item.html?q=${encodeURIComponent(e.title)}" title="score trajectory" style="color:var(--dim);text-decoration:none;margin-left:4px">⤳</a></span>
     <span class="sc">${badge}</span></li>`;

  $("out").innerHTML =
    `<h2>fresh on the board today</h2><ol>` +
      (fresh.slice(0,20).map(e => row(e, `<span class="up">${fmt(e.score||0)}</span> ${e.metric||""}`)).join("")
        || `<li><span class="it" style="color:var(--dim)">nothing new today</span></li>`) + `</ol>` +
    `<h2>heating up — gains in the last 24h</h2><ol>` +
      (hot.slice(0,12).map(e => row(e, `<span class="up">+${fmt(e.delta)}</span>`)).join("")
        || `<li><span class="it" style="color:var(--dim)">no spikes today</span></li>`) + `</ol>` +
    `<h2>crossing over — on 2+ sources</h2><ol>` +
      (cross.slice(0,10).map(c => row({title: c.title, url: c.url, source: c.sources.join(" + ")},
        `${fmt(c.best.score)} ${c.best.metric}`)).join("")
        || `<li><span class="it" style="color:var(--dim)">none yet</span></li>`) + `</ol>` +
    `<h2>new neighborhoods — domains first seen today</h2><ol>` +
      (newDoms.slice(0,15).map(([h, v]) => row({title: h, url: v.url, source: v.source},
        `<a href="domain.html?d=${encodeURIComponent(h)}" style="color:var(--dim)">deep dive →</a>`)).join("")
        || `<li><span class="it" style="color:var(--dim)">no new domains today</span></li>`) + `</ol>`;
} catch (e) { $("err").textContent = "data unavailable: " + e; }
