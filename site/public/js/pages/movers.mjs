const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
const fmt = n => {
  const s = n < 0 ? "-" : "", a = Math.abs(n);
  return s + (a >= 1e9 ? (a/1e9).toFixed(1)+"B" : a >= 1e6 ? (a/1e6).toFixed(1)+"M" : a >= 1e3 ? (a/1e3).toFixed(1)+"k" : String(a));
};
const $ = id => document.getElementById(id);
const P = new URLSearchParams(location.search);

const idx = await fetch("docs/index.json", {cache:"no-cache"}).then(r => r.json()).catch(() => ({}));
const days = (idx.movers || []).slice().reverse(); // newest first
const pick = $("dpick");
pick.innerHTML = `<option value="latest">latest</option>` +
  `<option value="w7">weekly (7d)</option>` +
  days.map(d => `<option value="${d}">${d}</option>`).join("");
const want = P.get("d") || "latest";
pick.value = (days.includes(want) || want === "w7") ? want : "latest";
pick.onchange = () => { history.replaceState(null,"",`?d=${pick.value}`); load(); };

function row(it, right) {
  return `<li><span class="it"><a href="${it.url}">${esc(it.title)}</a><span class="src">${srcName(it.source)}</span>` +
    `<a class="trj" href="item.html?q=${encodeURIComponent(it.title)}" title="trajectory">⤳</a></span>` +
    `<span class="sc">${right}</span></li>`;
}
function section(title, items, right, cls) {
  if (!items.length) return "";
  return `<h2>${title}</h2><ol>` +
    items.map(it => row(it, `<span class="${cls||''}">${right(it)}</span>`)).join("") + `</ol>`;
}

async function load() {
  const d = pick.value;
  const url = d === "latest" ? "docs/api/movers-latest.json" : `docs/api/movers-${d}.json`;
  $("out").innerHTML = `<p id="err">loading ${d}…</p>`;
  let m;
  try {
    const r = await fetch(url, {cache:"no-cache"});
    if (!r.ok) throw new Error(r.status);
    m = await r.json();
  } catch (e) {
    $("out").innerHTML = `<p id="err">no movers file for ${d} — archive started 2026-11-15; <a href="?d=latest">latest →</a></p>`;
    $("stats").innerHTML = "";
    return;
  }
  $("stats").innerHTML =
    `<div class="stat"><b>${m.entered.length}</b><small>entered</small></div>` +
    `<div class="stat"><b>${m.left.length}</b><small>left</small></div>` +
    `<div class="stat"><b>${m.gainers.length}</b><small>gainers</small></div>` +
    `<div class="stat"><b>${m.droppers.length}</b><small>droppers</small></div>` +
    `<div class="stat"><b>${(m.pkg_rank_up||[]).length + (m.pkg_rank_down||[]).length}</b><small>pkg rank moves</small></div>` +
    `<div class="stat"><b style="font-size:15px">${m.a} → ${m.b}</b><small>snapshot pair</small></div>`;
  $("out").innerHTML =
    section("gainers", m.gainers, it => `+${fmt(it.delta)} <span class="dim">${fmt(it.score)} ${it.metric}</span>`, "up") +
    section("droppers", m.droppers, it => `${fmt(-Math.abs(it.delta))} <span class="dim">${fmt(it.score)} ${it.metric}</span>`, "down") +
    section("entered", m.entered, it => `<span class="up">new</span> · #${it.rank} · ${fmt(it.score)} ${it.metric}`) +
    section("left", m.left, it => `<span class="down">gone</span> · was #${it.rank ?? "?"} · ${fmt(it.score)} ${it.metric}`) +
    section("package rank — climbing", m.pkg_rank_up || [], it => `rank ${it.from} → ${it.to}`, "up") +
    section("package rank — falling", m.pkg_rank_down || [], it => `rank ${it.from} → ${it.to}`, "down") ||
    `<p id="err">empty movers set</p>`;
}
load();
