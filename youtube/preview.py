# «قبل القمة»: the split design (Liverpool's dark crimson on the right, Arsenal's white and red on the left).
import sys
out = sys.argv[1]
LIV, ARS = 'logo/364.png', 'logo/359.png'
def duel(label, l, a, mx):
    return f'''<div class="du" data-in><div class="v l">{l}</div><div class="bars"><div class="bl"><i data-w="{100*l/mx}"></i></div><span>{label}</span><div class="ba"><i data-w="{100*a/mx}"></i></div></div><div class="v a">{a}</div></div>'''
def side(logo, title, rows, cls):
    return f'<div class="card {cls}" data-in><img src="{logo}"><h2>{title}</h2>' + ''.join(f'<div class="r"><span>{k}</span><b>{v}</b></div>' for k, v in rows) + '</div>'
def form(logo, items, cls):
    return f'<div class="card {cls}" data-in><img src="{logo}"><h2>آخر مباراتين</h2>' + ''.join(f'<div class="fm"><em class="w">ف</em><span>{t}</span><b>{s}</b></div>' for t, s in items) + '</div>'
SC = [
  f'<div class="kick" data-in>قمة الجولة 9 • الدوري الإنجليزي</div><div class="vs" data-in><img src="{LIV}"><b>×</b><img src="{ARS}"></div><div class="ttl" data-in>ليفربول × آرسنال</div><div class="pill" data-in>كل ما تحتاج معرفته</div>',
  '<div class="ph kb" style="background-image:url(ph/anfield.jpg)"></div><div class="shade"></div><div class="info" data-in><div><span>اليوم</span><b>الأحد</b></div><div><span>الموعد</span><b>6:30 م</b><i>بتوقيت القاهرة</i></div><div><span>الملعب</span><b>أنفيلد</b></div></div>',
  f'<div class="champ" data-in><img src="{ARS}"><div><span>بطل الموسم الماضي</span><b>2025-26</b><i>بعد انتظار 22 عامًا</i></div></div>',
  side(ARS, 'آرسنال', [('المركز', '2'), ('النقاط', '21'), ('فوز', '7'), ('هزيمة', '1')], 'ars') + '<div class="note" data-in>متساوٍ في النقاط مع المتصدر مانشستر سيتي</div>',
  side(LIV, 'ليفربول', [('المركز', '4'), ('النقاط', '15'), ('فوز • تعادل • هزيمة', '4 • 3 • 1'), ('الفارق عن آرسنال', '6 نقاط')], 'liv'),
  form(LIV, [('2-1 على برينتفورد', 'خارج أرضه'), ('2-0 على برايتون', 'في أنفيلد')], 'liv'),
  form(ARS, [('1-0 على نوتنغهام فورست', 'خارج أرضه'), ('2-0 على إيفرتون', 'على أرضه')], 'ars') + '<div class="note" data-in>شباك نظيفة في المباراتين</div>',
  f'<div class="huge" data-in><img src="{ARS}"><b data-n="5">5</b><span>أهداف فقط في 8 مباريات<br>أقوى دفاع في الدوري</span></div>',
  '<div class="kick" data-in>وجهًا لوجه هذا الموسم</div><div class="duels">' + duel('سجّل', 11, 13, 15) + duel('استقبل', 8, 5, 15) + duel('النقاط', 15, 21, 24) + '</div>',
  '<div class="coaches"><div class="co" data-in><div class="cph" style="background-image:url(ph/iraola.jpg)"></div><b>أندوني إيراولا</b><span>ليفربول • موسمه الأول</span></div><div class="cvs" data-in>×</div><div class="co" data-in><div class="cph" style="background-image:url(ph/arteta.jpg)"></div><b>ميكيل أرتيتا</b><span>آرسنال • صانع اللقب</span></div></div>',
  '<div class="kick" data-in>آخر مواجهتين</div><div class="h2h"><div class="m" data-in><span>أنفيلد • أغسطس 2025</span><b class="sl"><span>ليفربول</span><span>1</span><span>-</span><span>0</span><span>آرسنال</span></b><i>ركلة حرة من سوبوسلاي</i></div><div class="m" data-in><span>الإمارات • يناير 2026</span><b class="sl"><span>آرسنال</span><span>0</span><span>-</span><span>0</span><span>ليفربول</span></b><i>تعادل سلبي</i></div></div>',
  f'<div class="huge" data-in><img src="{ARS}"><b data-n="0">0</b><span>أهداف لآرسنال<br>في آخر مباراتين أمام ليفربول</span></div>',
  f'<div class="kick" data-in>الغيابات • ليفربول</div><div class="news"><div class="nw ok" data-in><img src="{LIV}"><span>سوبوسلاي</span><b>عودة محتملة</b></div><div class="nw no" data-in><img src="{LIV}"><span>فريمبونغ</span><b>غائب حتى ما بعد التوقف الدولي</b></div></div>',
  f'<div class="kick" data-in>الغيابات • آرسنال</div><div class="news"><div class="nw ok" data-in><img src="{ARS}"><span>ديكلان رايس</span><b>عاد إلى التدريبات</b></div><div class="nw ok" data-in><img src="{ARS}"><span>كالافيوري</span><b>عاد إلى التدريبات</b></div></div>',
  '<div class="read" data-in><span>قراءتنا بالأرقام</span><b>أقوى دفاع</b><i>×</i><b>ليفربول في أنفيلد</b><em>مباراة قد تُحسم بهدف واحد</em></div>',
  f'<div class="kick" data-in>ماذا تعني النتيجة؟</div><div class="sc2"><div class="o ars" data-in><img src="{ARS}"><span>فوز آرسنال</span><b>الفارق 9 نقاط</b></div><div class="o liv" data-in><img src="{LIV}"><span>فوز ليفربول</span><b>الفارق 3 نقاط</b></div></div>',
  f'<div class="vs" data-in><img src="{LIV}"><b>?</b><img src="{ARS}"></div><div class="ttl" data-in>ما توقعك للنتيجة؟</div><div class="pill" data-in>اكتبه في التعليقات 👇 وتابع القناة</div>',
]
CSS = '''
*{margin:0;box-sizing:border-box}body{width:1920px;height:1080px;overflow:hidden;font-family:Cairo,sans-serif;direction:rtl;background:#f4f1ee}
.halfR{position:absolute;inset:0;background:linear-gradient(135deg,#5c0011,#a3001c 60%,#c8102e);clip-path:polygon(52% 0,100% 0,100% 100%,40% 100%)}
.halfL{position:absolute;inset:0;background:#f6f3ef;clip-path:polygon(0 0,52% 0,40% 100%,0 100%)}
.halfL::after{content:'';position:absolute;inset:0;background:repeating-linear-gradient(90deg,rgba(239,1,7,.05) 0 40px,transparent 40px 80px)}
.seam{position:absolute;inset:0;background:linear-gradient(90deg,transparent 0,transparent 100%);clip-path:polygon(51.4% 0,52.6% 0,40.6% 100%,39.4% 100%);background:#d4af37}
.brand{position:absolute;top:40px;left:64px;font:700 26px 'Reem Kufi';letter-spacing:5px;color:#a3001c}.chip{position:absolute;top:34px;right:64px;font:900 28px Cairo;color:#fff;border:2px solid #d4af37;padding:6px 26px;border-radius:8px;background:rgba(0,0,0,.25)}
.scene{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:30px;padding:120px 110px 170px}.scene>*{position:relative}
.ph{position:absolute;inset:0;background-size:cover;background-position:center}.shade{position:absolute;inset:0;background:linear-gradient(0deg,rgba(20,0,5,.92),rgba(20,0,5,.45))}
.kick{font:700 44px 'Reem Kufi';color:#fff;background:#111;padding:8px 34px;border-radius:6px;border-bottom:5px solid #d4af37}
.vs{display:flex;align-items:center;gap:90px}.vs img{width:330px;height:330px;object-fit:contain;background:#fff;border-radius:50%;padding:38px;box-shadow:0 18px 40px rgba(0,0,0,.35)}.vs b{font:700 150px 'Reem Kufi';color:#d4af37}
.ttl{font:700 104px 'Reem Kufi';color:#111;background:#fff;padding:0 50px;border-radius:10px;box-shadow:0 14px 40px rgba(0,0,0,.25)}.pill{font:900 40px Cairo;color:#fff;background:#111;padding:10px 40px;border-radius:50px}
.info{display:flex;gap:40px}.info div{background:rgba(255,255,255,.95);border-top:8px solid #d4af37;width:430px;padding:30px;text-align:center;display:flex;flex-direction:column;gap:4px;border-radius:8px}.info span{font:600 34px Cairo;color:#777}.info b{font:700 84px 'Reem Kufi';color:#a3001c}.info i{font:600 28px Cairo;color:#555;font-style:normal}
.champ{display:flex;align-items:center;gap:60px;background:#fff;padding:50px 80px;border-radius:14px;box-shadow:0 20px 60px rgba(0,0,0,.3);border-right:14px solid #ef0107}.champ img{width:280px}.champ div{display:flex;flex-direction:column}.champ span{font:900 46px Cairo;color:#555}.champ b{font:700 150px 'Reem Kufi';color:#ef0107;line-height:1.1;direction:ltr}.champ i{font:900 42px Cairo;color:#111;font-style:normal}
.card{width:900px;background:#fff;border-radius:14px;padding:34px 50px;box-shadow:0 20px 60px rgba(0,0,0,.3);display:flex;flex-direction:column;gap:12px;align-items:stretch}.card img{width:150px;height:150px;object-fit:contain;align-self:center}.card h2{font:700 66px 'Reem Kufi';text-align:center}
.card.liv{border-top:12px solid #c8102e}.card.liv h2{color:#a3001c}.card.ars{border-top:12px solid #ef0107}.card.ars h2{color:#ef0107}
.r{display:flex;justify-content:space-between;font:900 40px Cairo;border-bottom:2px solid #eee;padding:8px 0}.r b{font:700 52px 'Reem Kufi';color:#111}
.fm{display:flex;align-items:center;gap:24px;font:900 44px Cairo;border-bottom:2px solid #eee;padding:10px 0}.fm em{font-style:normal;background:#1aa260;color:#fff;width:64px;height:64px;border-radius:10px;display:flex;align-items:center;justify-content:center}.fm b{margin-right:auto;font:600 32px Cairo;color:#777}
.note{font:900 40px Cairo;color:#fff;background:#111;padding:12px 36px;border-radius:8px}
.huge{display:flex;align-items:center;gap:60px;background:#fff;padding:40px 90px;border-radius:14px;box-shadow:0 20px 60px rgba(0,0,0,.3)}.huge img{width:220px}.huge b{font:700 300px 'Reem Kufi';color:#ef0107;line-height:1}.huge span{font:900 54px Cairo;color:#111;line-height:1.4}
.duels{display:flex;flex-direction:column;gap:28px;width:1500px;background:rgba(255,255,255,.96);padding:40px 60px;border-radius:14px;box-shadow:0 20px 60px rgba(0,0,0,.3)}
.du{display:grid;grid-template-columns:140px 1fr 140px;align-items:center;gap:24px}.du .v{font:700 76px 'Reem Kufi';text-align:center}.du .l{color:#a3001c}.du .a{color:#ef0107}
.bars{display:grid;grid-template-columns:1fr 220px 1fr;align-items:center}.bars span{text-align:center;font:900 40px Cairo}.bl,.ba{height:34px;background:#eee;border-radius:6px;display:flex}.bl{justify-content:flex-start}.ba{justify-content:flex-end}.bl i{background:#a3001c;border-radius:6px}.ba i{background:#ef0107;border-radius:6px}
.coaches{display:flex;align-items:center;gap:70px}.co{width:560px;background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.3);text-align:center;padding-bottom:24px}.cph{height:520px;background-size:cover;background-position:center 20%}.co b{display:block;font:700 56px 'Reem Kufi';margin-top:16px}.co span{font:900 34px Cairo;color:#666}.cvs{font:700 140px 'Reem Kufi';color:#d4af37}
.h2h{display:flex;gap:50px}.m{width:720px;background:#fff;border-radius:14px;padding:40px;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,.3);display:flex;flex-direction:column;gap:10px;border-bottom:10px solid #d4af37}.m span{font:900 34px Cairo;color:#777}.m b{font:700 64px 'Reem Kufi'}.sl{display:flex;justify-content:center;gap:16px}.m i{font:900 36px Cairo;font-style:normal;color:#a3001c}
.news{display:flex;flex-direction:column;gap:26px;width:1300px}.nw{display:grid;grid-template-columns:110px 1fr auto;align-items:center;gap:30px;background:#fff;border-radius:12px;padding:24px 40px;box-shadow:0 14px 40px rgba(0,0,0,.25);font:900 52px Cairo}.nw img{width:96px}.nw b{font:900 38px Cairo;padding:8px 24px;border-radius:8px}.nw.ok b{background:#e3f6ea;color:#127a43}.nw.no b{background:#fde4e4;color:#b3001b}
.read{display:flex;flex-direction:column;align-items:center;gap:10px;background:#111;color:#fff;padding:50px 100px;border-radius:14px;border:4px solid #d4af37}.read span{font:900 40px Cairo;color:#d4af37}.read b{font:700 90px 'Reem Kufi'}.read i{font:700 70px 'Reem Kufi';color:#d4af37;font-style:normal}.read em{font:900 46px Cairo;font-style:normal;margin-top:16px;background:#a3001c;padding:8px 30px;border-radius:8px}
.sc2{display:flex;gap:60px}.o{width:640px;background:#fff;border-radius:14px;padding:44px;text-align:center;display:flex;flex-direction:column;gap:12px;align-items:center;box-shadow:0 20px 60px rgba(0,0,0,.3)}.o img{width:170px}.o span{font:900 46px Cairo;color:#555}.o b{font:700 80px 'Reem Kufi'}.o.ars b{color:#ef0107}.o.liv b{color:#a3001c}
#cap{position:absolute;bottom:52px;left:50%;transform:translateX(-50%);max-width:1520px;text-align:center;font:900 40px Cairo;color:#fff;background:#111;padding:12px 34px;border-radius:6px;border-bottom:5px solid #d4af37}
#progw{position:absolute;bottom:0;left:0;right:0;height:8px;background:#ddd}#prog{height:100%;background:#d4af37;width:0;margin-right:auto}
'''
html = f'''<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><link rel="stylesheet" href="../fonts/fonts.css"><style>{CSS}</style></head>
<body><div class="halfL"></div><div class="halfR"></div><div class="seam"></div><div class="brand">FOOTBALL LEGENDS</div><div class="chip">قبل القمة</div>
{''.join(f'<div class="scene" style="opacity:0">{s}</div>' for s in SC)}<div id="cap"></div><div id="progw"><div id="prog"></div></div><script src="../engine.js"></script></body></html>'''
open(f'{out}/page.html', 'w').write(html); print('scenes', len(SC))
