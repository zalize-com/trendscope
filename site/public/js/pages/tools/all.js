(function(){
  const data = JSON.parse(document.getElementById("tools-data").textContent);
  const grid = document.getElementById("grid");
  const q = document.getElementById("q");
  const esc = s => s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  let total = 0;
  for (const g in data) total += data[g].length;
  function render(filter){
    filter = (filter||"").trim().toLowerCase();
    let html = "", shown = 0;
    for (const g in data){
      const items = data[g].filter(t =>
        !filter || (t.name+" "+t.desc+" "+t.tool).toLowerCase().includes(filter));
      if (!items.length) continue;
      html += '<div class="cat">'+esc(g)+'</div><div class="cards">';
      for (const t of items){
        shown++;
        html += '<div class="card"><a href="'+esc(t.href)+'"><b>'+esc(t.name)+'</b>'+
                (t.desc?'<span>'+esc(t.desc)+'</span>':'')+'</a></div>';
      }
      html += '</div>';
    }
    grid.innerHTML = html || '<p class="none">no tools match “'+esc(filter)+'” — try “json”, “feed”, “color”…</p>';
    return shown;
  }
  render("");
  q.addEventListener("input", () => render(q.value));
  document.addEventListener("keydown", e => {
    if (e.key === "/" && document.activeElement !== q){ e.preventDefault(); q.focus(); }
  });
})();
