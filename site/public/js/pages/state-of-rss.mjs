// state-of-rss census: reads feeds.json, zerowatch.json, dormant.json, latest.json
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const fmt = (n) => Number(n).toLocaleString("en-US");

async function j(path, fallback) {
  try {
    const r = await fetch(path, { cache: "no-store" });
    if (!r.ok) return fallback;
    const t = await r.text();
    return JSON.parse(t);
  } catch (e) { return fallback; }
}

const [feeds, zw, dormant, latest] = await Promise.all([
  j("data/feeds.json", {}),
  j("data/zerowatch.json", { persistent_empty: [], tide: [] }),
  j("data/dormant.json", []),
  j("data/latest-lite.json", null).then((d) => d || j("data/latest.json", { items: [] })),
]);

// feeds.json = { generated_at, count, feeds: [{key,label,feed,lane,dormant}] }
const feedArr = Array.isArray(feeds) ? feeds : (feeds.feeds || []);
const feedMap = {};
const feedList = feedArr.map((f) => {
  const rec = typeof f === "object" ? f : { feed: f };
  feedMap[rec.key] = rec;
  return rec;
});
const persistent = new Set(zw.persistent_empty || []);
const tide = new Set(zw.tide || []);
const dormantSet = new Set(Array.isArray(dormant) ? dormant : dormant.keys || []);

// alive today = source key in latest snapshot has a non-empty item list.
// latest.json items is { sourceKey: [item, ...] }
const aliveSet = new Set();
const itemsObj = latest.items || {};
for (const [k, v] of Object.entries(itemsObj)) {
  const n = Array.isArray(v) ? v.length : (v && v.items ? v.items.length : 0);
  if (n > 0) aliveSet.add(k);
}
let aliveToday = aliveSet.size;
const itemCount = Object.values(itemsObj).reduce(
  (a, v) => a + (Array.isArray(v) ? v.length : (v && v.items ? v.items.length : 0)), 0);

const total = feedList.length;
const deadN = persistent.size;
const dormantN = dormantSet.size;
const tideN = tide.size;

const cards = [
  { n: fmt(total), l: "feeds tracked daily", cls: "" },
  { n: fmt(aliveToday), l: "alive today", cls: "alive" },
  { n: fmt(deadN), l: "suspected dead (3× empty)", cls: "dead" },
  { n: fmt(dormantN), l: "dormant (no new posts)", cls: "" },
  { n: fmt(tideN), l: "empty this round (tide)", cls: "" },
  { n: fmt(itemCount), l: "items collected today", cls: "" },
];
document.getElementById("cards").innerHTML = cards
  .map((c) => `<div class="card ${c.cls}"><div class="n">${c.n}</div><div class="l">${c.l}</div></div>`)
  .join("");

// per-lane table
const laneName = { br: "blogs / blogrolls", yt: "YouTube channels", nl: "newsletters", sec: "security", eb: "eng blogs", tb: "tech blogs", pb: "podcasts / personal", misc: "misc / community", tldr: "TLDR", github: "GitHub", aws: "AWS", gitlab: "GitLab", slack: "Slack", meta: "Meta" };
const byLane = {};
for (const f of feedList) {
  const lane = f.lane || (f.key || "").split("_")[0] || "?";
  const L = (byLane[lane] = byLane[lane] || { n: 0, dorm: 0, dead: 0, alive: 0 });
  L.n++;
  if (f.dormant || dormantSet.has(f.key)) L.dorm++;
  if (persistent.has(f.key)) L.dead++;
  if (aliveSet.has(f.key)) L.alive++;
}
// keys in persistent/tide that aren't in feedMap (already pruned) get counted under "other"
for (const k of persistent) if (!feedMap[k]) (byLane._gone = byLane._gone || { n: 0, dorm: 0, dead: 0, alive: 0 }).dead++, byLane._gone.n++;

const rows = Object.entries(byLane)
  .sort((a, b) => b[1].n - a[1].n)
  .map(([lane, L]) => {
    const pct = L.n ? ((100 * L.alive) / L.n).toFixed(1) : "0.0";
    const name = lane === "_gone" ? "pruned keys" : laneName[lane] || lane;
    return `<tr><td>${esc(name)}</td><td class="num">${fmt(L.n)}</td><td class="num">${fmt(L.dorm)}</td><td class="num">${fmt(L.dead)}</td><td class="num">${fmt(L.alive)}</td><td class="num">${pct}%</td></tr>`;
  });
document.querySelector("#lanes tbody").innerHTML = rows.join("");

if (!feedList.length) {
  document.getElementById("cards").innerHTML = '<p id="err">could not load data/feeds.json — try again later.</p>';
}
