const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
const fmt = n => n >= 1e9 ? (n/1e9).toFixed(1)+"B" : n >= 1e6 ? (n/1e6).toFixed(1)+"M" : n >= 1e3 ? (n/1e3).toFixed(1)+"k" : String(n);
const $ = id => document.getElementById(id);
const d = await fetch("docs/api/streaks.json", {cache:"no-cache"}).then(r => r.json());
const recs = d.active.concat(d.longest_all_time);
const live = d.active.slice().sort((a,b) => b.consecutive_days - a.consecutive_days || b.top_score - a.top_score);
const allTime = d.longest_all_time.slice(0, 15);

$("stats").innerHTML =
  `<div class="stat"><b>${d.latest_snapshot}</b><small>latest snapshot</small></div>
   <div class="stat"><b>${d.days_tracked}</b><small>days tracked</small></div>
   <div class="stat"><b class="cur">${d.active_count}</b><small>on active streak (≥2d)</small></div>
   <div class="stat"><b>${d.repeat_appearances}</b><small>repeat appearances</small></div>`;

const row = (r, badge) =>
  `<li><span class="it"><a href="${r.url}">${esc(r.title)}</a><span class="src">${r.source}</span>
   <a href="item.html?q=${encodeURIComponent(r.title)}" title="score trajectory" style="color:var(--dim);text-decoration:none;margin-left:4px">⤳</a></span>
   <span class="sc">${badge} · ${fmt(r.top_score)} ${r.metric||""}</span></li>`;

const srcs = [...new Set(recs.map(r => r.source))].sort();
const QS = new URLSearchParams(location.search).get("s");
$("srcbar").innerHTML = srcs.map(s =>
  `<a class="chip${s===QS?" on":""}" href="?s=${encodeURIComponent(s)}">${s}</a>`).join(" ") +
  (QS ? ` <a class="chip" href="?">all</a>` : "");

const sf = r => !QS || r.source === QS;
const liveF = live.filter(sf), allF = allTime.filter(sf);
$("out").innerHTML =
  `<h2>on the board right now (consecutive days)</h2><ol>` +
    (liveF.length
      ? liveF.slice(0, 25).map(r => row(r, `<span class="streak">${r.consecutive_days}d streak</span>`)).join("")
      : `<li><span class="it" style="color:var(--dim)">nothing on a streak yet — streaks start at 2 consecutive days</span></li>`) + `</ol>` +
  `<h2>longest runs (all time)</h2><ol>` +
    allF.map(r => row(r, `<span class="streak">${r.longest_streak}d</span> <span class="dim">(${r.days_on_board}d total)</span>`)).join("") + `</ol>`;
