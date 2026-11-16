const d = await fetch("docs/api/streaks.json").then(r => r.json());
const rows = d.longest_all_time || [];
const tb = document.getElementById("tb");
for (let i = 0; i < rows.length; i++) {
  const it = rows[i];
  const tr = document.createElement("tr");
  const peak = it.top_rank != null ? "#" + it.top_rank : (it.top_score ?? "");
  tr.innerHTML = `<td>${i + 1}</td>
    <td><b>${it.days_on_board ?? ""}</b></td>
    <td>${it.longest_streak ?? ""}</td>
    <td><a href="${it.url || "#"}">${it.title}</a></td>
    <td>${it.source}</td>
    <td class="muted">${peak}${it.top_score != null && it.top_rank != null ? " · " + it.top_score : ""}</td>`;
  tb.appendChild(tr);
}
document.getElementById("note").textContent =
  `${rows.length} veterans over ${d.days_tracked} tracked days · generated ${d.generated_at?.slice(0,10) || ""}`;
