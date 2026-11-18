const esc = s => { const d = document.createElement("div"); d.textContent = s||""; return d.innerHTML; };
const fmt = n => n>=1e6?(n/1e6).toFixed(1)+"M":n>=1e3?(n/1e3).toFixed(1)+"k":String(n);
const data = await fetch("docs/api/crossovers.json", {cache:"no-cache"}).then(r => r.json()).catch(() => null);
if (!data) { document.getElementById("err").textContent = "could not load docs/api/crossovers.json"; } else {
const xs = data.crossovers || [];
const SRCS = [...new Set(xs.flatMap(x => x.sources))].sort();
const state = { src: null };
const bar = document.getElementById("srcbar");
bar.innerHTML = `<a class="chip on" href="#" data-s="">all</a>` + SRCS.map(s => `<a class="chip" href="#" data-s="${esc(s)}">${esc(srcName(s))}</a>`).join("");
bar.addEventListener("click", e => {
  const a = e.target.closest("a[data-s]"); if (!a) return; e.preventDefault();
  state.src = a.dataset.s || null;
  bar.querySelectorAll(".chip").forEach(c => c.classList.toggle("on", c === a));
  render();
});
function render() {
  const list = xs.filter(x => !state.src || x.sources.includes(state.src));
  const out = document.getElementById("out");
  if (!list.length) { out.innerHTML = `<p id="err">no crossovers yet — needs a story on 2+ sources in the same window.</p>`; return; }
  out.innerHTML = `<h2>${list.length} crossovers · snapshot ${esc(data.latest_snapshot)}</h2><ol>` +
    list.map(x => `<li>
      <span class="it"><a href="${esc(x.url)}">${esc(x.title)}</a></span>
      ${x.sources.map(s => `<span class="src${state.src===s?" on":""}">${esc(srcName(s))}</span>`).join("")}
      <span class="sc">${x.days}d · best ${scoreText(x.best, fmt)} on ${esc(srcName(x.best.source))} <span class="date">${esc(x.best.date)}</span></span>
    </li>`).join("") + `</ol>`;
}
render();
}
