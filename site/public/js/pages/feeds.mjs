const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
const $ = id => document.getElementById(id);
const host = u => { try { return new URL(u).host; } catch { return u; } };

const LANE_NAMES = {
  br: "blogs & sites", yt: "YouTube", nl: "newsletters", sec: "security",
  eb: "engineering blogs", tb: "tech blogs", pb: "personal blogs",
  tldr: "TLDR", aws: "AWS", github: "GitHub", gitlab: "GitLab",
  meta: "Meta", slack: "Slack", misc: "other sources",
};

const laneDetails = ([lane, fs]) =>
  `<details data-lane="${esc(lane)}"><summary>${esc(LANE_NAMES[lane] || lane)}<small>${fs.length.toLocaleString()} feeds</small></summary>` +
  `<p class="lane-opml"><a href="data/opml/${encodeURIComponent(lane)}.opml" download>⬇ subscribe to this lane (OPML)</a></p>` +
  `<ul data-fill="${esc(lane)}"></ul></details>`;

const row = f => `<li class="feed"><a href="${esc(f.feed)}">${esc(f.label)}</a>` +
  `<span class="host">${esc(host(f.feed))}</span>` +
  (f.dormant ? `<span class="chip" title="alive but quiet — no new posts recently">dormant</span>` : "") +
  `<span class="acts"><button class="copy" data-url="${esc(f.feed)}" title="copy feed URL">copy</button>` +
  `<a href="source.html?s=${encodeURIComponent(f.key)}" title="deep dive">src</a></span></li>`;

try {
  const d = await fetch("data/feeds.json", {cache:"no-cache"}).then(r => r.json());
  const feeds = d.feeds;
  const lanes = {};
  for (const f of feeds) (lanes[f.lane] ||= []).push(f);
  const groups = Object.entries(lanes).sort((a,b) => b[1].length - a[1].length);

  $("stats").innerHTML =
    `<div class="stat"><b>${d.count.toLocaleString()}</b><small>feeds</small></div>` +
    `<div class="stat"><b>${groups.length}</b><small>lanes</small></div>` +
    `<div class="stat"><b>${feeds.filter(f=>f.dormant).length}</b><small>dormant</small></div>`;

  $("out").innerHTML = groups.map(laneDetails).join("");

  const byLane = l => lanes[l].map(row).join("");
  $("out").addEventListener("toggle", e => {
    if (e.target.tagName === "DETAILS" && e.target.open) {
      const ul = e.target.querySelector("ul[data-fill]");
      if (ul && !ul.dataset.done) { ul.innerHTML = byLane(ul.dataset.fill); ul.dataset.done = "1"; }
    }
  }, true);

  // copy-to-clipboard (delegate)
  $("out").addEventListener("click", e => {
    const b = e.target.closest("button.copy");
    if (!b) return;
    navigator.clipboard.writeText(b.dataset.url).then(() => { b.textContent = "copied"; setTimeout(() => b.textContent = "copy", 1200); });
  });

  // search → flat filtered list (lazy lane rendering suspended)
  let t;
  $("q").addEventListener("input", e => {
    clearTimeout(t);
    t = setTimeout(() => {
      const q = e.target.value.trim().toLowerCase();
      if (!q) {
        $("out").innerHTML = groups.map(laneDetails).join("");
        return;
      }
      const hits = feeds.filter(f =>
        f.label.toLowerCase().includes(q) || f.key.includes(q) || f.feed.toLowerCase().includes(q));
      $("out").innerHTML = hits.length
        ? `<p class="sub" style="margin:4px 0 8px">${hits.length.toLocaleString()} match${hits.length===1?"":"es"}${hits.length>200?" (first 200)":""}</p><ul>` +
          hits.slice(0,200).map(row).join("") + "</ul>"
        : `<p id="err">no feeds match “${esc(q)}”</p>`;
    }, 200);
  });
} catch (e) {
  console.error(e);
  $("err").textContent = "failed to load feeds.json";
}
