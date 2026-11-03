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
