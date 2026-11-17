// source key → human label: strip the lane prefix, underscores to spaces
// (sec_cyber_intelligence_insights → "cyber intelligence insights")
window.srcName = s =>
  String(s || "")
    .replace(/^(sec|eb|tb|br|nl|pb|yt|tldr|aws|github|gitlab|meta|slack)_/, "")
    .replace(/_/g, " ");
