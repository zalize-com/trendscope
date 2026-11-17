(function(){
  const data = JSON.parse(document.getElementById("tools-data").textContent);
  const grid = document.getElementById("grid");
  const q = document.getElementById("q");
  const esc = s => s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  // favorites — localStorage, it-tools style: star on each card, favs float to top
  const KEY = "ts_tool_favs";
  let favs = new Set(JSON.parse(localStorage.getItem(KEY) || "[]"));
  const save = () => localStorage.setItem(KEY, JSON.stringify([...favs]));
  const all = [];
  for (const g in data) for (const t of data[g]) all.push({...t, group: g});
  function card(t){
    const on = favs.has(t.tool);
    return '<div class="card"><button class="fav'+(on?' on':'')+'" data-fav="'+esc(t.tool)+'" title="'+(on?'remove from favorites':'favorite')+'">'+(on?'★':'☆')+'</button>'+
      '<a href="'+esc(t.href)+'"><b>'+esc(t.name)+'</b>'+
      (t.desc?'<span>'+esc(t.desc)+'</span>':'')+'</a></div>';
  }
  function group(label, items){
    if (!items.length) return "";
    return '<div class="cat">'+esc(label)+'</div><div class="cards">'+items.map(card).join('')+'</div>';
  }
  function render(filter){
    filter = (filter||"").trim().toLowerCase();
    const match = t => !filter || (t.name+" "+t.desc+" "+t.tool).toLowerCase().includes(filter);
    let html = "", shown = 0;
    const fv = all.filter(t => favs.has(t.tool) && match(t));
    html += group("★ favorites", fv); shown += fv.length;
    for (const g in data){
      const items = data[g].filter(t => match({...t, group: g}));
      if (!items.length) continue;
      html += group(g, items.map(t => ({...t, group: g}))); shown += items.length;
    }
    grid.innerHTML = html || '<p class="none">no tools match “'+esc(filter)+'” — try “json”, “feed”, “color”…</p>';
    return shown;
  }
  render("");
  q.addEventListener("input", () => render(q.value));
  grid.addEventListener("click", e => {
    const b = e.target.closest("[data-fav]");
    if (!b) return;
    e.preventDefault();
    const id = b.dataset.fav;
    favs.has(id) ? favs.delete(id) : favs.add(id);
    save();
    render(q.value);
  });
  document.addEventListener("keydown", e => {
    if (e.key === "/" && document.activeElement !== q){ e.preventDefault(); q.focus(); }
  });
})();
