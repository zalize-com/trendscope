# trendscope

> 开发者注意力数据集 —— 开发者每天在读什么、在造什么、在下什么，
> 每日快照，开放数据（CC0），由 GitHub Actions 自动更新。

[English README →](README.md)

**在线仪表盘:** `https://zalize-com.github.io/trendscope/`
**最新数据:** [`data/latest.json`](data/latest.json)

## 这是什么

每天两次，跨 **1390 个数据源**抓一份"开发者注意力"快照：Hacker News、
Show HN、Ask HN、GitHub Trending、Lobste.rs、Dev.to、Product Hunt、
Techmeme、Slashdot、Ars Technica、The Verge、arXiv、npm、PyPI、
crates.io、Lemmy (programming.dev)、Krebs on Security、Changelog News、
freeCodeCamp News、Echo JS、InfoQ、The Register。

每条记录带 `url` + `captured_at` 溯源字段和各源原生分数
（点数 / star / 反应数 / 下载量）——请在同一源内比较，不要跨源比。

## 数据文件

| 文件 | 说明 |
|---|---|
| `data/latest.json` | 最新完整快照（供下游消费的稳定 URL） |
| `data/latest.csv` | 同上，CSV 版 |
| `data/daily/YYYY-MM-DD.json` / `.csv` | 当日完整快照 |
| `data/history.csv` | 追加式全量历史 —— 可做趋势速度分析 |
| `data/index.json` | 全部快照日期索引 |
| `feed.xml` | 每次快照 + 每周摘要的 RSS |
| `docs/api/` | 23 条 JSON/CSV/SVG/RSS API 线（见 `docs/api.md`） |

## 50 个静态页面

榜单、速度榜、连日霸榜、跨源扩散、域名榜、作者榜、主题热度、
讨论热度、HN 经典史、求职榜、工作节奏、周报、突围雷达、关键词盯梢、
流星项、嵌入画廊、73 件浏览器小工具……全部零构建纯静态。

## 嵌入你的网站

iframe 22 种模式（`embed.html?mode=top|new|risers|watch&kw=…` 等），
或免 iframe 的 Web Component：

```html
<script src="https://zalize-com.github.io/trendscope/docs/api/widget.js" defer></script>
<trend-scope mode="top" n="5"></trend-scope>
```

README 徽章：`docs/api/sparkline.svg`（全站）+ `sparkline/<源>.svg`（20 源各一条）。

## 许可

数据 CC0，代码 MIT。随便用，引用一句来源最好。
