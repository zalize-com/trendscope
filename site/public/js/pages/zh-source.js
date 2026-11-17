const P=new URLSearchParams(location.search);
const k=P.get('k')||'';
const ZH_LABEL={
 "42jing":"42 章经","aigcweekly":"AIGC Weekly","akimio":"山与","bojieli":"Bojie Li",
 "yuanchaofa":"元超法","huhuhang":"胡涂说","liamding":"Liam Ding","lyricquail":"Lyric",
 "lyricim":"Lyric 编程","liduos":"李懂","fusheng":"傅盛","quaily":"Quaily",
 "baoyu":"宝玉","lijigang":"李继刚","datawhale":"Datawhale","huggingface":"Hugging Face 中文",
 "paperweekly":"PaperWeekly","xinzhi":"新智元","jiqizhixin":"机器之心","mlbeginner":"ML入门",
 "qbitai":"量子位","qbitaigzh":"量子位 QbitAI","nl_hardcored":"硬核小卒","nl_pythoncat":"Python潮流周刊","laborinfocn":"工劳小报","bestxtools":"好工具周刊","xgo5b632":"XGo","xgo831fa":"XGo 技术",
 "bilibilitech":"B站技术","bytetech":"字节跳动技术","xiaomitech":"小米技术","dewutech":"得物技术",
 "iqiyitech":"爱奇艺技术","baidusec":"百度安全","tencenttech":"腾讯技术","alimiddle":"阿里中间件",
 "the5fire":"the5fire","luenci":"论词","michealwayne":"Micheal Wayne","maonie":"猫呢","kekxv":"kekxv","corvo":"Corvo",
 "billwang1990github":"王垠","blogcodingnow":"酷壳","blogdevtang":"唐巧","colobu":"鸟窝",
 "dbanotes":"冯大辉","cnblogs":"博客园","headsalon":"Headsalon","onevcat":"OneV's Den",
 "techmeituan":"美团技术","casatwy":"casatwy","daimajia":"daimajia"};
function esc(s){const d=document.createElement('div');d.textContent=s;return d.innerHTML;}
async function main(){
 if(!k){document.getElementById('err').textContent='missing ?k= param';return;}
 document.title=(ZH_LABEL[k]||k)+' — trendscope 中文源';
 document.getElementById('t').textContent=ZH_LABEL[k]||k;
 document.getElementById('sub').innerHTML=`key: <code>${esc(k)}</code>`;
 let snap,srcs;
 try{
  let r=await fetch('data/latest-lite.json');if(!r.ok)r=await fetch('data/latest.json');snap=await r.json();
  srcs=await fetch('data/sources.json').then(r=>r.json()).catch(()=>({}));
 }catch(e){document.getElementById('err').textContent='数据加载失败';return;}
 const items=(snap.items||{})[k]||[];
 const s=srcs[k]||{};
 document.getElementById('meta').innerHTML=
  `<div><b>${items.length}</b><small>今日条目</small></div>`+
  (s.home?`<div><b style="font-size:14px"><a href="${esc(s.home)}">${esc(s.home.replace(/^https?:\/\//,''))}</a></b><small>主页</small></div>`:'')+
  `<div><b style="font-size:14px">${esc(s.type||'zh')}</b><small>lane</small></div>`;
 if(!items.length){document.getElementById('err').textContent='今日无条目——该源本轮未更新或 feed 暂不可达';return;}
 document.getElementById('list').innerHTML=items.map((it,i)=>
  `<li><span class="rk">${i+1}</span><a href="${esc(it.url)}" target="_blank" rel="noopener">${esc(it.title)}</a>`+
  `<span class="sc">${esc(scoreText(it))}</span></li>`).join('');
}
main();
