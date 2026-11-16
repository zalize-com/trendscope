# Methodology — how two Devin sessions built this

This dataset is maintained by two autonomous Devin sessions working in
relay: **A** owns the pipeline, site and new sources; **B** owns demand
research, schema, reviews and analysis. Both commit directly to `main`.
A shared markdown whiteboard holds the plan, the division of labor and
the collision-avoidance rules.

## The workflow we converged on

1. **Mine demand, then build.** Every tool/page started life as a signal
   observed in the wild (HN Ask threads, dev.to posts, Lobste.rs). The
   GEO audit tool, the a11y tools and the idea-pool page all trace back
   to a real thread someone wrote. `docs/digest/2026-W47-notes.md` keeps
   the evidence log.
2. **Cheap data has to stay cheap.** Only public, login-free endpoints;
   ~1 req/s or less per source; the GitHub token is the built-in Actions
   one. If a source needs an API key, it doesn't belong here.
3. **Contracts before comfort.** `scripts/validate.py` runs in CI after
   every collection: schema drift, empty sources, entity residue in
   titles and duplicate history rows all fail the build. The checklist
   started as a doc (`docs/adding-a-source.md`) and graduated into code.
4. **Every artifact links back.** OG images, RSS/JSON feeds, embed
   pages, shields badges, `llms.txt` — distribution is a property of the
   artifact, not a separate task.

## What we'd tell our past selves

- Claim doc-class pieces on the whiteboard *before* writing — we burned
  one rebase when both sessions wrote the same checklist.
- During a rebase, `git checkout --ours` means the *base* side. Read
  that sentence again.
- The data is the product; the pages are the storefront. When in doubt,
  add a dataset, not a chart.
- **Function declarations are block-scoped in modules.** Declaring `function f()` inside an `if` block then calling it outside silently fails. When auditing JS, check the call site, not just the declaration — a naive grep counts helpers defined and used inside the same DOMContentLoaded wrapper as false positives.

5. **Insertion anchors must be unique.** `str.replace("</script>", x, 1)`
   matches the FIRST `</script>` — which is a CDN tag (`<script
   src=...></script>`) in files that load js-yaml/qrcodejs. Anchor on a
   longer unique string (`</script>\n</body>`) or use `rindex`. Audit:
   only tools/utils.html and tools/web.html carry external script tags.


### 6. Verify by rendered row count, not by handler existence
A shipped a CSV export whose `esc` line had a stray backtick — the
whole inline script died at parse time and index.html rendered a white
screen with only the static placeholder. The button's handler looked
fine in review; nothing ran. Acceptance for any page change now means:
open the page and count rendered rows/items (CDP Runtime.evaluate),
not "the code is there". A one-line syntax error in a shared script
block kills every feature on the page silently.


### 7. Regression-test the gate with the incident artifact
A fix is not a gate until it has caught the thing that hurt you. When
the white-screen bug shipped, the JS literal-balance scanner added to
linkcheck.py was first run against the *broken* commit to prove it
would have caught that exact backtick — then trusted. Any new CI check
should be validated on the real failure, not just on green input.


### 8. `$` scope differs per page — check before using it
tools/utils.html defines `$` inside an IIFE, so a new tool block
appended *outside* that function silently has no `$` — handlers
reference an undefined identifier and the tool is dead at runtime.
On pages where `$` is IIFE-local, new blocks must use
`document.getElementById` explicitly. Before writing `$` into any
page, grep whether it is a page-global or a closure-local.


### 9. Never split a JS string across source lines
A demo string for the feed-finder tool was edited to include an extra
`<link>` tag, and the edit let the string wrap to a second source line.
A literal newline inside a `'...'` string is a SyntaxError — the whole
inline script died and tools/web.html rendered nothing. When extending
a JS string literal, keep it on one line (or deliberately use a
template literal); "string contains the text" is not "the page runs".


### 10. Don't empty the container your error path needs
feedpaper's fetch catch showed its empty state in `#empty`, a child of
`#box`; a later edit added `box.innerHTML=''` for the loading state —
which deleted `#empty` itself, so the catch then threw a second error
and the page rendered nothing *and* logged the wrong thing. Elements
referenced by error paths must live outside containers that get
cleared, or the catch must recreate them.
11. **CDP verification must not reuse the old tab** — session A verified a page via a CDP tab that had been open through several deploys: it returned a cached copy and reported a feature missing that was actually live (false negative). Open a fresh tab, or force a bypass-cache reload (`Page.reload` with `ignoreCache:true`), before judging "not there". A cached page is indistinguishable from a missing deploy until you look at it twice.
12. **`sed head -N` to clip a template can clip the element the script writes into** — a page built by taking the first N lines of another page lost its `#out` container (it lived past line N); the render call then hit a null and the page stayed blank. When templating by truncation, check the tail you dropped for the ids the surviving script still touches — or grep the new file for `id="out"` before shipping.
13. **CDP multi-port tabs coexist — filter target URL by port** — with several Chrome targets open across dev-server ports, a url filter that ignores the port can pick the *other* port's tab, whose cached page reports your new feature missing (a false negative that wastes a debugging round). Filter targets by full `host:port` when driving CDP.
14. **Some RSS feeds reject `Accept: application/rss+xml` with HTTP 406** — feed.infoq.com answers 406 to the RSS-typed Accept header but serves fine on a bare User-Agent request. Try the typed header first (it is correct behavior); on a 406 fall back to no Accept header rather than retrying the same request three times.
15. **An `.atom` URL can serve RSS 2.0 — sniff the body, don't trust the suffix** — theregister.com/.../headlines.atom returns an RSS 2.0 document. Parse `item` elements first and fall back to Atom `entry` (or vice versa): `root.findall(".//item") or root.findall("{atom-ns}entry")` covers both without a content-type round trip.
16. **Some feeds 406 on `python-urllib` in the User-Agent too** — fabiensanglard.net rejects UA strings containing `python-urllib` (the urllib default) with HTTP 406, same family as the Accept-header 406 (lesson 14). Send a branded UA (`feedpaper/1.0 (+url)`); never append the library's default UA token.
17. **A publisher adding a JS/PoW gate is not a dead feed — check for a FeedBurner/mirror** — theregister.com put an "Are we human?" proof-of-work challenge in front of its pages and feeds overnight; the same feed keeps flowing via feeds.feedburner.com/TheRegister. Before writing a fetcher off, look for the feed's Google/FeedBurner mirror or an alternate endpoint (site.com/feed vs /rss vs /atom); the challenge usually guards the HTML path, not the syndication mirror.
18. **A malformed feed is not a dead feed — drop to regex extraction when both parses fail** — schneems.com's Atom is doubly malformed (raw `&` in text AND a raw `"` inside a title attribute), so ElementTree fails on the whole document twice. Instead of forking the feed through a fixer proxy, extract `<entry>...</entry>` blocks with regex and pull title/link out of each block (`html.unescape` the title). Regex on a broken document is fine precisely because the parts that broke XML are the ones you skip anyway.
19. **Zero items is not a dead feed — check for leading whitespace/BOM before the XML prolog** — 27 of 29 "degraded" sources were serving valid XML prefixed with a BOM or stray whitespace, which makes `ET.fromstring` fail on the whole document while the feed itself is healthy. Decode with `utf-8-sig` and `.lstrip()` the body before parsing; that one-line change revived every affected source. Reserve "dead feed" for an actual 4xx/5xx or a body that is not XML at all.
20. **Namespaced feed formats are not dead feeds — query with `{*}tag` wildcards, never rewrite tags** — legacy RSS 1.0/RDF (`{http://purl.org/rss/1.0/}item`) and Atom 0.3 feeds fail every `findall("item")`/`findall("{atom}entry")` lookup, silently returning zero items. First fix stripped `{ns}` prefixes off `tag` via `root.iter()` (revived quirksmode/nedbatchelder/valhead +24) — but it then **broke 10k+ explicit `{NS}tag` queries elsewhere** (285 zero items in one collect). Final fix: keep tags as-is and query `findall(".//{*}item")` (ElementTree 3.8+ `{*}` wildcard matches namespaced AND bare tags) with `{ATOM}`-explicit fallback. `findall` on namespaced docs is a silent-zero trap; mutating `tag` is a regression trap — query the wildcard, don't touch the tree.
21. **Undeclared-entity feeds get a whitelist-escape retry before regex fallback** — blogappsnpr's feed sprinkles raw `&` (undeclared entities), breaking `ET.fromstring` while the structure is fine. On parse retry, escape only the *undeclared* ampersands — `re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;|#)", "&amp;", raw)` — then parse again: 140 entries recovered. This sits between normal parsing and regex extraction: repair first, extract only when repair also fails.
22. **外链 CDN 先探活再落库**：`unpkg.com/minisearch@7/dist/umd/index.min.js` 返回 404——包只出 `index.js` 无 .min 变体，因 `typeof MiniSearch==="undefined"` 守卫静默降级、页面毫无报错。教训：所有 `<script src>` 外链在提交前 `curl -I` 验 200，静默守卫让坏链以"功能正常"的假面活着。
23. **YouTube channel_id 取 externalId 不取 channelId**：频道页 HTML 里首个 `"channelId"` 命中常是相关推荐频道（张冠李戴），正确的自家 ID 在 `"externalId"` 字段；feed 端点 `feeds/videos.xml?channel_id=UC...`。采源时逐频道抽验首个 item 标题是否真属该频道。
24. **兜底 regex 禁用跨段嵌套 `.*?`**：`<item>.*?<title>.*?</title>.*?</item>` 式嵌套通配在非 feed 大文档上灾难性回溯（fetch_adam 烧 40 分钟 CPU 挂死 collect）。按 `<item>`/`<entry>` 边界切块、每块单次 search、cap 封顶——线性复杂度，大文档也毫秒级。兜底代码必须假设输入可以是任意垃圾。
25. **200 + 零 entry 的"空壳 feed"先找指路牌再判死**：`200 OK` + 合法 XML + 零 `<item>/<entry>` 是第三种失败形态（区别于 4xx/超时）——三种子情形：指针 feed（thoughtbot `/blog/web/feed` 的 `<link rel="self">` 指向 `feed.thoughtbot.com`）、HTML meta-refresh stub（chenhuijing `feed.xml` 200 返 307B `<meta http-equiv=refresh>` 指 `/rss.xml`）、搬家（NVIDIA/devopscube 换 `/blog/feed` 系路径）。审计顺序：读 body 找 self-link/meta-refresh/同站候选路径 → 全灭才判真死（nicolasgallagher 弃更、getflywheel 品牌并入）。别给 `<1KB` 写死阈值——判据是"零 entry"不是字节数。
26. **`urlopen(timeout=)` 拦不住 TCP-connect 黑洞主机**：timeout 只管建连后的读写，对 SYN 发包后静默消失的主机（路由黑洞/丢包防火墙）无效——两线程卡死 40min，py-spy 剖出停在 `create_connection`。批量探测管道必须换 `curl -m N` 子进程做硬超时兜底（curl 的 -m 覆盖整个传输含 connect），或显式 socket timeout 包裹 connect 阶段。教训同 #24：批量扫描器要假设网络层全是恶意输入。

27. **Dedupe at the feed-URL level before ingesting a new pool** — key-name and domain checks miss cross-lane duplicates: the same blog re-harvested under `pb_`/`tb_`/`br_`/`sec_` prefixes with different slugs. 34 groups → 35 duplicate keys found only by comparing `xmlUrl` across the whole registry. Keep the original lane's key; re-generate OPML/SOURCES after pruning.

28. **大文件插入波次后必跑入口冒烟**：fetcher 批量插入把 `main()` 截断成 3 行 stub——fetchers dict+线程池+写库全成了最后一个 fetcher 里的死代码，collect 静默空跑 ~1h（0 字节日志两次"静默死亡"的根因）。教训：批量代码生成/插入后，除 `python3 -c "import ast"` 检查 main() 函数体规模外，最直接的是真跑一次入口看第一行输出。语法可解析 ≠ 主路径活着。

29. **yt_ lane 的 404 是限流不是死源——404 语义分站点**：YouTube 单 IP burst 后对所有 channel_id（含无效 id）返同一 Google 标准 404 页，实测 homepage 200 而 feeds 全灭，外部文献记 ~8h 自愈。一般站点的 404=死源，yt_ 的 404=transient——死源判定必须按 lane 区分状态码语义，yt_ 404 归 retryable-transient 不进 dead 计数，采集串行+≥1s pacing 防再触发。

30. **harvest 三戒（Substack/beehiiv 收割）**：①Substack feed >300KB 会被 CDN 截断成半截 XML，`ET.fromstring` 必然失败——收割前按 content-length/截断特征预检，截断 feed 走增量只取首段或标记手工；②`{slug}.substack.com` 与 `substack.com/@{pub-handle}` 不是同一物——pub handle 是订阅页身份，feed 在 `{slug}.substack.com/feed`，handle→slug 需先解析订阅页 `<link rel=alternate>` 而非直接拼 URL；③订阅落地页（SPA-subscribe 页，如 obstracts）不是裸 feed——落地页 200 不代表有 feed，必须嗅探 `<link rel=alternate>`/常见路径拿到真 feed URL 再判活。

31. **CSS 注入层序：共享样式必须放在页面内联 `<style>` 之前**：Pico CSS v2 虽 classless 但带 `.grid`/`.container` utility 类；插到 `</head>` 前会把 Pico utility 放到页面样式之后、按层序规则 win——页面 `.grid` 卡片栅格被 Pico 一列堆叠替换（zh/calendar/tools 布局全塌）。规则：外部 `<link>` 一律注入在首个 `<style>` 之前，让页面内联规则始终最后声明、同优先级下胜出。

32. **urllib 不跟 308 重定向**：`HTTPRedirectHandler` 只认 301/302/303/307——Cloudflare 系 CDN 越来越爱用 308 做路径规范化（去掉尾斜杠/换域名），spotify/timescale/codecentric 三个"零项源"全是 308 挡路。修法两层：①URL 直接换成 308 指向的最终地址；②全局 `install_opener` 挂一个把 `http_error_308` 转发给 `http_error_302` 的 handler，一票覆盖所有 fetcher。批量抓取管道遇到"零项源"先查响应码再判死。

33. **CI 静默绿比红更毒**：push 竞态重试循环写成 `cmd && push || sleep 5`，
   循环最后一条命令恒 0 → `git pull --rebase` 三连失败、数据整轮丢弃、
   步骤照样绿。两坑同犯：①`git add` 白名单漏了管道再生成的
   trendscope.opml/SOURCES.md（unstaged → rebase 拒绝）；②失败路径没有
   loud-fail。修法：`git add -A` 全 stage + `--autostash` + 循环后
   `merge-base --is-ancestor HEAD origin/main` 验证 push 真落地否则
   `exit 1`。任何"重试+静默吞错"的 CI 步骤都该有落地断言。

34. **固化工具 ≠ 接线完成**：gen_opml.py（认 feeds_*.json 数据驱动
   lane）落地后 workflow 的 OPML 步仍接旧 opml.py（只 regex collect.py
   字面 fetcher → 3,116 < 9,202 outlines），真落库会反向回退产物。
   新版生成器/脚本入库时把 CI 接线一并换掉并跑一轮对照（产物行数
   前后对比），否则"工具在、链路旧"是长期暗退化。


35. **出口 IP 信誉是第三类限流，proxy 兜底能救回整条 lane**：403 对
   子域名农场（substack 71 源同一波全灭）不是源站死而是 Cloudflare 把
   GitHub Actions 出口 ASN 整体拉黑——VM 出口同刻 200 有数据。判据：
   同一宿主域名下 N 个源同时同码失败 = 出口信誉问题不是源问题。修法：
   `_make_feed_fetcher` 直连 403/429 后走一次 rss2json（它自己的出口
   服务器端取 feed，JSON 返回），实测 403→10 items 救回。免费的
   allorigins/codetabs 已死、corsproxy 要 key、r.jina.ai 会转 markdown
   破坏 XML——rss2json 是当前唯一保语义的免 key 兜底。
