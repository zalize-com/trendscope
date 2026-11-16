const BASE = "https://trendscope--plov6nur.preview.devinapps.com/embed.html";
const MODES = [
  ["board (default)", ""],
  ["stats", "?mode=stats"],
  ["topics", "?mode=topics"],
  ["streak", "?mode=streak"],
  ["week", "?mode=week"],
  ["movers", "?mode=movers"],
  ["velocity", "?mode=velocity"],
  ["weekday", "?mode=weekday"],
  ["heatmap", "?mode=heatmap"],
    ["health", "?mode=health"],
    ["streaks", "?mode=streaks"],
  ["rhythm", "?mode=rhythm"],
  ["new", "?mode=new"],
  ["risers", "?mode=risers"],
  ["discussed", "?mode=discussed"],
  ["crossovers", "?mode=crossovers"],
  ["canon", "?mode=canon"],
  ["hiring", "?mode=hiring"],
  ["ideas", "?mode=ideas"],
  ["domain", "?mode=domain"],
  ["author", "?mode=author"],
  ["sources", "?mode=sources"],
  ["item", "?mode=item&q=Show%20HN"],
  ["radar", "?mode=radar"],
  ["watch", "?mode=watch&kw=rust%2Csqlite"],
  ["meteors", "?mode=meteors"],
  ["veterans", "?mode=veterans"],
  ["gone", "?mode=gone"],
];
const esc = s => s.replace(/&/g,"&amp;").replace(/</g,"&lt;");
document.getElementById("out").innerHTML = MODES.map(([name, q]) => {
  const src = BASE + q + (q ? "&" : "?") + "n=6";
  const snip = `<iframe src="${src}" width="420" height="300" frameborder="0" loading="lazy"></iframe>`;
  return `<div class="card"><h3>${name}</h3><code>${esc(snip)}</code><iframe src="${src}" loading="lazy"></iframe></div>`;
}).join("");
