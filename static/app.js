const $ = s => document.querySelector(s);
const chat = $('#chat'), input = $('#input'), send = $('#send'), list = $('#list');
let sid = localStorage.getItem('sid');
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const api = (u, o) => fetch('/api' + u, o).then(async r => { if (!r.ok) throw new Error('요청 실패 (' + r.status + ')'); return r.json(); });
const post = (u, b) => api(u, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(b || {}) });

function speak(t) {  // 브라우저 내장 TTS로 일본어 발음 듣기
  speechSynthesis.cancel(); const u = new SpeechSynthesisUtterance(t); u.lang = 'ja-JP'; u.rate = .85; speechSynthesis.speak(u);
}
chat.addEventListener('click', e => { const b = e.target.closest('.spk'); if (b) speak(b.dataset.t); });

const item = x => `<div class="it"><div><div class="jp">${esc(x.jp)}</div><div class="sub">${esc(x.ko_pron)}</div><div>${esc(x.ko)}</div></div>
  <button class="spk" data-t="${esc(x.jp)}" title="발음 듣기">🔊</button></div>`;
const bot = d => { const t = d.translation || {}; return `<div class="row">
  <div class="tr"><div class="sub">일본어로 이렇게 말하세요</div><div class="jp">${esc(t.jp)}
  <button class="spk" data-t="${esc(t.jp)}">🔊</button></div><div class="sub">${esc(t.reading)}</div><div>🗣 ${esc(t.ko_pron)}</div></div>
  <h4>일본인이 이렇게 답할 수 있어요 (듣기 연습)</h4>${(d.answers || []).map(item).join('')}
  <h4>함께 쓰면 좋은 추천 문구</h4>${(d.suggestions || []).map(item).join('')}</div>`; };
const me = q => `<div class="row me"><div>${esc(q)}</div></div>`;
const bottom = () => chat.scrollTop = chat.scrollHeight;

async function loadList() {
  const ss = await api('/sessions');
  list.innerHTML = ss.map(s => `<li data-id="${s.id}" class="${s.id === sid ? 'on' : ''}"><span>${esc(s.title)}</span><i data-del="${s.id}">✕</i></li>`).join('');
  return ss;
}
async function open(id) {
  sid = id; localStorage.setItem('sid', id);
  const ms = await api('/sessions/' + id);
  chat.innerHTML = ms.length ? ms.map(m => m.role === 'user' ? me(m.content) : bot(m.content)).join('')
    : '<div class="row sub" id="empty" style="text-align:center;margin-top:20vh">여행 중 궁금한 걸 한국어로 물어보세요.<br>일본어 문장 · 발음 · 예상 답변을 알려드려요.</div>';
  bottom(); $('#side').classList.remove('open'); loadList();
}
async function newChat() { const s = await post('/sessions'); await open(s.id); input.focus(); }

async function submit() {
  const q = input.value.trim(); if (!q || send.disabled) return;
  input.value = ''; input.style.height = 'auto'; send.disabled = true;
  if (!sid) await newChat();
  $('#empty')?.remove();
  chat.insertAdjacentHTML('beforeend', me(q) + '<div class="row dots" id="ld">번역 중…</div>'); bottom();
  try { const d = await post(`/sessions/${sid}/chat`, { message: q }); $('#ld').outerHTML = bot(d); loadList(); }
  catch (e) { $('#ld').outerHTML = `<div class="row err">${esc(e.message)}</div>`; }
  send.disabled = false; bottom();
}
send.onclick = submit;
input.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); submit(); } });
input.addEventListener('input', () => { input.style.height = 'auto'; input.style.height = input.scrollHeight + 'px'; });
$('#newBtn').onclick = newChat; $('#menu').onclick = () => $('#side').classList.toggle('open');
list.addEventListener('click', async e => {
  if (e.target.dataset.del) { await api('/sessions/' + e.target.dataset.del, { method: 'DELETE' }); if (e.target.dataset.del === sid) { sid = null; localStorage.removeItem('sid'); } init(); return; }
  const li = e.target.closest('li'); if (li) open(li.dataset.id);
});
async function init() {
  const ss = await loadList();
  const id = ss.find(s => s.id === sid)?.id || ss[0]?.id;
  id ? open(id) : newChat();
}
init();
