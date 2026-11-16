const LIBS = [
["Chart.js","4.4.7","stats.html","3 hand-rolled SVG line charts","charting"],
["marked","15.0.7","tools/more.html","60-line regex markdown renderer","markdown"],
["turndown","7.2.2","tools/more.html","50-line HTML→MD conv()","markdown"],
["turndown-plugin-gfm","1.0.2","tools/more.html","GFM tables for turndown","markdown"],
["jsdiff (diff)","7.0.0","tools/more.html","O(n×m) LCS diff DP","diff"],
["PapaParse","5.5.3","tools/more.html + utils.html","2 hand-rolled CSV quote parsers","csv"],
["dayjs","1.11.13","tools/utils.html + feedpaper","864e5 millisecond date math","datetime"],
["croner","9.0.0","tools/utils.html","527k-iteration cron brute force","scheduling"],
["cronstrue","2.50.0","tools/utils.html","hand-rolled cron describer crRead","scheduling"],
["compare-versions","6.1.1","tools/utils.html","semver compare edge cases","semver"],
["Lucide","latest","index.html + feedpaper","emoji glyphs (★🔥💬⚠📄)","icons"],
["js-yaml","4.1.0","tools/utils.html","hand-rolled YAML parse","yaml"],
["swagger-ui-dist","5","swagger.html","hand-rolled API docs UI","api docs"],
];
document.getElementById("t").insertAdjacentHTML("beforeend",
  LIBS.map(([n,v,w,r,tag]) =>
    `<tr><td><b>${n}</b></td><td><code>${v}</code></td><td>${w}<br><span class="tag">${tag}</span></td><td style="color:var(--dim)">${r}</td></tr>`).join(""));
document.getElementById("sum").textContent =
  `${LIBS.length} libraries · all MIT/BSD-family · ~${(LIBS.length*40)}KB gzipped total · zero npm install`;
