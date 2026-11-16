const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
const $ = document.getElementById("out");

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

try {
  const txt = await fetch("data/health-log.csv", {cache:"no-cache"}).then(r => r.text());
  const [hdr, ...rs] = parseCSV(txt);
  const ci = Object.fromEntries(hdr.map((h,i)=>[h,i]));
  const runs = rs.map(r => ({date:r[ci.date], source:r[ci.source],
    ok:r[ci.ok]==="1", items:+r[ci.items], ms:+r[ci.ms]}));

  // rollup per source
  const bySrc = {};
  for (const r of runs) {
    const s = bySrc[r.source] ||= {runs:0, ok:0, ms:[], items:[]};
    s.runs++; s.ok += r.ok ? 1 : 0; s.ms.push(r.ms); s.items.push(r.items);
  }
  const days = [...new Set(runs.map(r=>r.date))].sort();
  const totalRuns = runs.length, okRuns = runs.filter(r=>r.ok).length;

  // consecutive all-green days
  const byDay = {};
  for (const r of runs) byDay[r.date] = (byDay[r.date] ?? true) && r.ok;
  let green = 0;
  for (const d of [...days].reverse()) { if (!byDay[d]) break; green++; }

  const allOk = days.length && Object.values(byDay).every(Boolean);
  $.innerHTML = `
    <div class="banner" style="border-color:${allOk ? "var(--green)" : "var(--red)"}">
      ${allOk ? "● all systems operational" : "● degraded"}
      — ${okRuns}/${totalRuns} source-runs green · ${days.length} day${days.length===1?"":"s"} logged
      ${green ? ` · <b style="color:var(--green)">${green} day${green===1?"":"s"} all-green</b>` : ""}
    </div>
    <h2>uptime matrix <span style="text-transform:none">(date × source)</span></h2>
    <div class="legend"><span class="dot ok"></span>ok <span class="dot bad"></span>failed <span class="dot none"></span>no run</div>
    <table><tr><th>source</th>${days.map(d=>`<th>${d.slice(5)}</th>`).join("")}</tr>
      ${Object.keys(bySrc).sort().map(s => `<tr><td class="src">${s}</td>${
        days.map(d => {
          const rr = runs.filter(r => r.date===d && r.source===s);
          const cls = !rr.length ? "none" : rr.every(r=>r.ok) ? "ok" : "bad";
          return `<td><span class="dot ${cls}" title="${rr.map(r=>r.ms+"ms").join(", ")||"—"}"></span></td>`;
        }).join("")}</tr>`).join("")}
    </table>
    <h2>per-source rollup</h2>
    <table><tr><th>source</th><th class="num">uptime</th><th class="num">runs</th>
      <th class="num">avg items</th><th class="num">median ms</th><th class="num">p95 ms</th></tr>
      ${Object.entries(bySrc).sort((a,b)=>a[0].localeCompare(b[0])).map(([s,v]) => {
        const ms = [...v.ms].sort((a,b)=>a-b);
        const med = ms[Math.floor(ms.length/2)], p95 = ms[Math.floor(ms.length*0.95)] || ms[ms.length-1];
        return `<tr><td class="src">${s}</td>
          <td class="num">${(100*v.ok/v.runs).toFixed(0)}%</td>
          <td class="num">${v.runs}</td>
          <td class="num">${(v.items.reduce((a,b)=>a+b,0)/v.items.length).toFixed(1)}</td>
          <td class="num">${med}</td><td class="num">${p95}</td></tr>`;
      }).join("")}
    </table>
    <p class="legend" style="margin-top:14px">npm/PyPI latency is one request per watched package — slower by design.</p>`;
} catch (e) {
  $.innerHTML = `<p id="err">health log not available yet — the pipeline writes it on each daily run.</p>`;
}
