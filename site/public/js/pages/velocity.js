const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
const fmt = n => n >= 1e9 ? (n/1e9).toFixed(1)+"B" : n >= 1e6 ? (n/1e6).toFixed(1)+"M" : n >= 1e3 ? (n/1e3).toFixed(1)+"k" : (Math.round(n*10)/10)+"";
fetch("docs/api/velocity.json", {cache:"no-cache"}).then(r => r.json()).then(d => {
  const top = d.items.slice(0, 40);
  document.getElementById("grid").innerHTML = top.length
    ? '<table><tr><th>#</th><th>title</th><th>+/day</th><th>latest</th><th>days</th></tr>' +
      top.map((it,i) => `<tr><td class="d">${i+1}</td>
        <td><a href="${esc(it.url)}" target="_blank" rel="noopener">${esc(it.title)}</a> <span class="src">${esc(srcName(it.source))}</span></td>
        <td class="n">+${fmt(it.per_day)} ${esc(it.metric||"")}/d</td>
        <td class="n">${fmt(it.latest)}</td>
        <td class="d">${it.days}d</td></tr>`).join("") + "</table>"
    : '<p id="err">no multi-day items yet — velocity needs items that stay on front pages across snapshots</p>';
  document.getElementById("sub").textContent =
    `${d.total} multi-day items · snapshot ${d.latest_snapshot} · top ${top.length} · rolling counters (npm/pypi/crates) excluded`;
}).catch(() => { document.getElementById("err").textContent = "velocity.json unavailable"; });
