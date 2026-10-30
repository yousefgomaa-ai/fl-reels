# «ملخص الجولة» (was «الجولة بالأرقام», owner 2026-10-30): the broadcast-board design (dark purple, neon green). Builds <dir>/page.html.
import json, sys
out = sys.argv[1]
AR = {'Manchester City': 'مانشستر سيتي', 'Arsenal': 'آرسنال', 'Brighton & Hove Albion': 'برايتون', 'Liverpool': 'ليفربول', 'Chelsea': 'تشيلسي',
      'Brentford': 'برينتفورد', 'Leeds United': 'ليدز', 'Newcastle United': 'نيوكاسل', 'Aston Villa': 'أستون فيلا', 'Hull City': 'هال سيتي',
      'Everton': 'إيفرتون', 'Ipswich Town': 'إيبسويتش', 'AFC Bournemouth': 'بورنموث', 'Tottenham Hotspur': 'توتنهام', 'Fulham': 'فولهام',
      'Manchester United': 'مانشستر يونايتد', 'Crystal Palace': 'كريستال بالاس', 'Nottingham Forest': 'نوتنغهام فورست', 'Coventry City': 'كوفنتري', 'Sunderland': 'سندرلاند'}
d = json.load(open(sys.argv[2]))
ID = {r['team']: r['id'] for r in d['eng.1:table']}
T = {r['team']: r for r in d['eng.1:table']}
L = lambda n: f'logo/{ID[n]}.png'
def res(h, hs, as_, a, goals, k='', photo=''):
    gl = ''.join(f'<div class="g" data-in><b>{m}\'</b> {w}</div>' for m, w in goals)
    bg = f'<div class="ph kb" style="background-image:url(ph/{photo}.jpg)"></div><div class="shade"></div>' if photo else ''
    return f'''{bg}<div class="kick" data-in="0.1">{k}</div><div class="res" data-in="0.2">
<div class="tm"><img src="{L(h)}"><span>{AR[h]}</span></div><div class="sc"><b data-n="{hs}" data-d="0.6">{hs}</b><i>-</i><b data-n="{as_}" data-d="0.9">{as_}</b></div>
<div class="tm"><img src="{L(a)}"><span>{AR[a]}</span></div></div><div class="gs">{gl}</div>'''
def trow(r, hi=''):
    t = T[r]; gd = int(t['pointsFor'] - t['pointsAgainst'])
    return f'''<div class="tr {hi}" data-in data-dir="X" data-dist="-60"><b>{int(t["rank"])}</b><img src="{L(r)}"><span>{AR[r]}</span><em>{int(t["gamesPlayed"])}</em><em><bdi dir="ltr">{"+" if gd > 0 else ""}{gd}</bdi></em><strong data-n="{int(t["points"])}">{int(t["points"])}</strong></div>'''
def tile(n, label, d=0.4): return f'<div class="tile" data-in><b data-n="{n}" data-d="{d}">{n}</b><span>{label}</span></div>'
SC = [
  '<div class="hero"><div class="tag" data-in>الدوري الإنجليزي</div><div class="big" data-in>الجولة <b>8</b></div><div class="sub" data-in>ملخص الجولة</div></div>',
  '<div class="kick" data-in>الجولة في سطر</div><div class="tiles">' + tile(10, 'مباريات') + tile(19, 'هدفًا') + tile(4, 'فوز للضيوف') + tile(3, 'فوز لأصحاب الأرض') + tile(3, 'تعادلات') + '</div>',
  res('Aston Villa', 2, 1, 'Manchester City', [], 'مفاجأة الجولة', 'villapark'),
  '<div class="kick" data-in>مجريات أستون فيلا × مانشستر سيتي</div><div class="line" data-in><div class="bar"><i data-w="100" data-d="0.3"></i></div>'
  + ''.join(f'<div class="mk {s}" style="right:{m/90*100}%" data-in="{0.6+k*0.5}"><b>{m}\'</b><span>{w}</span></div>' for k, (m, w, s) in enumerate([(6, 'نيكولاس جاكسون', 'h'), (52, 'إرلينغ هالاند', 'a'), (60, 'نيكولاس جاكسون', 'h')]))
  + '</div><div class="note" data-in="2.2">جاكسون: هدفان في مباراة واحدة أمام المتصدر</div>',
  res('Arsenal', 2, 0, 'Everton', [(68, 'غابرييل ماغالهايس')], 'آرسنال يستغل الفرصة'),
  res('Chelsea', 0, 2, 'Tottenham Hotspur', [(77, 'هدف عكسي'), (87, 'ماتيس تيل')], 'ديربي لندن في ستامفورد بريدج'),
  res('Liverpool', 2, 0, 'Brighton & Hove Albion', [(17, 'هدف عكسي'), (21, 'ألكسندر إيزاك')], 'أنفيلد'),
  res('Manchester United', 0, 3, 'AFC Bournemouth', [], 'أثقل نتيجة في الجولة', 'oldtrafford'),
  '<div class="kick" data-in>أهداف بورنموث في أولد ترافورد</div><div class="tiles three">' + ''.join(f'<div class="tile pl" data-in><b>{m}\'</b><span>{w}</span></div>' for m, w in [(38, 'ريان'), (43, 'ماركوس تافيرنييه'), (71, 'إيفانيلسون')]) + '</div>',
  res('Crystal Palace', 0, 2, 'Newcastle United', [(47, 'ويليام أوسولا'), (58, 'هارفي بارنز')], 'نيوكاسل خارج أرضه'),
  res('Coventry City', 0, 1, 'Fulham', [(80, 'أوسكار بوب')], 'هدف متأخر'),
  '<div class="kick" data-in>ثلاثة تعادلات</div><div class="mini">' + ''.join(f'<div class="mr" data-in><img src="{L(h)}"><span>{AR[h]}</span><b><i>{hs}</i> - <i>{as_}</i></b><span>{AR[a]}</span><img src="{L(a)}"></div>' for h, hs, as_, a in [('Ipswich Town', 1, 1, 'Nottingham Forest'), ('Hull City', 1, 1, 'Brentford'), ('Sunderland', 0, 0, 'Leeds United')]) + '</div>',
  '<div class="kick" data-in>الترتيب بعد الجولة 8 • الصدارة</div><div class="table"><div class="th" data-in><b>#</b><span>الفريق</span><em>لعب</em><em>الفارق</em><strong>نقاط</strong></div>' + trow('Manchester City', 'top') + trow('Arsenal', 'top') + '</div><div class="note" data-in="1.6">التساوي في النقاط • سيتي يتقدم بفارق الأهداف</div>',
  '<div class="kick" data-in>المربع الذهبي والخامس</div><div class="table">' + trow('Brighton & Hove Albion') + trow('Liverpool') + trow('Chelsea') + '</div>',
  '<div class="kick" data-in>القاع</div><div class="table">' + trow('Coventry City', 'low') + trow('Nottingham Forest', 'low') + trow('Sunderland', 'low') + '</div>',
  '<div class="kick" data-in>أرقام الموسم حتى الآن</div><div class="duo"><div class="stat" data-in><img src="' + L('Brighton & Hove Albion') + '"><b data-n="23">23</b><span>أقوى هجوم: برايتون</span></div><div class="stat" data-in><img src="' + L('Arsenal') + '"><b data-n="5">5</b><span>أقوى دفاع: آرسنال</span></div></div>',
  '<div class="kick" data-in>أزمة في أولد ترافورد</div><div class="duo"><div class="stat red" data-in><img src="' + L('Manchester United') + '"><b data-n="1">1</b><span>فوز واحد في 8 مباريات</span></div><div class="stat red" data-in><b data-n="16">16</b><span>المركز الحالي</span></div></div>',
  '<div class="kick" data-in>الجولة 9</div><div class="mini">' + ''.join(f'<div class="mr" data-in><img src="{L(h)}"><span>{AR[h]}</span><b>×</b><span>{AR[a]}</span><img src="{L(a)}"></div>' for h, a in [('Liverpool', 'Arsenal'), ('Manchester City', 'Brighton & Hove Albion'), ('Chelsea', 'Manchester United')]) + '</div>',
  '<div class="hero"><div class="big" data-in style="font-size:120px">نجم الجولة؟</div><div class="sub" data-in>اكتبه في التعليقات 👇</div><div class="tag" data-in>تابع القناة: ملخص كل جولة</div></div>',
]
CSS = '''
*{margin:0;box-sizing:border-box}body{width:1920px;height:1080px;overflow:hidden;background:#12051f;font-family:Tajawal,sans-serif;color:#fff;direction:rtl}
.bg{position:absolute;inset:0;background:radial-gradient(1200px 700px at 80% 10%,#3d0f6b 0,transparent 60%),radial-gradient(900px 600px at 10% 100%,#0b3b2c 0,transparent 60%),#12051f}
.grid{position:absolute;inset:0;background-image:linear-gradient(rgba(0,255,133,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(0,255,133,.05) 1px,transparent 1px);background-size:64px 64px}
.brand{position:absolute;top:44px;right:70px;font:800 26px Tajawal;letter-spacing:6px;color:#00ff85}.brand i{color:#fff;font-style:normal}
.chip{position:absolute;top:38px;left:70px;background:#00ff85;color:#12051f;font:800 28px Tajawal;padding:8px 24px;border-radius:40px}
.scene{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:34px;padding:120px 120px 170px}
.ph{position:absolute;inset:0;background-size:cover;background-position:center;opacity:.35;filter:saturate(.7)}.shade{position:absolute;inset:0;background:linear-gradient(0deg,#12051f 10%,rgba(18,5,31,.55))}
.scene>*{position:relative}
.hero{text-align:center}.hero .big{font:400 190px Lalezar;line-height:1}.hero .big b{color:#00ff85;font-weight:400}.hero .sub{font:800 64px Tajawal;color:#c9b8ff}.hero .tag{display:inline-block;margin:20px 0;font:800 34px Tajawal;color:#00ff85;border:2px solid #00ff85;border-radius:50px;padding:8px 34px}
.kick{font:800 40px Tajawal;color:#00ff85;letter-spacing:1px}
.res{display:flex;align-items:center;gap:80px}.tm{display:flex;flex-direction:column;align-items:center;gap:18px;width:420px}.tm img{width:220px;height:220px;object-fit:contain;filter:drop-shadow(0 10px 30px rgba(0,0,0,.6))}.tm span{font:400 56px Lalezar}
.sc{display:flex;align-items:center;gap:26px;font:400 200px Lalezar;direction:rtl}.sc i{color:#00ff85;font-style:normal;font-size:120px}
.gs{display:flex;gap:26px}.g{background:rgba(255,255,255,.08);border:1px solid rgba(0,255,133,.35);border-radius:18px;padding:12px 26px;font:800 34px Tajawal}.g b{color:#00ff85}
.tiles{display:flex;gap:30px}.tile{width:290px;height:250px;border-radius:30px;background:linear-gradient(160deg,rgba(255,255,255,.1),rgba(255,255,255,.03));border:2px solid rgba(0,255,133,.4);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px}
.tile b{font:400 120px Lalezar;color:#00ff85;line-height:1.1}.tile span{font:800 32px Tajawal;color:#e6dcff}.tiles.three .tile{width:440px}.tile.pl b{font-size:96px}.tile.pl span{font-size:40px}
.line{width:1500px;height:330px;position:relative}.bar{position:absolute;top:150px;right:0;left:0;height:10px;background:rgba(255,255,255,.12);border-radius:10px}.bar i{display:block;height:100%;background:#00ff85;border-radius:10px;margin-right:0}
.mk{position:absolute;top:0;transform:translateX(50%);display:flex;flex-direction:column;align-items:center;gap:10px;width:360px}.mk b{font:400 64px Lalezar;color:#00ff85}.mk span{font:800 34px Tajawal}.mk.a{top:180px}.mk.a b{color:#6cabdd}
.note{font:800 40px Tajawal;color:#e6dcff;background:rgba(0,255,133,.12);padding:14px 36px;border-radius:20px}
.mini{display:flex;flex-direction:column;gap:22px}.mr{display:grid;grid-template-columns:90px 400px 200px 400px 90px;align-items:center;background:rgba(255,255,255,.07);border-radius:24px;padding:16px 30px;font:400 46px Lalezar;text-align:center}.mr img{width:80px;height:80px;object-fit:contain}.mr b{color:#00ff85;display:flex;justify-content:center;gap:14px}.mr b i{font-style:normal}
.table{display:flex;flex-direction:column;gap:14px;width:1300px}.tr,.th{display:grid;grid-template-columns:90px 100px 1fr 140px 160px 170px;align-items:center;padding:16px 34px;border-radius:22px;background:rgba(255,255,255,.07);font:800 44px Tajawal}
.th{background:none;color:#a99bd6;font-size:30px;padding:0 34px}.tr img{width:72px;height:72px;object-fit:contain}.tr em{font-style:normal;text-align:center;color:#c9b8ff}.tr strong{font:400 64px Lalezar;color:#00ff85;text-align:center}.tr b{font:400 52px Lalezar}
.tr.top{border:2px solid #00ff85}.tr.low{border:2px solid #ff4d6d}.tr.low strong{color:#ff4d6d}
.duo{display:flex;gap:60px}.stat{width:620px;height:430px;border-radius:36px;background:linear-gradient(160deg,rgba(0,255,133,.16),rgba(255,255,255,.03));border:2px solid rgba(0,255,133,.4);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px}
.stat img{width:110px;height:110px;object-fit:contain}.stat b{font:400 170px Lalezar;line-height:1.05;color:#00ff85}.stat span{font:800 38px Tajawal}.stat.red{background:linear-gradient(160deg,rgba(255,77,109,.18),rgba(255,255,255,.03));border-color:rgba(255,77,109,.5)}.stat.red b{color:#ff4d6d}
#cap{position:absolute;bottom:58px;left:50%;transform:translateX(-50%);max-width:1500px;text-align:center;font:800 40px Tajawal;background:rgba(10,3,18,.82);padding:12px 34px;border-radius:16px;border-right:6px solid #00ff85}
#progw{position:absolute;bottom:0;left:0;right:0;height:8px;background:rgba(255,255,255,.08)}#prog{height:100%;background:#00ff85;width:0;margin-right:auto}
'''
html = f'''<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><link rel="stylesheet" href="../fonts/fonts.css"><style>{CSS}</style></head>
<body><div class="bg"></div><div class="grid"></div><div class="brand">FOOTBALL <i>LEGENDS</i></div><div class="chip">ملخص الجولة</div>
{''.join(f'<div class="scene" style="opacity:0">{s}</div>' for s in SC)}<div id="cap"></div><div id="progw"><div id="prog"></div></div><script src="../engine.js"></script></body></html>'''
open(f'{out}/page.html', 'w').write(html); print('scenes', len(SC))
