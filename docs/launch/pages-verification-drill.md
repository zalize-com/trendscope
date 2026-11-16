# Pages 上线 30 分钟公网验证清单

前置：GitHub Pages 已启用——trendscope 必须选 **Source: GitHub Actions**
（站点是 Astro 构建产物，deploy-from-branch 会直出 Markdown 源文件不工作）。
feedpaper 可选 deploy-from-branch（main/root，纯静态）。目标域：
`https://zalize-com.github.io/trendscope/`（或自定义域）。

## 0-5 min：存活与 HTTPS
- [ ] `curl -sI https://<pages-domain>/` → 200，无 mixed-content 警告
- [ ] 浏览器开首页：topbar、hero、All 板 rows 渲染（非白屏/占位符）
- [ ] DevTools Network：`latest-lite.json` 200（≈6MB）而非 404
- [ ] Console 无红色 error（CORS/charset/404）

## 5-15 min：核心 surface 抽查
- [ ] `/movers.html` — w7 表渲染、entered/exited 列非空
- [ ] `/topics.html` — 主题 chips + lane 混合 examples（非全 sec_）
- [ ] `/zh.html` — 中文 lane chips 2 列栅格、条目标题非乱码
- [ ] `/digest.html?f=2026-W47-narrative` — narrative 渲染
- [ ] `/search.html` — 输入关键词有结果
- [ ] `/tools/` — 工具页正常 + topbar
- [ ] `/about.html` — sources.json 懒渲染目录
- [ ] 亮色/暗色各抽查一页（prefers-color-scheme）

## 15-25 min：分发通道
- [ ] OG 卡：`https://cards-dev.twitter.com/validator` 或 metatags.io
        贴首页 URL → og:image 预览图渲染、title/description 正确
- [ ] `feed.xml` / `feed.json` 200 + XML/JSON 合法（reader 导入冒烟：
        Feedly/NetNewsWire 任选其一贴 URL）
- [ ] `trendscope.opml` 200 + 导入 Feedly 显示 9,200+ 源分组
- [ ] `llms.txt` 200 + 计数与当前 registry 一致
- [ ] `sitemap.xml` 200 + loc 全部是 Pages 域（无旧 preview 域残留）
- [ ] canonical/og:url 指向 Pages 域（查 index + 任一内页）

## 25-30 min：数据新鲜度
- [ ] `data/latest.json` generated_at 是最近一次 Actions collect
- [ ] daily archives 链接 `.json.gz` 可下载
- [ ] health 页无红条（degraded < 4% 容忍线）

## 事故预案
- 白屏 → Console 报错行号 → 大概率 JS 语法错（methodology 5/6/9 类）→
  revert 上一 commit + 本地 smoke 复跑
- latest-lite 404 → data/ 未随 Pages 发布 → 检查 Actions 发布步 include 路径
- OG 不渲染 → og:image 绝对 URL 仍指 preview 域 → 全局改 Pages 域
- mixed content → 页面有 http:// 资源 → grep 修复
