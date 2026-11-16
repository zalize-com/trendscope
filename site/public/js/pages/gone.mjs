const d = await fetch("docs/api/gone.json").then(r => r.json());
const tb = document.getElementById("tb");
for (let i = 0; i < d.items.length; i++) {
  const it = d.items[i];
  const tr = document.createElement("tr");
  tr.innerHTML = `<td>${i + 1}</td>
    <td><a href="${it.url || "#"}">${it.title}</a></td>
    <td class="src">${it.source}</td>
    <td>${it.rank ?? ""}</td>
    <td class="src">${it.score ?? ""} ${it.metric || ""}</td>`;
  tb.appendChild(tr);
}
document.getElementById("note").textContent =
  `${d.items.length} items dropped · ${d.previous_snapshot} → ${d.latest_snapshot}`;
