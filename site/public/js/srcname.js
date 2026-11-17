// source key → human label: strip the lane prefix, underscores to spaces
// (sec_cyber_intelligence_insights → "cyber intelligence insights")
const PLATFORM = { github_trending: "github trending", gitlab_stars: "gitlab stars" };
window.srcName = s =>
  PLATFORM[s] ||
  String(s || "")
    .replace(/^(sec|eb|tb|br|nl|pb|yt|tldr|aws|github|gitlab|meta|slack)_/, "")
    .replace(/_/g, " ");

// unified score display: feed lanes rank items (score = inverse rank), so show
// "#N in feed"; other sources show "score metric". Pass the page's fmt() if any.
window.scoreText = (it, fmt) => {
  const f = fmt || (n => Number(n || 0).toLocaleString("en-US"));
  if (it && it.metric === "feed rank") return "#" + (it.rank ?? it.score) + " in feed";
  return f(it ? it.score : 0) + (it && it.metric ? " " + it.metric : "");
};

// kind-lite.json (non-post kinds: video/release/paper/...) — shared lazy loader.
// base = path prefix to repo root ("" at root, "../" under /daily/, /tools/).
let _kindsP = null;
window.loadKinds = (base = "") => {
  _kindsP = _kindsP || fetch(base + "data/kind-lite.json")
    .then(r => (r.ok ? r.json() : {}))
    .then(d => (window.__KINDS = d.kinds || {}))
    .catch(() => (window.__KINDS = {}));
  return _kindsP;
};
window.kindChip = url => {
  const k = (window.__KINDS || {})[url];
  return k ? `<span class="src kindchip">${k}</span>` : "";
};
