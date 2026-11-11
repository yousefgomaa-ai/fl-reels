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
  // 1.35 times slower (was 1.6; owner, 2026-11-04: «مش عايزين الزائر يمل»): longer without dragging.
  const D0 = window.DATA || {}, S = D0.beats ? 1 : Number(D0.slow) || 1.35, T0 = window.TOTAL;
  if (S !== 1) {
    const d0 = window.draw;
    window.TOTAL = T0 * S + 2.5;
    if (typeof window.POSTER === 'number') window.POSTER = window.POSTER * S;
    window.draw = (t) => d0(Math.min(T0, t / S));
  }
  const b = document.createElement('div');
  b.style.cssText = 'position:absolute;top:0;left:0;height:10px;width:0;background:linear-gradient(90deg,var(--kc),#ffd21f);z-index:99;box-shadow:0 0 14px rgba(255,210,31,.7)';
  document.body.appendChild(b);
  // Keep them watching (owner, 2026-11-04: «خلي كل خطوة او حركة او معلومة تخلي المتفرج يكمل الريل للآخر»): a promise in the
  // first seconds of what waits at the end, and the whole frame drifting closer all along so nothing stands still.
  const TEASE = { 'en-recap': 'THE BIGGEST WIN IS LAST 👀', 'en-night': 'WAIT FOR THE BIGGEST ONE 👀', 'en-fixtures': 'THE BIG ONE IS LIT AT THE END 👀',
    'en-compare': 'THE VERDICT IS AT THE END 👀', 'en-boot': "WHO'S NUMBER ONE? WATCH TO THE END 👀", 'en-five': "EUROPE'S No.1 COMES LAST 👀",
    'en-history': "THIS SEASON'S LEADER AT THE END 👀", 'en-preview': 'FORM AND KICK-OFF COMING UP 👀', 'en-guess': 'THE ANSWER IS AT THE END 👀',
    'en-hilo': 'THE ANSWER IS AT THE END 👀', 'en-predict': 'MAKE YOUR PICK BEFORE THE END 👀', 'en-streak': 'WAIT FOR THE NUMBER 👀',
    'en-result': 'THE KEY NUMBERS ARE COMING 👀', 'en-table': "WAIT FOR WHO'S TOP 👀", 'en-form': "WHO'S ICE COLD? 👀", 'en-top5': 'NUMBER ONE COMES LAST 👀', 'en-weekend': 'THE BIGGEST WIN IS LAST 👀' };
  const tz = D0.tease === '' ? '' : D0.tease || TEASE[D0.kind] || '';
  let te = null;
  if (tz) {
    te = document.createElement('div'); te.textContent = tz;
    te.style.cssText = "position:absolute;left:50%;" + ({ 'en-compare': 'top:560px;', 'en-guess': 'top:200px;', 'en-hilo': 'top:200px;' }[D0.kind] || 'bottom:150px;') + "transform:translateX(-50%);white-space:nowrap;padding:12px 34px;border-radius:40px;background:#ffd21f;color:#040a2e;font:400 54px B,Arial;letter-spacing:2px;z-index:98;box-shadow:0 10px 30px rgba(0,0,0,.45);opacity:0";
    document.body.appendChild(te);
  }
  document.body.style.transformOrigin = '50% 40%';
  const d = window.draw;
  window.draw = (t) => {
    d(t); b.style.width = (100 * Math.min(1, t / window.TOTAL)) + '%';
    document.body.style.transform = `scale(${1 + .035 * Math.min(1, t / window.TOTAL)})`;
    if (te) { const a = Math.min(1, Math.max(0, (t - .3) / .3)) * (1 - Math.min(1, Math.max(0, (t - 3.6) / .4))); te.style.opacity = a; te.style.transform = `translateX(-50%) scale(${.9 + .1 * a + .02 * Math.sin(t * 6)})`; }
  };
}
// The competition's colours (en.css body.t-*), when the job names one.
if (window.DATA && window.DATA.theme) document.body.classList.add('t-' + String(window.DATA.theme).replace(/[^a-z0-9]/g, ''));
