NAME = 'جود بيلينغهام'
BADGES = ['🏆 دوري الأبطال 2024', '⚽ 7 أهداف في كأس العالم']
CLUBS = [8658, 9789, 8633, 8491]
CONSTS = "const BIR = 'rgba(0,70,160,.45)', BVB = 'rgba(253,225,0,.35)', RMA = 'rgba(255,255,255,.25)', ENG = 'rgba(206,17,36,.4)';"
SC = r'''
  { club: -1, html: '' },
  { club: 0, glow: '#0c1e3a', html: head(8658, 'برمنغهام سيتي', 'مولود 2003', BIR) + `<div class="rows">${row('⚡', 'أول مباراة وعمره', '16 عامًا')}</div>` },
  { club: 0, glow: '#0c1e3a', html: `<div class="ttl" style="font-size:180px">22</div><div class="ttl">قميصه محجوب</div>${SUB('تكريمًا له بعد موسم واحد')}` },
  { club: 1, glow: '#2e2a0c', html: `<div class="yrs" style="font-size:90px">صيف 2020</div><div class="vs"><img src="${L(8658)}"><span class="x">←</span><img src="${L(9789)}"></div><div class="rows">${row('🏆', 'كأس ألمانيا', '✓')}</div>` },
  { club: 1, glow: '#2e2a0c', html: head(9789, 'بوروسيا دورتموند', '2020 - 2023', BVB) + `<div class="chips">${chip(24, 'هدفًا', 24)}${chip(23, 'تمريرة حاسمة', 23)}${chip(132, 'مباراة', 132)}</div>` },
  { club: 2, glow: '#1a1a2e', html: `<div class="yrs" style="font-size:90px">صيف 2023</div><div class="vs"><img src="${L(9789)}"><span class="x">←</span><img src="${L(8633)}"></div><div class="ttl">إلى ريال مدريد</div>` },
  { club: 2, glow: '#1a1a2e', html: `<div class="ttl">الموسم الأول</div><div class="rows">${row('🏆', 'الدوري الإسباني', '✓')}${row('🏆', 'دوري أبطال أوروبا', '✓')}${row('⭐', 'أفضل لاعب في الدوري', '✓')}</div>` },
  { ph: 2, club: 2, glow: '#3a2a10', html: `<div class="ttl">جائزة كوبا</div><div class="rows">${row('⭐', 'أفضل لاعب شاب في العالم', '✓')}</div>` },
  { club: 2, glow: '#1a1a2e', html: head(8633, 'ريال مدريد', 'منذ 2023', RMA) + `<div class="chips">${chip(50, 'هدفًا', 50)}${chip(35, 'تمريرة حاسمة', 35)}${chip(154, 'مباراة', 154)}</div>` },
  { club: 3, glow: '#3a0c14', html: head(8491, 'منتخب إنجلترا', 'يورو 2024', ENG) + `<div class="rows">${row('🥈', 'نهائي أمم أوروبا', '✓')}</div>` },
  { ph: 1, club: 3, glow: '#3a0c14', html: `<div class="yrs" style="font-size:110px">2026</div><div class="ttl">كأس العالم</div><div class="chips">${chip(7, 'أهداف', 7)}</div><div class="rows">${row('🥉', 'المركز الثالث', '✓')}</div>` },
  { club: 3, glow: '#3a0c14', html: `<div class="ttl">مع منتخب إنجلترا</div><div class="chips">${chip(14, 'هدفًا', 14)}${chip(60, 'مباراة', 60)}</div>` },
  { club: 3, glow: '#2a1a5e', html: `<div class="vs" style="gap:24px;justify-content:center">${CLUBS.map((id) => `<img src="${L(id)}" style="width:120px;height:120px">`).join('<span class="x" style="font-size:40px">←</span>')}</div><div class="ttl" style="margin-top:30px">أي محطة هي<br>الأجمل في رأيك؟</div>${SUB('اكتبها في التعليقات 👇')}` },
'''
