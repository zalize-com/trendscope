# Zero-source triage — 2026-11-16 (167 persistent-empty, 3 consecutive rounds)

Method: extracted feed URLs → probed from VM egress (curl, UA browser) →
parsed last-post dates on 200s. Caveat: VM egress ≠ Actions egress; a 200
here can still be ASN-blocked there, so "alive" rows are *candidates* for
fallback lanes, not proof the pipeline sees them.

## ① Confirmed dead — safe to remove (5)
| key | feed | evidence |
|---|---|---|
| `br_akshay_sharma` | https://akshay326.com/rss.xml | 404 (VM) |
| `br_flow_im_ohr_the_burdens_of_being_upright` | https://blog.hamdorf.org/feed/ | 000 (VM) |
| `br_ux_designer_corner` | https://uglyduck.ca/feed/ | ERR (VM) |
| `br_web_archive_org` | https://web.archive.org/web/20181228051203/http://www.uliaea.ca/atom.xml | 302 (VM) |
| `sec_security_online` | https://securityonline.info/feed | 000 (VM) |

## ② Dormant — alive feed, no post >365d (28)
- `br_ace_high_george_kurdin` — last post 2023-04-09 (~43mo ago)
- `br_augmented_realist_noah_norman` — last post 2025-05-13 (~18mo ago)
- `br_brightball` — last post 2024-07-15 (~28mo ago)
- `br_climateer_steve` — last post 2024-09-15 (~26mo ago)
- `br_flutterby` — last post 2025-10-01 (~13mo ago)
- `br_fun_with_the_cloud_yehuda_cohen` — last post 2025-08-27 (~14mo ago)
- `br_getting_job_done_oriented_programming_al` — last post 2024-12-30 (~22mo ago)
- `br_have_you_played_adrian_hon` — last post 2024-03-26 (~32mo ago)
- `br_hitesh_writes_hitesh_yadav` — last post 2024-10-23 (~25mo ago)
- `br_into_the_details_peter_ehrlich` — last post 2025-11-10 (~12mo ago)
- `br_lejog_2023_daniel_janus` — last post 2023-06-30 (~41mo ago)
- `br_perspective_by_ankit_agarwal` — last post 2023-09-30 (~38mo ago)
- `br_the_healthy_dev_tom_white` — last post 2023-08-05 (~39mo ago)
- `br_wynken_de_worde_sarah_werner_s_blog_abou` — last post 2024-12-31 (~22mo ago)
- `nl_air_around_ai` — last post 2024-08-08 (~27mo ago)
- `nl_big_tech_digest` — last post 2025-08-15 (~15mo ago)
- `nl_consolesubstack` — last post 2024-02-11 (~33mo ago)
- `nl_embertimes` — last post 2024-07-15 (~28mo ago)
- `nl_hardcored` — last post 2023-06-06 (~41mo ago)
- `nl_programming_feedback_for_advanced_beginners` — last post 2020-08-12 (~76mo ago)
- `nl_reading` — last post 2025-03-30 (~19mo ago)
- `nl_saas_bites` — last post 2024-09-10 (~26mo ago)
- `nl_weeklyengineering` — last post 2024-08-11 (~27mo ago)
- `strategize` — last post 2024-11-04 (~24mo ago)
- `tb_tauqeer_ahmad` — last post 2022-08-25 (~51mo ago)
- `yt_coreyschafer` — last post 2007-02-06 (~240mo ago)
- `yt_simsig` — last post 2022-11-30 (~48mo ago)
- `yt_theodorepowell` — last post 2023-08-10 (~39mo ago)

## ③ Moved feeds — 301/302 to a live target; update URL to revive (14)
- `br_age_of_ai_zap` → `https://www.zappable.com/feed`
- `br_am_i_stronger_yet_steve` → `https://secondthoughts.ai/feed`
- `br_confessions_of_a_code_addict_abhinav_upa` → `https://blog.codingconfessions.com/feed`
- `br_jan_kremer` → `https://jankremer.de/index.xml`
- `br_niklas_weber` → `https://www.nklswbr.com/rss`
- `br_pseudofreedom_yi_zhang` → `https://www.pseudofreedom.com/feed`
- `br_shdon_com` → `https://www.shdon.com/rss/`
- `eb_thumbtack` → `https://blog.thumbtack.com/feed`
- `nl_alternainewsletter` → `https://newsletter.altern.ai/feed`
- `nl_devinterrupted` → `https://devinterrupted.substack.com/feed`
- `nl_generative` → `https://newsletter.generatecoll.com/feed`
- `nl_simply_explained` → `https://simplyexplainednewsletter.substack.com/feed`
- `nl_techtalksweekly` → `https://www.techtalksweekly.io/feed`
- `tidyfirst` → `https://newsletter.kentbeck.com/feed`

## ④ Alive + publishing (<90d since last post) — wave victims, keep (68)
68 sources verified live with recent posts — see tide/fallback lanes.
## ⑤ Rate-limited at probe time (429) — inconclusive, likely tide (20)
`rdartlang`, `rdataengineering`, `rdjango`, `rdocker`, `relm`, `rgolang`, `rjavascript`, `rkubernetes`, `rlaravel`, `rnetsec`, `rnextjs`, `ropensource`, `rpython`, `rreactjs`, `rredis`, `rrust`, `rscala`, `rsveltejs`, `rsysadmin`, `rwebdesign`
## ⑥ Stale (90–365d) — slow publishers, keep (22)
`br_aniruddha_substack`, `br_axel_s_substack_substack`, `br_blogxxxxxxx`, `br_brad_s_newsletter_substack`, `br_desert_of_my_real_life_media_technology_`, `br_engineering_at_scale_animesh_gaitonde`, `br_good_internet_ren_walter_substack`, `br_harmony_harshal_patil_substack`, `br_interessant3_duarte_substack`, `br_josh_baldwin`, `br_mccd_space`, `br_nehal_s_learnings_substack`, `br_of_scars_and_surprise_geoff_ayers_substa`, `br_posts_joisig_gone_awol`, `br_river_macleod`, `br_something_about_cats_ian_yanusko_substac`, `br_superb_owl_max_goodbird_substack`, `br_synystron_synlogica`, `br_the_incrementalist_jesal_gadhia_substack`, `br_theory_of_change_substack`, `nl_aifordevelopers`, `nl_womenonrails`
## ⑦ Unresolved (key↔fetcher name mismatch) (10)
`aboutwayfair`, `anyway`, `blog48`, `developerwordpress`, `mallonbacka`, `nicolasgallagher`, `rayepeng`, `seebug`, `trib`, `w3blog11`

## Actions
1. ~~**Revive 14 moved feeds**~~ — DONE 11/16: all 14 URL swaps landed (br_*×7 in-place, nl/eb/tidyfirst×7 via feeds_moved.json); collect run confirmed **18/18 revived** (18 = 14 swaps + 4 dormant overrides carrying new URLs).
2. **Prune 5 dead** (§①) — drops total_sources to ~9,208; coordinate the "9,200+" copy before removing. Held for post-launch batch.
3. ~~**Keep dormant 28**~~ — DONE 11/16: `dormant` 4th-element flag landed on all 28 (br 14 / yt 3 / nl 9 + tb_tauqeer + strategize via feeds_moved overrides); `data/dormant.json` generated, frontend grey-chip wiring by A.
4. The 68 active-but-zero (§④) confirm the "egress wave" diagnosis — they're the audience for the rss2json fallback already shipped.
5. §⑤ 20 probe-429 + §⑦ 10 unresolved — revisit next zerowatch pass; unresolved keys are fetcher-name mismatches (e.g. fetch_seebug→key "paper"), not missing sources.
