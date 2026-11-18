// selfhosted — today's self-hosting/own-your-data items across ALL sources
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const srcName = window.srcName;
const el = document.getElementById("daily");
const RX = /self.?host|self host|own your data|data sovereignty|home.?lab|homelab|degoogle|de-?google/i;

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

function render(d) {
  const items = d.items || {};
  const seen = new Set();
  const rows = [];
  for (const key of Object.keys(items)) {
    for (const it of items[key]) {
      if (seen.has(it.url)) continue;
      seen.add(it.url);
      if (RX.test(it.title || "")) rows.push({ ...it, _src: key });
    }
  }
  rows.sort((a, b) => (b.score || 0) - (a.score || 0));
  const top = rows.slice(0, 50);
  if (!top.length) {
    el.innerHTML = '<p id="err">no self-hosting items in today\'s snapshot.</p>';
    return;
  }
  const lanes = new Set(rows.map((r) => (r._src || "").split("_")[0]));
  const stamp = `<p class="stamp">snapshot ${esc(d.date)} · ${top.length} of ${rows.length.toLocaleString("en-US")} self-hosting items · from ${lanes.size} source lanes · <a href="../data/latest-lite.json">raw json</a></p>`;
  el.innerHTML = stamp + top.map((it, i) => `
    <div class="row">
      <span class="rank">${i + 1}</span>
      <span><a href="${esc(it.url)}" target="_blank" rel="noopener">${esc(it.title)}</a>
        <span class="meta">${it.author ? " · " + esc(it.author) : ""}${it.source ? " · " + esc(srcName(it.source)) : ""}</span></span>
      <span class="score">${it.metric === "feed rank" ? "#" + (it.rank ?? it.score) : (it.score || 0).toLocaleString("en-US")}</span>
    </div>`).join("");
}

load();
