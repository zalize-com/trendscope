// daily/<lane> — renders one lane's freshest items from latest-lite.json
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const KNOWN_PREFIXES = new Set(["sec", "eb", "tb", "br", "nl", "pb", "yt", "tldr", "aws", "github", "gitlab", "meta", "slack"]);
const srcName = window.srcName;
const el = document.getElementById("daily");
const lane = el.dataset.lane;

async function load() {
  try {
    const r = await fetch("../data/latest-lite.json", { cache: "no-store" });
    if (!r.ok) throw new Error("http " + r.status);
    const d = await r.json();
    render(d);
  } catch (e) {
    el.innerHTML = '<p id="err">could not load today\'s snapshot — try again later.</p>';
  }
}

// lazy kind chips — re-render once loaded
async function loadKinds() {
  try {
    const r = await fetch("../data/kind-lite.json");
    if (!r.ok) return;
    KINDS = (await r.json()).kinds || {};
    if (LAST) render(LAST);
  } catch (e) {}
}
let KINDS = {}, LAST = null;

function inLane(key) {
  if (lane === "misc") return !KNOWN_PREFIXES.has(key.split("_")[0]);
  return key.startsWith(lane + "_");
}

function render(d) {
  LAST = d;
  const items = d.items || {};
  const rows = [];
  for (const key of Object.keys(items)) {
    if (!inLane(key)) continue;
    for (const it of items[key]) rows.push(it);
  }
  rows.sort((a, b) => (b.score || 0) - (a.score || 0));
  const top = rows.slice(0, 40);
  if (!top.length) {
    el.innerHTML = '<p id="err">no items in this lane today — sources are rate-limited or quiet.</p>';
    return;
  }
  const stamp = `<p class="stamp">snapshot ${esc(d.date)} · ${top.length} of ${rows.length.toLocaleString("en-US")} items · <a href="../data/latest-lite.json">raw json</a></p>`;
  el.innerHTML = stamp + top.map((it, i) => `
    <div class="row">
      <span class="rank">${i + 1}</span>
      <span><a href="${esc(it.url)}" target="_blank" rel="noopener">${esc(it.title)}</a>
        <span class="meta">${it.author ? " · " + esc(it.author) : ""}${it.source ? " · " + esc(srcName(it.source)) : ""}${KINDS[it.url] ? ` <span class="src kindchip">${KINDS[it.url]}</span>` : ""}</span></span>
      <span class="score">${it.metric === "feed rank" ? "#" + (it.rank ?? it.score) : (it.score || 0).toLocaleString("en-US")}</span>
    </div>`).join("");
}

load();
loadKinds();
