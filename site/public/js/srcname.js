// source key → human label: strip the lane prefix, underscores to spaces
// (sec_cyber_intelligence_insights → "cyber intelligence insights")
window.srcName = s =>
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
