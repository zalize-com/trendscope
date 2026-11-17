const DOW = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];
const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
fetch("docs/api/weekday.json", {cache:"no-cache"}).then(r => r.json()).then(d => {
  const grid = {}, totals = {};
  for (const [s, v] of Object.entries(d.sources)) {
    grid[s] = Object.fromEntries(v.counts.map((c, i) => [i, c]));
    totals[s] = v.total;
  }
  const srcs = Object.keys(totals).sort((a,b)=>totals[b]-totals[a]);
  let max = 1;
  for (const s of srcs) for (const v of Object.values(grid[s]||{})) if (v > max) max = v;
  let h = '<table><tr><th>source</th>' + DOW.map(x=>`<th>${x}</th>`).join("") + '<th>total</th></tr>';
  for (const s of srcs) {
    h += `<tr><td class="src" title="${esc(s)}">${esc(srcName(s))}</td>`;
    for (let x = 0; x < 7; x++) {
      const v = (grid[s]||{})[x] || 0;
      const a = v ? (0.12 + 0.88*v/max).toFixed(2) : 0;
      h += `<td class="c" title="${v} items first-seen on ${DOW[x]}" style="background:rgba(88,166,255,${a})">${v||""}</td>`;
    }
    h += `<td class="c">${totals[s]}</td></tr>`;
  }
  document.getElementById("grid").innerHTML = h + "</table>";
  const notes = srcs.slice(0,4).map(s => {
    const ent = Object.entries(grid[s]||{}).sort((a,b)=>b[1]-a[1]);
    return `${esc(srcName(s))} peaks on <b>${DOW[ent[0]?.[0]]}</b> (${ent[0]?.[1]} items)`;
  }).join(" · ");
  const tot = Object.values(totals).reduce((a,b)=>a+b,0);
  document.getElementById("sub").textContent = `${tot} items · ${srcs.length} sources · ${d.days_tracked} days of snapshots`;
  document.getElementById("notes").innerHTML = notes + ". Based on the day each item first appeared on a front page — early days of data, so treat small numbers as directional.";
}).catch(() => { document.getElementById("err").textContent = "weekday.json unavailable"; });
