const TOPIC_RULES = {
  "AI/LLM": ["ai","llm","gpt","claude","gemini","openai","anthropic","machine learning","ml ","neural","diffusion","agent","rag","transformer","model","inference","fine-tun","copilot","mcp","prompt"],
  "Web Dev": ["react","vue","svelte","angular","next.js","nextjs","typescript","javascript","css","html","web","vite","tailwind","frontend","browser","dom"],
  "DevOps/Infra": ["kubernetes","k8s","docker","terraform","ci/cd","deploy","aws","cloud","serverless","infra","observability","monitor","devops"],
  "Security": ["security","vuln","cve","exploit","breach","malware","ransomware","phishing","zero-day","0day","auth","encryption","privacy"],
  "Data Eng": ["data","postgres","sql","database","duckdb","pipeline","etl","spark","kafka","analytics","warehouse","dbt"],
  "Languages": ["rust","golang","go ","python","java","kotlin","swift","zig","c++","compiler","lua"],
  "Tools/OSS": ["open source","cli","tool","github","git ","editor","vscode","neovim","terminal","framework","library","release","v1.0"],
  "Career/Business": ["startup","hiring","salary","remote","career","interview","acquisition","ipo","funding","layoff","business","saas"],
};
const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
const fmt = n => {
  const s = n < 0 ? "-" : "", a = Math.abs(n);
  return s + (a >= 1e9 ? (a/1e9).toFixed(1)+"B" : a >= 1e6 ? (a/1e6).toFixed(1)+"M" : a >= 1e3 ? (a/1e3).toFixed(1)+"k" : String(a));
};
const topicsOf = it => {
  const text = `${it.title||""} ${(it.tags||[]).join(" ")} ${it.description||""}`.toLowerCase();
  return Object.keys(TOPIC_RULES).filter(t => TOPIC_RULES[t].some(k => text.includes(k)));
};

const params = new URLSearchParams(location.search);
const want = params.get("t");

fetch("data/latest-lite.json", {cache:"no-cache"}).then(r=>r.ok?r:Promise.reject()).catch(()=>fetch("data/latest.json",{cache:"no-cache"})).then(r => r.json()).then(snap => {
  const all = Object.entries(snap.items).flatMap(([s, its]) => its);
  const chipHTML = Object.keys(TOPIC_RULES).map(t => {
    const c = (snap.topics.find(x => x.topic === t) || {}).count || 0;
    return `<a class="chip ${t === want ? "on" : ""}" href="topics.html?t=${encodeURIComponent(t)}">${t} <b>${c}</b></a>`;
  }).join("");
  document.getElementById("chips").innerHTML = chipHTML;

  if (!want || !TOPIC_RULES[want]) {
    document.getElementById("h1").innerHTML = "topi<span>cs</span>";
    document.getElementById("sub").textContent = `${snap.date} snapshot — pick a topic`;
    document.getElementById("out").innerHTML = (snap.topics||[]).map(t =>
      `<h2><a href="topics.html?t=${encodeURIComponent(t.topic)}">${t.topic}</a> — ${t.count} items
       <span class="spark" data-topic="${t.topic}"></span></h2>
       <ol>${(t.examples||[]).map(e => `<li><span class="it"><a href="${e.url}">${esc(e.title)}</a> <span class="sc">${e.source}</span></span></li>`).join("")}</ol>`).join("");
    // per-topic daily counts → inline sparkline
    fetch("docs/api/topics.json", {cache:"no-cache"}).then(r => r.json()).then(d => {
      const days = d.days, topics = d.topics;
      document.querySelectorAll(".spark").forEach(el => {
        const t = el.dataset.topic;
        const vals = days.map(dd => (topics[t] && topics[t].counts[dd]) || 0);
        const mx = Math.max(...vals, 1);
        el.innerHTML = `<svg width="${days.length * 8}" height="14" viewBox="0 0 ${days.length * 8} 14" style="vertical-align:-2px;margin-left:8px">${
          vals.map((v,i) => `<rect x="${i*8}" y="${14 - Math.round(12*v/mx)}" width="6" height="${Math.max(1,Math.round(12*v/mx))}" fill="var(--accent)" opacity="${0.35 + 0.65*v/mx}"/>`).join("")}</svg>`;
        el.title = vals.map((v,i) => `${days[i]}: ${v}`).join(" · ");
      });
      // topic movers: last day vs mean of the previous days
      if (days.length >= 2) {
        const allT = Object.keys(topics);
        const deltas = allT.map(t => {
          const now = (topics[t] && topics[t].counts[days[days.length-1]]) || 0;
          const prev = days.slice(0, -1).map(dd => (topics[t] && topics[t].counts[dd]) || 0);
          const avg = prev.reduce((a,b) => a+b, 0) / prev.length;
          return { t, now, delta: now - avg };
        }).filter(x => Math.abs(x.delta) >= 1)
          .sort((a,b) => b.delta - a.delta);
        if (deltas.length)
          document.getElementById("movers").innerHTML = "topic movers vs recent avg: " + deltas.slice(0,4).map(x =>
            `<a href="topics.html?t=${encodeURIComponent(x.t)}" style="color:${x.delta>0?"var(--green)":"var(--orange)"}">${x.t} ${x.delta>0?"+":"−"}${Math.abs(x.delta).toFixed(1)}</a>`).join(" · ");
      }
    }).catch(() => {});
    return;
  }

  document.title = `${want} — today's developer attention | trendscope`;
  document.getElementById("h1").innerHTML = `<span>${esc(want)}</span>`;
  const matched = all.filter(it => topicsOf(it).includes(want));
  document.getElementById("sub").textContent =
    `${matched.length} items across ${new Set(matched.map(i=>i.source)).size} sources · ${snap.date} snapshot`;
  fetch("docs/api/topics.json", {cache:"no-cache"}).then(r => r.json()).then(d => {
    const days = d.days;
    const vals = days.map(dd => (d.topics[want] && d.topics[want].counts[dd]) || 0);
    const mx = Math.max(...vals, 1);
    const el = document.getElementById("sub");
    el.innerHTML = `${el.textContent} · <svg width="${days.length * 8}" height="14"
      viewBox="0 0 ${days.length * 8} 14" style="vertical-align:-2px" title="${days.map((d,i)=>`${d}: ${vals[i]}`).join(" · ")}">${
      vals.map((v,i) => `<rect x="${i*8}" y="${14 - Math.round(12*v/mx)}" width="6" height="${Math.max(1,Math.round(12*v/mx))}" fill="var(--accent)" opacity="${0.35 + 0.65*v/mx}"/>`).join("")}</svg>`;
  }).catch(() => {});
  const bySrc = {};
  matched.forEach(it => (bySrc[it.source] = bySrc[it.source] || []).push(it));
  document.getElementById("out").innerHTML = Object.entries(bySrc)
    .sort((a,b) => b[1].length - a[1].length).map(([s, its]) =>
      `<h2>${s} — ${its.length}</h2><ol>${its.map((it,i) =>
        `<li><span class="r">${i+1}</span><span class="it"><a href="${it.url}">${esc(it.title)}</a><a class="trj" href="item.html?q=${encodeURIComponent(it.title)}" title="trajectory">⤳</a></span><span class="sc">${fmt(it.score)} ${it.metric}</span></li>`).join("")}</ol>`).join("");
}).catch(() => { document.getElementById("err").textContent = "snapshot unavailable"; });
