const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
const fmt = n => n >= 1e6 ? (n/1e6).toFixed(1)+"M" : n >= 1e3 ? (n/1e3).toFixed(1)+"k" : String(n);
const $ = id => document.getElementById(id);
const KEY = "ts-watch";
const load = () => { try { return JSON.parse(localStorage.getItem(KEY)) || []; } catch(e) { return []; } };
const save = l => localStorage.setItem(KEY, JSON.stringify(l));
let kws = load();
function renderChips() {
  $("chips").innerHTML = kws.length
    ? kws.map((k,i) => `<a class="chip" href="#" data-i="${i}" style="text-decoration:none">${esc(k)} ✕</a>`).join("")
    : `<span style="color:var(--dim);font-size:12px">no keywords yet — add one above</span>`;
  $("chips").querySelectorAll("a").forEach(a => a.onclick = e => {
    e.preventDefault(); kws.splice(+a.dataset.i,1); save(kws); run();
  });
}
async function run() {
  renderChips();
  if (!kws.length) { $("out").innerHTML = ""; $("stats").innerHTML = ""; return; }
  const low = kws.map(k => k.toLowerCase());
  const match = t => { t = t.toLowerCase(); return low.filter(k => t.includes(k)); };
  const [nw, latest] = await Promise.all([
    fetch("docs/api/new.json", {cache:"no-cache"}).then(r => r.json()),
    fetch("data/latest-lite.json", {cache:"no-cache"}).then(r=>r.ok?r:Promise.reject()).catch(()=>fetch("data/latest.json",{cache:"no-cache"})).then(r => r.json()),
  ]);
  const fresh = nw.items.map(e => ({...e, hit: match(e.title)})).filter(e => e.hit.length);
  const board = Object.values(latest.items).flat().map(e => ({...e, hit: match(e.title)})).filter(e => e.hit.length);
  const freshUrls = new Set(fresh.map(e => e.url));
  const still = board.filter(e => !freshUrls.has(e.url));
  $("stats").innerHTML =
    `<div class="stat"><b>${kws.length}</b><small>watched terms</small></div>
     <div class="stat"><b class="up">${fresh.length}</b><small>new today matching</small></div>
     <div class="stat"><b>${still.length}</b><small>still on the board</small></div>`;
  const row = e =>
    `<li><span class="it"><a href="${e.url}">${esc(e.title.length>85?e.title.slice(0,85)+"…":e.title)}</a><span class="src">${e.source}</span>
     ${e.hit.map(k=>`<span class="chip on" style="margin:0 0 0 4px">${esc(k)}</span>`).join("")}
     <a href="item.html?q=${encodeURIComponent(e.title)}" style="color:var(--dim);text-decoration:none;margin-left:4px">⤳</a></span>
     <span class="sc">${fmt(e.score||0)} ${e.metric||""}</span></li>`;
  $("out").innerHTML =
    `<h2>new today matching your watchlist</h2><ol>` +
      (fresh.map(row).join("") || `<li><span class="it" style="color:var(--dim)">no fresh matches today</span></li>`) + `</ol>` +
    `<h2>still on the board</h2><ol>` +
      (still.slice(0,20).map(row).join("") || `<li><span class="it" style="color:var(--dim)">none</span></li>`) + `</ol>`;
}
$("add").onclick = () => {
  const v = $("kw").value.trim(); if (!v) return;
  for (const k of v.split(",")) { const t = k.trim(); if (t && !kws.includes(t)) kws.push(t); }
  save(kws); $("kw").value = ""; run();
};
$("kw").onkeydown = e => { if (e.key === "Enter") $("add").click(); };
try { await run(); $("err").textContent = ""; }
catch (e) { $("err").textContent = "data unavailable: " + e; }
