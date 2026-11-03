NAME = 'فينيسيوس جونيور'
BADGES = ['🏆 دوري الأبطال ×2', '⭐ أفضل لاعب في العالم 2024']
CLUBS = [9770, 8633, 8256]
CONSTS = "const FLA = 'rgba(200,16,46,.45)', RMA = 'rgba(255,255,255,.25)', BRA = 'rgba(0,155,58,.5)';"
SC = r'''
  { club: -1, html: '' },
  { ph: 2, club: 0, glow: '#3a0c0c', html: head(9770, 'فلامنغو', 'مولود 2000', FLA) + `<div class="rows">${row('⚡', 'أول مباراة وعمره', '16 عامًا')}</div>` },
  { club: 1, glow: '#1a1a2e', html: `<div class="yrs" style="font-size:90px">صيف 2018</div><div class="vs"><img src="${L(9770)}"><span class="x">←</span><img src="${L(8633)}"></div><div class="ttl">إلى ريال مدريد</div>${SUB('وعمره 18 عامًا')}` },
  { ph: 1, club: 1, glow: '#3a2a10', html: `<div class="yrs" style="font-size:110px">2022</div><div class="ttl" style="font-size:66px">نهائي دوري الأبطال</div><div class="rows">${row('⚽', 'هدف الفوز أمام ليفربول', '✓')}</div>` },
  { club: 1, glow: '#3a2a10', html: `<div class="yrs" style="font-size:110px">2024</div><div class="ttl" style="font-size:66px">نهائي دوري الأبطال</div><div class="rows">${row('⚽', 'هدف أمام دورتموند', '✓')}${row('🏆', 'اللقب الأوروبي', '×2')}</div>` },
  { club: 1, glow: '#1a1a2e', html: `<div class="ttl">مع ريال مدريد</div><div class="rows">${row('🏆', 'الدوري الإسباني', '×3')}</div>` },
  { club: 1, glow: '#3a2a10', html: `<div class="yrs" style="font-size:120px">2024</div><div class="rows">${row('⭐', 'جائزة الفيفا للأفضل', '✓')}${row('🥈', 'الكرة الذهبية', 'المركز 2')}</div>` },
  { club: 1, glow: '#3a2a10', html: `<div class="ttl" style="font-size:140px">⭐</div><div class="ttl">أفضل لاعب</div>${SUB('في دوري أبطال أوروبا 2023 - 2024')}` },
  { club: 1, glow: '#1a1a2e', html: head(8633, 'ريال مدريد', 'منذ 2018', RMA) + `<div class="chips">${chip(129, 'هدفًا', 129)}${chip(88, 'تمريرة حاسمة', 88)}${chip(386, 'مباراة', 386)}</div>` },
  { club: 1, glow: '#1a1a2e', html: `<div class="ttl" style="font-size:66px">تجديد العقد</div><div class="yrs" style="font-size:130px">2032</div>${SUB('مع ريال مدريد')}` },
  { club: 2, glow: '#0c3a1e', html: head(8256, 'منتخب البرازيل', 'منذ 2019', BRA) + `<div class="chips">${chip(14, 'هدفًا', 14)}${chip(57, 'مباراة', 57)}</div>` },
  { club: 2, glow: '#0c3a1e', html: `<div class="ttl">مع الناشئين</div><div class="rows">${row('🏆', 'بطولة أمريكا الجنوبية', '✓')}${row('👟', 'هداف البطولة', '✓')}</div>${SUB('تحت 17 عامًا')}` },
  { club: 2, glow: '#2a1a5e', html: `<div class="vs" style="gap:24px;justify-content:center">${CLUBS.map((id) => `<img src="${L(id)}" style="width:130px;height:130px">`).join('<span class="x" style="font-size:40px">←</span>')}</div><div class="ttl" style="margin-top:30px">أي محطة هي<br>الأجمل في رأيك؟</div>${SUB('اكتبها في التعليقات 👇')}` },
'''
