const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
const fmt = n => n >= 1e3 ? (n/1e3).toFixed(1)+"k" : String(n);

function parseCSV(text) {
  const rows = []; let field = "", row = [], inQ = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQ) {
      if (c === '"') { if (text[i+1] === '"') { field += '"'; i++; } else inQ = false; }
      else field += c;
    } else if (c === '"') inQ = true;
    else if (c === ",") { row.push(field); field = ""; }
    else if (c === "\n") { row.push(field); rows.push(row); row = []; field = ""; }
    else if (c !== "\r") field += c;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  return rows;
}

const text = await fetch("data/show-hn-monthly.csv", {cache:"no-cache"}).then(r => r.text());
const rows = parseCSV(text).slice(1).filter(r => r.length >= 8 && r[0]);
const canon = rows.map(r => ({ month: r[0], rank: +r[1], title: r[2], url: r[3],
  points: +r[4], comments: +r[5], author: r[6], hn: r[8] }));
const months = [...new Set(canon.map(c => c.month))].sort();
const years = [...new Set(months.map(m => m.slice(0,4)))].sort();

document.getElementById("stats").innerHTML = `
  <div class="stat"><b>${months.length}</b><small>months</small></div>
  <div class="stat"><b>${canon.length}</b><small>stories</small></div>
  <div class="stat"><b>${fmt(canon.reduce((a,c)=>a+c.points,0))}</b><small>total points</small></div>
  <div class="stat"><b>${fmt(Math.max(...canon.map(c=>c.points)))}</b><small>peak score</small></div>`;

// attention inflation: avg points of the #1 story per year
const byYear = {};
canon.filter(c => c.rank === 1).forEach(c => {
  const y = c.month.slice(0,4);
  (byYear[y] = byYear[y] || []).push(c.points);
});
const yAvg = Object.entries(byYear).sort().map(([y, pts]) =>
  [y, Math.round(pts.reduce((a,b)=>a+b,0)/pts.length)]);
const yMax = Math.max(...yAvg.map(x=>x[1]));
document.getElementById("infl").innerHTML = yAvg.map(([y,v]) =>
  `<div class="bcol" title="${y}: avg #1 score ${fmt(v)}">
    <span class="v">${y.endsWith("0")||y.endsWith("5")||v===yMax?fmt(v):""}</span>
    <div class="b" style="height:${Math.max(4,Math.round(78*v/yMax))}px${v===yMax?";background:var(--orange);opacity:1":""}"></div>
    <span class="y">${y.slice(2)}</span></div>`).join("");

// this month in history: rank-1 story of the same month, every year
const curM = months[months.length-1];
const mm = curM.slice(5);
const timh = canon.filter(c => c.month.slice(5) === mm && c.rank === 1 && c.month !== curM)
  .sort((a,b) => b.month.localeCompare(a.month));
document.getElementById("timh").innerHTML = timh.map((c,i) =>
  `<li><span class="r">${c.month.slice(0,4)}</span><span class="it">
   <a href="${c.url}">${esc(c.title)}</a><a class="trj" href="item.html?q=${encodeURIComponent(c.title)}" title="trajectory">⤳</a></span><span class="sc"><b>${fmt(c.points)}</b> pts</span></li>`).join("")
  || '<li class="it" style="color:var(--dim)">no prior years for this month</li>';

// month explorer: any month's top-10
const mpick = document.getElementById("mpick");
mpick.innerHTML = [...months].reverse().map(m => `<option>${m}</option>`).join("");
function renderMonth(m) {
  document.getElementById("browse").innerHTML = canon.filter(c => c.month === m)
    .sort((a,b) => a.rank - b.rank).map(c =>
      `<li><span class="r">${c.rank}</span><span class="it">
       <a href="${c.url}">${esc(c.title)}</a><a class="trj" href="item.html?q=${encodeURIComponent(c.title)}" title="trajectory">⤳</a></span>
       <span class="sc"><b>${fmt(c.points)}</b> pts · ${fmt(c.comments)}💬 · <a href="${c.hn}">hn</a></span></li>`).join("");
}
mpick.onchange = () => renderMonth(mpick.value);
mpick.value = months[months.length - 1];
renderMonth(mpick.value);

// year chips
const P = new URLSearchParams(location.search);
let yr = P.get("y") || "";
document.getElementById("years").innerHTML =
  `<a class="${!yr?"on":""}" href="showhn.html">all time</a>` +
  years.map(y => `<a class="${y===yr?"on":""}" href="showhn.html?y=${y}">${y}</a>`).join("");

const pool = (yr ? canon.filter(c => c.month.startsWith(yr)) : canon)
  .slice().sort((a,b) => b.points - a.points).slice(0, 40);
document.getElementById("out").innerHTML = pool.map((c,i) =>
  `<li><span class="r">${i+1}</span><span class="it">
   <a href="${c.url}">${esc(c.title)}</a><a class="trj" href="item.html?q=${encodeURIComponent(c.title)}" title="trajectory">⤳</a><span class="yr">${c.month}</span></span>
   <span class="sc"><b>${fmt(c.points)}</b> pts · ${fmt(c.comments)}💬 · <a href="${c.hn}">hn</a></span></li>`).join("");
