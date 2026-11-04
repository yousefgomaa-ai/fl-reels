# «تاريخ نادي مع بطولة»: Al Ahly and the CAF Champions League (2026-11-04), the museum design of history.py.
import sys
out = sys.argv[1]
YEARS = [1982, 1987, 2001, 2005, 2006, 2008, 2012, 2013, 2020, 2021, 2023, 2024]
# How many titles are lit in each scene (one per narration line).
LIT = [12, 0, 1, 2, 3, 4, 5, 6, 7, 8, 8, 9, 10, 11, 12, 12, 12, 12]
RM = 'logo/ahly.png'
def ph(k, sep=False, pos='center'): return f'<div class="frame" data-in><div class="pic kb{" sep" if sep else ""}" style="background-image:url(ph/{k}.jpg);background-position:{pos}"></div><div class="credit" id="cr-{k}"></div></div>'
def plate(year, title, sub=''): return f'<div class="plate" data-in><div class="yr">{year}</div><h2>{title}</h2>{f"<p>{sub}</p>" if sub else ""}</div>'
def sc(t): return f'<bdi dir="ltr">{t}</bdi>'
SC = [
  f'<div class="hero"><img src="{RM}" data-in><div class="n" data-in><b data-n="12" data-d="0.8">12</b></div><h1 data-in>الأهلي ودوري أبطال أفريقيا</h1><p data-in>القصة من البداية</p></div>',
  '<div class="two">' + ph('stadium', True) + plate('1982', 'البداية', 'أمام أسانتي كوتوكو الغاني') + '</div>',
  '<div class="two">' + ph('khatib', True, 'center 20%') + '<div class="plate" data-in><div class="yr">1982 • القاهرة</div><h2>الفوز على أسانتي كوتوكو ' + sc('3-0') + '</h2><p>أول لقب قاري</p><div class="sp"><span>هداف البطولة: الخطيب</span><b>6</b></div></div></div>',
  plate('1987', 'اللقب الثاني', 'على حساب الهلال السوداني'),
  '<div class="col"><div class="wait" data-in><span>ثم انتظار</span><b data-n="14">14</b><i>عامًا</i></div><p class="cap2" data-in>2001: على ماميلودي صن داونز</p></div>',
  plate('2005', 'بداية الجيل الذهبي', 'الفوز على النجم الساحلي ' + sc('3-0')),
  '<div class="two">' + ph('aboutrika', False, 'center 20%') + plate('2006 • صفاقس', 'هدف أبو تريكة', 'في الوقت بدل الضائع أمام الصفاقسي') + '</div>',
  plate('2008', 'اللقب السادس', 'على حساب كوتون سبور الكاميروني'),
  plate('2012 • رادس', 'الفوز على الترجي ' + sc('2-1'), 'اللقب السابع'),
  plate('2013 • القاهرة', 'الفوز على أورلاندو بايرتس ' + sc('2-0'), 'اللقب الثامن'),
  '<div class="two">' + ph('derby', False) + plate('2020 • القاهرة', 'نهائي القرن', 'أمام الزمالك') + '</div>',
  '<div class="two">' + ph('afsha', False, 'center 20%') + '<div class="plate" data-in><div class="yr">هدف أفشة</div><div class="clock">86</div><h2>الفوز على الزمالك ' + sc('2-1') + '</h2><p>اللقب التاسع</p></div></div>',
  plate('2021 • الدار البيضاء', 'الفوز على كايزر تشيفز ' + sc('3-0'), 'اللقب العاشر'),
  '<div class="two">' + ph('abdelmonem', False, 'center 20%') + plate('2023 • الدار البيضاء', 'الفوز على الوداد ' + sc('3-2'), 'في مجموع المباراتين • تعادل عبد المنعم') + '</div>',
  '<div class="two">' + ph('fans', False) + plate('2024 • القاهرة', 'الفوز على الترجي ' + sc('1-0'), 'اللقب الثاني عشر') + '</div>',
  '<div class="col"><h2 class="hd" data-in>سبعة عشر نهائيًا</h2><div class="cmp"><div class="cb" data-in><span>النهائيات</span><div class="bar"><i data-w="100" style="background:#8a7a5c"></i></div><b>17</b></div><div class="cb" data-in><span>الألقاب</span><div class="bar"><i data-w="70.6"></i></div><b>12</b></div></div></div>',
  '<div class="col"><h2 class="hd" data-in>أكثر الأندية تتويجًا</h2><div class="big" data-in><b data-n="12">12</b></div><p class="cap2" data-in>أكثر من أي نادٍ آخر في تاريخ البطولة</p></div>',
  f'<div class="hero"><img src="{RM}" data-in><h1 data-in>أي لقب هو الأجمل؟</h1><p data-in>اكتبه في التعليقات 👇 وتابع القناة</p></div>',
]
CSS = '''
*{margin:0;box-sizing:border-box}body{width:1920px;height:1080px;overflow:hidden;direction:rtl;font-family:'Noto Naskh Arabic',serif;color:#1d1a14;background:#efe5cf}
.paper{position:absolute;inset:0;background:radial-gradient(1400px 900px at 50% 40%,#f7f0de 0,#e9dcc0 70%,#d8c7a2 100%)}
.paper::after{content:'';position:absolute;inset:26px;border:2px solid #b8892b;outline:1px solid #b8892b;outline-offset:8px}
.brand{position:absolute;top:56px;left:80px;font:700 26px Amiri;letter-spacing:4px;color:#8a6a24}.chip{position:absolute;top:50px;right:80px;font:700 32px Amiri;color:#8a6a24}
.scene{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;padding:110px 120px 250px}.scene>*{position:relative}
.hero{text-align:center;display:flex;flex-direction:column;align-items:center;gap:6px}.hero img{width:170px}.hero .n b{font:700 260px Amiri;color:#b8892b;line-height:1}.hero h1{font:700 92px Amiri}.hero p{font:500 44px 'Noto Naskh Arabic';color:#6b5a3a}
.two{display:flex;align-items:center;gap:70px}.frame{width:640px;height:600px;background:#fff;padding:18px 18px 54px;box-shadow:0 18px 40px rgba(60,40,10,.35);transform:rotate(-1.5deg);position:relative}
.pic{width:100%;height:100%;background-size:cover;background-position:center}.pic.sep{filter:sepia(.75) contrast(1.05)}.frame{overflow:hidden}.credit{position:absolute;bottom:12px;left:18px;right:18px;font:500 17px 'Noto Naskh Arabic';color:#6b5a3a;direction:ltr;text-align:left}
.plate{max-width:900px;display:flex;flex-direction:column;gap:14px;align-items:flex-start}.plate .yr{font:700 52px Amiri;color:#b8892b;border-bottom:3px solid #b8892b;padding-bottom:4px}.plate h2{font:700 76px Amiri;line-height:1.25}.plate p{font:500 46px 'Noto Naskh Arabic';color:#4a3e28}
.col{display:flex;flex-direction:column;align-items:center;gap:30px}.hd{font:700 84px Amiri;text-align:center}.cap2{font:500 46px 'Noto Naskh Arabic';color:#6b5a3a}
.row5{display:flex;gap:30px}.y{width:230px;height:250px;background:#fbf6ea;border:2px solid #b8892b;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;box-shadow:0 10px 24px rgba(60,40,10,.2)}.y span{font-size:80px}.y b{font:700 64px Amiri;color:#8a6a24}
.sp{display:flex;align-items:center;gap:30px;font:700 52px Amiri}.sp b{font:700 90px Amiri;color:#b8892b}
.wait{display:flex;flex-direction:column;align-items:center}.wait span{font:500 52px 'Noto Naskh Arabic';color:#6b5a3a}.wait b{font:700 330px Amiri;color:#b8892b;line-height:1}.wait i{font:700 70px Amiri;font-style:normal}
.mini{background:#fbf6ea;border-right:10px solid #b8892b;padding:24px 40px;display:flex;flex-direction:column;box-shadow:0 10px 24px rgba(60,40,10,.2);min-width:700px}.mini b{font:700 80px Amiri;color:#b8892b}.mini span{font:500 44px 'Noto Naskh Arabic'}
.clock{font:700 160px Amiri;color:#b8892b;direction:ltr;line-height:1}.score{font:700 260px Amiri;color:#b8892b;direction:ltr;line-height:1}
.big b{font:700 220px Amiri;color:#b8892b;line-height:1}.chain{display:flex;gap:14px}.chain span{font:700 44px Amiri;background:#1d1a14;color:#efe5cf;padding:6px 26px}
.cmp{display:flex;flex-direction:column;gap:30px;width:1300px}.cb{display:grid;grid-template-columns:300px 1fr 140px;align-items:center;gap:30px;font:700 54px Amiri}.cb .bar{height:60px;background:rgba(184,137,43,.15);display:flex}.cb i{background:#b8892b;display:block;height:100%}.cb b{font:700 90px Amiri;color:#b8892b;text-align:center}
.strip{position:absolute;bottom:120px;left:120px;right:120px;display:flex;justify-content:space-between;border-top:3px solid #b8892b;padding-top:16px}
.strip div{display:flex;flex-direction:column;align-items:center;font:700 30px Amiri;color:#b6a684;transition:none}.strip div::before{content:'';width:22px;height:22px;border-radius:50%;background:#d8c7a2;border:3px solid #b6a684;margin-top:-30px;margin-bottom:8px}
.strip div.on{color:#8a6a24}.strip div.on::before{background:#b8892b;border-color:#8a6a24;box-shadow:0 0 18px #e0b44c}
#cap{position:absolute;bottom:40px;left:50%;transform:translateX(-50%);max-width:1560px;text-align:center;font:600 38px 'Noto Naskh Arabic';color:#efe5cf;background:#1d1a14;padding:8px 34px}
#progw{display:none}
'''
html = f'''<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><link rel="stylesheet" href="../fonts/fonts.css"><style>{CSS}</style></head>
<body><div class="paper"></div><div class="brand">FOOTBALL LEGENDS</div><div class="chip">تاريخ نادٍ مع بطولة</div>
{''.join(f'<div class="scene" style="opacity:0">{s}</div>' for s in SC)}
<div class="strip">{''.join(f'<div>{y}</div>' for y in YEARS)}</div><div id="cap"></div><div id="progw"><div id="prog"></div></div>
<script>const LIT={LIT};window.onScene=(i)=>{{document.querySelectorAll('.strip div').forEach((d,k)=>d.classList.toggle('on',k<LIT[i]));}};
fetch('ph/credits.json').then(r=>r.json()).then(c=>c.forEach(x=>{{const el=document.getElementById('cr-'+x.key);if(el)el.textContent='Photo: '+x.artist+', '+x.license+', Wikimedia Commons';}})).catch(()=>{{}});</script>
<script src="../engine.js"></script></body></html>'''
assert len(SC) == len(LIT) == 18
open(f'{out}/page.html', 'w').write(html); print('scenes', len(SC))
