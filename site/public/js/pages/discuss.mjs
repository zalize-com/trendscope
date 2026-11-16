const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
const fmt = n => n >= 1e3 ? (n/1e3).toFixed(1)+"k" : String(n);
const $ = id => document.getElementById(id);

const data = await fetch("docs/api/discussed.json", {cache:"no-cache"}).then(r => r.json()).catch(() => null);
if (!data) { $("err").textContent = "could not load docs/api/discussed.json"; throw 0; }

const srcs = new Set(data.discussed.map(x => x.source));
$("stats").innerHTML =
  `<div class="stat"><b>${data.total}</b><small>commented items</small></div>` +
  `<div class="stat"><b>${data.discussed[0] ? fmt(data.discussed[0].comments) : 0}</b><small>top comment count</small></div>` +
  `<div class="stat"><b>${srcs.size}</b><small>sources with comments</small></div>`;

function row(it, right) {
  return `<li><span class="it"><a href="${it.url}">${esc(it.title)}</a><span class="src">${it.source}</span>` +
    `<a class="trj" href="item.html?q=${encodeURIComponent(it.title)}" title="trajectory">⤳</a></span>` +
    `<span class="sc">${right}</span></li>`;
}

const d = data.discussed, h = data.heated;
$("out").innerHTML =
  `<h2>most discussed</h2><ol>` +
  d.map(it => row(it, `💬 ${fmt(it.comments)} · ${fmt(it.score)} ${it.metric||""} · ${it.date}`)).join("") + `</ol>` +
  `<h2>heated — comments per point (score ≥ 50)</h2><ol>` +
  h.map(it => row(it, `<span class="hot">${(it.comments/Math.max(1,it.score)).toFixed(1)}×</span> 💬${fmt(it.comments)} · ${fmt(it.score)}pts`)).join("") + `</ol>`;
