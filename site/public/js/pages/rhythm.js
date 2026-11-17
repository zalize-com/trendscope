const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
fetch("docs/api/rhythm.json", {cache:"no-cache"}).then(r => r.json()).then(d => {
  const grid = {}, totals = {};
  for (const [s, v] of Object.entries(d.sources)) {
    grid[s] = Object.fromEntries(v.counts.map((c, i) => [i, c]));
    totals[s] = v.total;
  }
  const srcs = Object.keys(totals).sort((a,b)=>totals[b]-totals[a]);
  const max = Math.max(...srcs.flatMap(s=>Object.values(grid[s]||{})),1);
  const hr = [...Array(24).keys()];
  let h = '<table><tr><th>source</th>' + hr.map(x=>`<th>${String(x).padStart(2,"0")}</th>`).join("") + '<th>total</th></tr>';
  for (const s of srcs) {
    h += `<tr><td class="src" title="${esc(s)}">${esc(srcName(s))}</td>`;
    for (const x of hr) {
      const v = (grid[s]||{})[x] || 0;
      const a = v ? (0.12 + 0.88*v/max).toFixed(2) : 0;
      h += `<td class="c" title="${v} captures at ${String(x).padStart(2,"0")}:00 UTC" style="background:rgba(88,166,255,${a})">${v||""}</td>`;
    }
    h += `<td class="c">${totals[s]}</td></tr>`;
  }
  document.getElementById("grid").innerHTML = h + "</table>";
  const peaks = srcs.slice(0,4).map(s => {
    const ent = Object.entries(grid[s]||{}).sort((a,b)=>b[1]-a[1]);
    return `${esc(srcName(s))} peaks ${String(ent[0]?.[0]).padStart(2,"0")}:00 UTC`;
  }).join(" · ");
  const tot = Object.values(totals).reduce((a,b)=>a+b,0);
  document.getElementById("sub").textContent = `${tot} captures · ${srcs.length} sources · ${d.days_tracked} days · UTC hours`;
  const ne = document.getElementById("notes"); if (ne) ne.innerHTML = peaks;
}).catch(() => { document.getElementById("err").textContent = "rhythm.json unavailable"; });
