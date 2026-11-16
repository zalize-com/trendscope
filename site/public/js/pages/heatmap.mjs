const DOW=["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
try{
  const d=await (await fetch("docs/api/weekday.json")).json();
  const names=Object.keys(d.sources);
  const days=d.days_of_week||DOW;
  // find busiest + quietest (source,day) pairs globally
  let best=null,worst=null;
  const rows=names.map(n=>{
    const c=d.sources[n].counts;
    const mx=Math.max(...c,1);
    c.forEach((v,i)=>{
      if(!best||v>best[2])best=[n,days[i]||DOW[i],v];
      if(!worst||v<worst[2])worst=[n,days[i]||DOW[i],v];
    });
    return{n,c,mx,tot:d.sources[n].total};
  }).sort((a,b)=>b.tot-a.tot);
  document.getElementById("stats").innerHTML=
    `<span class="stat">${names.length} sources × 7 days</span>
     <span class="stat">${d.days_tracked||"?"} days tracked</span>
     <span class="stat">busiest: ${best[0]} ${best[1]} (${best[2]})</span>
     <span class="stat">quietest: ${worst[0]} ${worst[1]} (${worst[2]})</span>`;
  const shade=v=>v===0?"background:var(--bg)":`background:color-mix(in srgb,var(--acc) ${Math.round(8+92*v)}%,transparent);color:${v>0.55?"#fff":""}`;
  document.getElementById("out").innerHTML=`<table>
    <tr><th>source</th>${days.map(x=>`<th>${x}</th>`).join("")}<th>total</th></tr>
    ${rows.map(r=>`<tr><td class="src">${r.n}</td>${r.c.map(v=>`<td><span class="cell" style="${shade(v/r.mx)}">${v||""}</span></td>`).join("")}<td>${r.tot}</td></tr>`).join("")}
  </table>
  <p class="legend">cells are normalized within each row — deep blue = that source's busiest weekday, blank = zero items. totals are raw item counts.</p>`;
}catch(e){document.getElementById("err").textContent="failed to load weekday.json — "+e.message;}
