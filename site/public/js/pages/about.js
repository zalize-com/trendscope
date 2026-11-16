let SRC=[];
  const body=document.getElementById('dir-body');
  const lanes=['all','curated','newsletter','engblog','security','blogroll'];
  let lane='all',q='';
  function esc(s){const d=document.createElement('div');d.textContent=s;return d.innerHTML;}
  function laneOf(k){return k.startsWith('br_')?'blogroll':k.startsWith('sec_')?'security':k.startsWith('eb_')?'engblog':k.startsWith('nl_')?'newsletter':k.startsWith('tldr_')||k.startsWith('yt_')||k.startsWith('pb_')||k.startsWith('tb_')?k.split('_')[0]:'curated';}
  function render(){
    const rows=[];
    let n=0;
    for(const k of Object.keys(SRC)){
      const s=SRC[k];
      const ln=s.type||laneOf(k);
      if(lane!=='all'&&ln!==lane)continue;
      if(q&&!(k.includes(q)||(s.name||'').toLowerCase().includes(q)||(s.home||'').includes(q)))continue;
      n++;
      if(rows.length<400)
        rows.push(`<tr><td><code>${esc(k)}</code></td><td>${s.home?`<a href="${esc(s.home)}">${esc(s.name).slice(0,70)}</a>`:esc(s.name)}</td><td>${esc(ln)}</td><td>${esc(s.metric||'')}</td></tr>`);
    }
    body.innerHTML=rows.join('');
    document.getElementById('dir-meta').innerHTML=`<b>${n.toLocaleString()}</b> sources shown`+(n>400?' (first 400)':'')+' — canonical list: <a href="docs/SOURCES.md">docs/SOURCES.md</a>';
  }
  document.getElementById('dir-chips').innerHTML=lanes.map(l=>`<button data-l="${l}" style="margin:0 4px 6px 0;padding:3px 10px;border:1px solid var(--border);border-radius:12px;background:${l===lane?'var(--accent)':'var(--panel)'};color:var(--fg);cursor:pointer;font:inherit;font-size:12px">${l}</button>`).join('');
  document.getElementById('dir-chips').onclick=e=>{if(e.target.dataset.l){lane=e.target.dataset.l;render();document.querySelectorAll('#dir-chips button').forEach(b=>b.style.background=b.dataset.l===lane?'var(--accent)':'var(--panel'));}};
  document.getElementById('dir-q').oninput=e=>{q=e.target.value.trim().toLowerCase();render();};
  fetch('data/sources.json').then(r=>r.json()).then(s=>{SRC=s;render();}).catch(()=>{document.getElementById('dir-meta').textContent='directory failed to load — see docs/SOURCES.md';});
