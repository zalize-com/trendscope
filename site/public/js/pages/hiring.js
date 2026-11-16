const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
const $ = id => document.getElementById(id);
const fmt = n => n >= 1e3 ? (n/1e3).toFixed(1)+"k" : String(n);


async function main() {
  const [j, hist] = await Promise.all([
    fetch("data/hiring.json").then(r => r.json()).catch(() => null),
    fetch("docs/api/hiring-history.json").then(r => r.json()).catch(() => null),
  ]);
  if (!j || !j.threads) { $("cards").innerHTML = "<p>no data yet</p>"; return; }
  const th = j.threads;
  const hire = th.hiring, seek = th.seeking;
  $("cards").innerHTML = `
    <div class="card hire"><h3>WHO IS HIRING — ${esc(hire?.month || "")}</h3>
      <div class="n">${hire ? fmt(hire.comments) : "—"}</div>
      <small>comments = open positions posted</small>
      ${hire ? `<a href="${hire.url}">${esc(hire.title)} ↗</a>` : ""}</div>
    <div class="card seek"><h3>WHO WANTS TO BE HIRED — ${esc(seek?.month || "")}</h3>
      <div class="n">${seek ? fmt(seek.comments) : "—"}</div>
      <small>comments = candidates looking</small>
      ${seek ? `<a href="${seek.url}">${esc(seek.title)} ↗</a>` : ""}</div>
    ${th.freelancer ? `<div class="card"><h3>FREELANCER — ${esc(th.freelancer.month)}</h3>
      <div class="n" style="color:var(--accent)">${fmt(th.freelancer.comments)}</div>
      <small>comments = freelance gigs/offers</small>
      <a href="${th.freelancer.url}">${esc(th.freelancer.title)} ↗</a></div>` : ""}`;
  if (hire && seek) {
    const ratio = hire.comments / seek.comments;
    $("note").innerHTML = `Market ratio this month: <b>${ratio.toFixed(2)}</b> positions per seeker
      ${ratio > 0.6 ? "— candidate-favorable" : ratio > 0.4 ? "— balanced" : "— employer-favorable"}.`;
  }
  // 15-year monthly history (hiring-monthly.csv, backfilled via Algolia)
  const mc = await fetch("data/hiring-monthly.csv", {cache:"no-cache"}).then(r => r.text()).catch(() => "");
  const mrows = mc.trim().split("\n").slice(1).map(l => l.split(","))
    .filter(c => c.length >= 4)
    .map(c => ({ month: c[0], kind: c[1], comments: +c[2] }));
  if (mrows.length > 4) {
    const MN = ["January","February","March","April","May","June","July",
                "August","September","October","November","December"];
    const months = [...new Set(mrows.map(r => r.month))].sort((a, b) => {
      const [am, ay] = a.split(" "), [bm, by] = b.split(" ");
      return (+ay - +by) || (MN.indexOf(am) - MN.indexOf(bm));
    });
    const series = k => months.map(m => {
      const r = mrows.find(x => x.month === m && x.kind === k);
      return r ? r.comments : null;
    });
    const hS = series("hiring"), sS = series("seeking"), fS = series("freelancer");
    const W = 820, H = 260, P = 34;
    const max = Math.max(...hS.filter(v => v != null), ...sS.filter(v => v != null), ...fS.filter(v => v != null), 1);
    const x = i => P + (W - 2 * P) * (i / Math.max(1, months.length - 1));
    const y = v => H - P - (H - 2 * P) * (v / max);
    const line = (pts, color) => {
      let d = "", started = false;
      pts.forEach((v, i) => { if (v == null) return; d += (started ? " L" : "M") + x(i).toFixed(1) + " " + y(v).toFixed(1); started = true; });
      return `<path d="${d}" fill="none" stroke="${color}" stroke-width="1.6"/>`;
    };
    const yearTicks = months.map((m, i) => m.startsWith("January")
      ? `<text x="${x(i)}" y="${H-8}" fill="var(--dim)" font-size="10" text-anchor="middle">${m.slice(-4)}</text>` : "").join("");
    const peak = months[hS.indexOf(Math.max(...hS.filter(v=>v!=null)))];
    $("hist").innerHTML = `<h2>${months.length} months of HN hiring threads — ${months[0].split(" ")[1]} → ${months[months.length-1].split(" ")[1]}</h2>
      <svg class="chart" viewBox="0 0 ${W} ${H}">
        <line x1="${P}" y1="${H-P}" x2="${W-P}" y2="${H-P}" stroke="var(--border)"/>
        <line x1="${P}" y1="${P}" x2="${P}" y2="${H-P}" stroke="var(--border)"/>
        ${line(hS, "var(--green)")}${line(sS, "var(--orange)")}${line(fS, "var(--accent)")}
        ${yearTicks}
        <text x="8" y="${y(max)}" fill="var(--dim)" font-size="10">${fmt(max)}</text>
      </svg>
      <div class="leg"><b><span class="dot" style="background:var(--green)"></span>who is hiring</b>
        <b><span class="dot" style="background:var(--orange)"></span>who wants to be hired</b>
        <b><span class="dot" style="background:var(--accent)"></span>freelancer</b>
        <b style="margin-left:auto">hiring peak: ${esc(peak)} (${fmt(Math.max(...hS.filter(v=>v!=null)))})</b></div>`;
  }

  const rows = (hist && hist.rows || []).map(r => ({ at: r.captured_at, kind: r.kind, month: r.month, comments: +r.comments }));
  if (rows.length < 2) return;
  const days = [...new Set(rows.map(r => r.at.slice(0, 10)))].sort();
  const hirePts = days.map(d => (rows.filter(r => r.kind === "hiring" && r.at.startsWith(d)).pop() || {}).comments);
  const seekPts = days.map(d => (rows.filter(r => r.kind === "seeking" && r.at.startsWith(d)).pop() || {}).comments);
  const freePts = days.map(d => (rows.filter(r => r.kind === "freelancer" && r.at.startsWith(d)).pop() || {}).comments);
  const W = 820, H = 240, P = 30;
  const max = Math.max(...hirePts, ...seekPts, ...freePts.filter(v => v != null), 1);
  const x = i => P + (W - 2 * P) * (days.length < 2 ? 0.5 : i / (days.length - 1));
  const y = v => H - P - (H - 2 * P) * (v / max);
  const line = (pts, color) => pts.map((v, i) => v == null ? "" :
    `<circle cx="${x(i)}" cy="${y(v)}" r="3" fill="${color}"/>`).join("") +
    `<polyline fill="none" stroke="${color}" stroke-width="2" points="` +
    pts.map((v, i) => v == null ? "" : `${x(i)},${y(v)}`).filter(Boolean).join(" ") + `"/>`;
  $("daily").innerHTML = `<h2>comments per day — ${esc(hire?.month || "")}</h2>
    <svg class="chart" viewBox="0 0 ${W} ${H}">
      <line x1="${P}" y1="${H-P}" x2="${W-P}" y2="${H-P}" stroke="var(--border)"/>
      <line x1="${P}" y1="${P}" x2="${P}" y2="${H-P}" stroke="var(--border)"/>
      ${line(hirePts, "var(--green)")}${line(seekPts, "var(--orange)")}${line(freePts, "var(--accent)")}
      ${days.map((d, i) => `<text x="${x(i)}" y="${H-8}" fill="var(--dim)" font-size="10" text-anchor="middle">${d.slice(5)}</text>`).join("")}
      <text x="8" y="${y(max)}" fill="var(--dim)" font-size="10">${fmt(max)}</text>
    </svg>
    <div class="leg"><b><span class="dot" style="background:var(--green)"></span>who is hiring</b>
      <b><span class="dot" style="background:var(--orange)"></span>who wants to be hired</b>
      <b><span class="dot" style="background:var(--accent)"></span>freelancer</b></div>`;
}
main();
