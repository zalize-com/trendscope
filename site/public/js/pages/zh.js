const ZH = new Set("billwang1990github,blogcodingnow,blogdevtang,colobu,dbanotes,cnblogs,headsalon,onevcat,techmeituan,casatwy,daimajia,42jing,aigcweekly,akimio,bojieli,yuanchaofa,huhuhang,liamding,lyricquail,lyricim,liduos,fusheng,quaily,baoyu,lijigang,datawhale,huggingface,paperweekly,xinzhi,jiqizhixin,mlbeginner,qbitai,qbitaigzh,xgo5b632,xgo831fa,bilibilitech,bytetech,xiaomitech,dewutech,iqiyitech,baidusec,tencenttech,alimiddle,the5fire,luenci,michealwayne,maonie,kekxv,corvo,nl_hardcored,nl_pythoncat,laborinfocn,bestxtools".split(","));
const ZH_LABEL = {
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
  "techmeituan":"美团技术","casatwy":"casatwy","daimajia":"daimajia"
};
function esc(s){const d=document.createElement('div');d.textContent=s;return d.innerHTML;}
async function main(){
  let r=await fetch('data/latest-lite.json'); if(!r.ok) r=await fetch('data/latest.json'); const snap=await r.json();
  const have=[...ZH].filter(k=>snap.items[k]);
  document.getElementById('srcs').innerHTML=have.map(k=>
    `<a class="chip" href="zh-source.html?k=${k}" style="color:inherit">${esc(ZH_LABEL[k]||k)} <b>${snap.items[k].length}</b></a>`).join('');
  const queues=have.map(k=>snap.items[k].slice());
  const list=[]; while(list.length<60&&queues.some(q=>q.length))
    for(const q of queues) if(q.length) list.push(q.shift());
  const board=document.getElementById('board');
  board.innerHTML=list.map((it,i)=>`
    <div class="row"><span class="rank">${i+1}</span>
      <span><a href="${esc(it.url)}" target="_blank" rel="noopener">${esc(it.title)}</a>
        <span class="meta"><span class="src">${esc(ZH_LABEL[it.source]||it.source)}</span>${it.author?' · '+esc(it.author):''}</span></span>
    </div>`).join('');
}
main().catch(e=>{document.getElementById('board').innerHTML='<p class="muted">load failed: '+e+'</p>';});
