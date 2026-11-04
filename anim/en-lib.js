// FB Legends pages: a star's cut-out (cut/<slug>.png) when it exists, else his Commons photo.
function starImg(el, slug, photo, cls, style) {
  return new Promise((res) => {
    const im = new Image(); im.className = cls || 'cut'; if (style) im.style.cssText = style;
    const fall = () => { if (photo && im.src.indexOf(photo) < 0) { im.className = 'ph'; im.src = photo; } else { im.remove(); res(null); } };
    im.onload = () => res(im); im.onerror = fall;
    el.appendChild(im); im.src = slug ? `cut/${slug}.webp` : (photo || ''); if (!slug && !photo) { im.remove(); res(null); }
  });
}
const cnt = (to, k) => (String(to).includes('.') ? (Number(to) * k).toFixed(2) : String(Math.round(Number(to) * k)));
// A thin bar along the top that fills as the reel plays (owner, 2026-11-03: «الساسبينس ... عشان المتفرج يكمله للآخر»):
// called once a page has set window.draw and window.TOTAL.
function progBar() {
  // Longer reels (owner, 2026-11-04: «عايزين الريلز تكون اطول شويه»): every page plays 1.6 times slower, calmer, and holds
  // its last frame (the question) 2.5 seconds more; about 18 seconds instead of 10. Not a story timed to its voice
  // (DATA.beats), nor a page that asks otherwise (DATA.slow).
  const D0 = window.DATA || {}, S = D0.beats ? 1 : Number(D0.slow) || 1.6, T0 = window.TOTAL;
  if (S !== 1) {
    const d0 = window.draw;
    window.TOTAL = T0 * S + 2.5;
    if (typeof window.POSTER === 'number') window.POSTER = window.POSTER * S;
    window.draw = (t) => d0(Math.min(T0, t / S));
  }
  const b = document.createElement('div');
  b.style.cssText = 'position:absolute;top:0;left:0;height:10px;width:0;background:linear-gradient(90deg,#46d7ff,#ffd21f);z-index:99;box-shadow:0 0 14px rgba(255,210,31,.7)';
  document.body.appendChild(b);
  const d = window.draw;
  window.draw = (t) => { d(t); b.style.width = (100 * Math.min(1, t / window.TOTAL)) + '%'; };
}
// The competition's colours (en.css body.t-*), when the job names one.
if (window.DATA && window.DATA.theme) document.body.classList.add('t-' + String(window.DATA.theme).replace(/[^a-z0-9]/g, ''));
