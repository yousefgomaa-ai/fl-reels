// Long YouTube videos (owner, 2026-10-30): one scene per narration line, drawn at time t by draw(t).
// Children with data-in fade in one after another, data-n counts up, data-w grows a bar, .kb slowly zooms a photo.
const clamp = (x) => Math.max(0, Math.min(1, x)), ease = (p) => 1 - Math.pow(1 - p, 3);
let TL = { starts: [0], end: 10, caps: [] };
function setTimeline(tl) { TL = tl; }
function draw(t) {
  const S = TL.starts, scenes = [...document.querySelectorAll('.scene')];
  let i = S.length - 1; while (i > 0 && t < S[i]) i--;
  const a = S[i], b = i + 1 < S.length ? S[i + 1] : TL.end, local = t - a;
  scenes.forEach((el, k) => { el.style.opacity = k === i ? clamp(local / 0.45) : (k === i - 1 ? 1 - clamp(local / 0.45) : 0); el.style.visibility = (k === i || k === i - 1) ? 'visible' : 'hidden'; });
  const cur = scenes[i]; if (!cur) return;
  cur.querySelectorAll('[data-in]').forEach((el, j) => {
    const d = el.dataset.in === '' ? 0.25 + j * 0.3 : parseFloat(el.dataset.in), p = ease(clamp((local - d) / 0.55));
    el.style.opacity = p; el.style.transform = `translate${el.dataset.dir || 'Y'}(${(1 - p) * (el.dataset.dist || 36)}px)`;
  });
  cur.querySelectorAll('[data-n]').forEach((el) => {
    const n = parseFloat(el.dataset.n), p = ease(clamp((local - parseFloat(el.dataset.d || 0.4)) / 1.3));
    el.textContent = (el.dataset.pre || '') + Math.round(n * p) + (el.dataset.post || '');
  });
  cur.querySelectorAll('[data-w]').forEach((el) => { const p = ease(clamp((local - parseFloat(el.dataset.d || 0.5)) / 1.2)); el.style.width = (parseFloat(el.dataset.w) * p) + '%'; });
  cur.querySelectorAll('.kb').forEach((el) => { el.style.transform = `scale(${1.04 + 0.08 * clamp(local / Math.max(1, b - a))})`; });
  if (window.onScene) window.onScene(i, local);
  const prog = document.getElementById('prog'); if (prog) prog.style.width = (100 * t / TL.end) + '%';
  const cap = document.getElementById('cap'), c = TL.caps.find((x) => t >= x[0] && t < x[1]);
  if (cap) { cap.textContent = c ? c[2] : ''; cap.style.opacity = c ? 1 : 0; }
}
