const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
const fmt = n => n >= 1e9 ? (n/1e9).toFixed(1)+"B" : n >= 1e6 ? (n/1e6).toFixed(1)+"M" : n >= 1e3 ? (n/1e3).toFixed(1)+"k" : String(n);
const $ = id => document.getElementById(id);
const d = await fetch("docs/api/risers.json", {cache:"no-cache"}).then(r => r.json());
await loadKinds();
const spikes = d.single_day_spikes, jumps = d.package_rank_jumps,
      climbers = d.sustained_climbers, latest = d.latest_snapshot;

const QS = new URLSearchParams(location.search).get("s");
const srcs = [...new Set(spikes.concat(jumps, climbers).map(i => i.source))].sort();
$("srcbar").innerHTML = srcs.map(s =>
  `<a class="chip${s===QS?" on":""}" href="?s=${encodeURIComponent(s)}">${esc(srcName(s))}</a>`).join(" ") +
  (QS ? ` <a class="chip" href="?">all</a>` : "");
const sf = e => !QS || e.source === QS;
const spikesF = spikes.filter(sf), jumpsF = jumps.filter(sf), climbersF = climbers.filter(sf);

$("stats").innerHTML =
  `<div class="stat"><b>${latest}</b><small>latest snapshot</small></div>
   <div class="stat"><b>${d.days_tracked}</b><small>days tracked</small></div>
   <div class="stat"><b class="up">+${spikes.length ? fmt(spikes[0].delta) : 0}</b><small>biggest 1-day spike</small></div>
   <div class="stat"><b>${spikes.length}</b><small>positive single-day deltas</small></div>`;

const crow = (e,i) =>
  `<li><span class="sc" style="min-width:16px;text-align:right">${i+1}</span>
   <span class="it"><a href="${e.url}">${esc(e.title)}</a><span class="src">${srcName(e.source)}</span>${kindChip(e.url)}
   <a href="item.html?q=${encodeURIComponent(e.title)}" title="score trajectory" style="color:var(--dim);text-decoration:none;margin-left:4px">⤳</a></span>
   <span class="sc"><span class="up">+${fmt(e.gain)}</span> ${e.metric} <span class="date">over ${e.days_tracked}d · still on board</span></span></li>`;

const srow = (e,i) =>
  `<li><span class="sc" style="min-width:16px;text-align:right">${i+1}</span>
   <span class="it"><a href="${e.url}">${esc(e.title)}</a><span class="src">${srcName(e.source)}</span>${kindChip(e.url)}
   <a href="item.html?q=${encodeURIComponent(e.title)}" title="score trajectory" style="color:var(--dim);text-decoration:none;margin-left:4px">⤳</a></span>
   <span class="sc"><span class="up">+${fmt(e.delta)}</span> ${e.metric} <span class="date">· ${e.date} · ${fmt(e.from_score)}→${fmt(e.to_score)}</span></span></li>`;
const jrow = (e,i) =>
  `<li><span class="sc" style="min-width:16px;text-align:right">${i+1}</span>
   <span class="it"><a href="${e.url}">${esc(e.title)}</a><span class="src">${srcName(e.source)}</span>${kindChip(e.url)}
   <a href="item.html?q=${encodeURIComponent(e.title)}" title="score trajectory" style="color:var(--dim);text-decoration:none;margin-left:4px">⤳</a></span>
   <span class="sc"><span class="up">▲${e.jump}</span> <span class="date">· ${e.date} · #${e.from_rank}→#${e.to_rank}</span></span></li>`;

$("out").innerHTML =
  `<h2>sustained climbers — still on board today</h2><ol>` +
    (climbersF.slice(0,15).map(crow).join("") || `<li><span class="it" style="color:var(--dim)">none rising right now</span></li>`) + `</ol>` +
  `<h2>biggest single-day spikes (all time)</h2><ol>` +
    (spikesF.slice(0,30).map(srow).join("") || `<li><span class="it" style="color:var(--dim)">no consecutive-day gains in this filter</span></li>`) + `</ol>` +
  `<h2>package rank jumps (rolling sources)</h2><ol>` +
    (jumpsF.slice(0,15).map(jrow).join("") || `<li><span class="it" style="color:var(--dim)">none yet</span></li>`) + `</ol>`;
