document.querySelectorAll('.copy').forEach(b=>b.onclick=()=>{
  navigator.clipboard.writeText(document.getElementById(b.dataset.t).innerText.replace(/\ncopy$/,''));
  b.textContent='copied';setTimeout(()=>b.textContent='copy',1500);
});
