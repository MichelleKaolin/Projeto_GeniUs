let isDark = true;
let currentView = 'overview';
let quizData = [
  {q:"Qual a complexidade de tempo do QuickSort no pior caso?",opts:["O(n log n)","O(n²)","O(n)","O(log n)"],ans:1},
  {q:"Qual estrutura de dados usa LIFO (Last In First Out)?",opts:["Fila","Pilha","Árvore","Grafo"],ans:1},
  {q:"O que é um algoritmo de busca binária?",opts:["Busca em lista não ordenada","Busca por força bruta","Divide e conquista em lista ordenada","Busca em grafos"],ans:2},
  {q:"Qual o resultado de 2^10?",opts:["512","1024","2048","256"],ans:1},
  {q:"O que é recursão?",opts:["Repetição com for","Função que chama a si mesma","Algoritmo de ordenação","Tipo de variável"],ans:1}
];
let qIndex = 0;
let answered = false;
 
function showPage(id){document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));document.getElementById(id).classList.add('active');window.scrollTo(0,0);}
function showAuth(tab){showPage('auth');switchTab(tab);}
function switchTab(tab){
  document.getElementById('form-login').style.display=tab==='login'?'block':'none';
  document.getElementById('form-signup').style.display=tab==='signup'?'block':'none';
  document.getElementById('tab-login').classList.toggle('active',tab==='login');
  document.getElementById('tab-signup').classList.toggle('active',tab==='signup');
}
function doLogin(){showPage('dashboard');showToast('🎉 Bem-vindo de volta, Alex!');}
function doSignup(){showPage('dashboard');showToast('🚀 Conta criada! Bem-vindo ao GeniUs!');}
function toggleTheme(){isDark=!isDark;document.body.classList.toggle('light',!isDark);document.querySelectorAll('.btn-theme').forEach(b=>b.textContent=isDark?'🌙':'☀️');}
function showView(v){
  document.querySelectorAll('.dash-view').forEach(d=>d.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
  document.getElementById('view-'+v).classList.add('active');
  currentView=v;
  if(v==='desafio'){qIndex=0;loadQ();}
  if(window.innerWidth<=768)document.getElementById('sidebar').classList.remove('open');
}
function toggleSidebar(){document.getElementById('sidebar').classList.toggle('open');}
function toggleProfile(){document.getElementById('profileMenu').classList.toggle('open');}
function toggleDisc(el){el.classList.toggle('selected');showToast(el.classList.contains('selected')?'✅ Disciplina adicionada':'❌ Disciplina removida');}
function loadQ(){
  if(qIndex>=quizData.length){showToast('🎉 Desafio concluído! +200 XP');showView('overview');return;}
  answered=false;
  const d=quizData[qIndex];
  document.getElementById('qNum').textContent=qIndex+1;
  document.getElementById('qProgress').style.width=((qIndex+1)/quizData.length*100)+'%';
  document.getElementById('quizQuestion').textContent=d.q;
  const opts=document.getElementById('quizOptions');
  opts.innerHTML='';
  d.opts.forEach((o,i)=>{const b=document.createElement('button');b.className='quiz-option';b.textContent=o;b.onclick=()=>answerQ(i);opts.appendChild(b);});
}
function answerQ(i){
  if(answered)return;
  answered=true;
  const d=quizData[qIndex];
  const btns=document.querySelectorAll('.quiz-option');
  btns[i].classList.add(i===d.ans?'correct':'wrong');
  if(i!==d.ans)btns[d.ans].classList.add('correct');
  if(i===d.ans)showToast('✅ Correto! +40 XP');
  else showToast('❌ Errou! A resposta era: '+d.opts[d.ans]);
  setTimeout(()=>{qIndex++;loadQ();},1500);
}
function showToast(msg){
  const t=document.createElement('div');t.className='toast';t.textContent=msg;
  document.getElementById('toasts').appendChild(t);
  setTimeout(()=>t.remove(),3000);
}
// Timer
function updateTimer(){
  const now=new Date();const end=new Date();end.setHours(23,59,59);
  const diff=end-now;const h=Math.floor(diff/3600000);const m=Math.floor((diff%3600000)/60000);const s=Math.floor((diff%60000)/1000);
  const el=document.getElementById('timerVal');if(el)el.textContent=`${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
}
setInterval(updateTimer,1000);updateTimer();
document.addEventListener('click',e=>{if(!e.target.closest('.avatar')&&!e.target.closest('.profile-menu'))document.getElementById('profileMenu').classList.remove('open');});