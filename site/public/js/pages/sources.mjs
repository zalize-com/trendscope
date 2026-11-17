const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
const $ = id => document.getElementById(id);
try {
  const d = await fetch("docs/api/sources.json", {cache:"no-cache"}).then(r => r.json());
  const dormant = new Set(await fetch("data/dormant.json", {cache:"no-cache"}).then(r => r.json()).catch(() => []));
  const zw = await fetch("data/zerowatch.json", {cache:"no-cache"}).then(r => r.json()).catch(() => null);
  const persistent = new Set(zw?.persistent_empty || []);
  const srcs = Object.entries(d.sources).sort((a,b) => b[1].items - a[1].items);
  const total = srcs.reduce((n,[,v]) => n + v.items, 0);
  $("stats").innerHTML =
    `<div class="stat"><b>${srcs.length}</b><small>sources</small></div>` +
    `<div class="stat"><b>${total}</b><small>items collected</small></div>` +
    `<div class="stat"><b>${d.days_tracked}</b><small>days tracked</small></div>` +
    (zw ? `<div class="stat"><b>${zw.persistent_empty.length}</b><small>persistent-empty (${zw.rounds}d)</small></div>` +
      `<div class="stat"><b>${zw.tide.length}</b><small>in rate-limit tide</small></div>` : "");
  const row = ([name, v]) => {
    const t = v.top_item || {};
    const dorm = dormant.has(name) ? ` <span class="chip" style="color:var(--st-dormant);border-color:var(--st-dormant)" title="alive but quiet — no new posts recently">dormant</span>` : "";
    const pchip = persistent.has(name) ? ` <span class="chip" style="color:var(--st-dead);border-color:var(--st-dead)" title="empty in ${zw.rounds} consecutive snapshots — likely dead or egress-blocked">empty ${zw.rounds}d</span>` : "";
    return `<li><span class="it"><a href="source.html?s=${encodeURIComponent(name)}"><b>${esc(name)}</b></a>${dorm}${pchip}` +
      ` <img src="docs/api/sparkline/${name}.svg" width="90" height="23" style="vertical-align:-4px;opacity:.85" alt="${name} items/day" loading="lazy">` +
      ` · ${v.items} items · ${v.unique_urls} unique · ${v.one_day_pct}% one-day` +
      (t.title ? ` · top: <a href="${esc(t.url)}">${esc(t.title)}</a>` : "") +
      `</span><span class="sc"><a href="source.html?s=${encodeURIComponent(name)}">deep dive →</a></span></li>`;
  };
  // 9k+ rows × per-row sparkline <img>: render in viewport-driven batches so the
  // page paints immediately and sparklines only fetch for rows on screen.
  const out = $("out"), ol = document.createElement("ol"), BATCH = 400;
  out.appendChild(ol);
  const sentinel = document.createElement("li");
  sentinel.style.cssText = "list-style:none;text-align:center;padding:8px";
  let i = 0;
  const fill = () => {
    const html = srcs.slice(i, i + BATCH).map(row).join("");
    i += BATCH;
    if (i >= srcs.length) {
      sentinel.remove();
      ol.insertAdjacentHTML("beforeend", html);
    } else {
      ol.insertAdjacentHTML("beforeend", html);
      ol.appendChild(sentinel);
    }
  };
  fill();
  if (i < srcs.length) {
    sentinel.textContent = "loading more…";
    ol.appendChild(sentinel);
    new IntersectionObserver(e => { if (e[0].isIntersecting) fill(); }, {rootMargin: "600px"}).observe(sentinel);
  }
} catch (e) {
  console.error(e);
  const el = document.getElementById("err");
  if (el) el.textContent = "failed to load sources.json";
}
