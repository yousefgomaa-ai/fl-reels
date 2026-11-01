NAME = 'كفاراتسخيليا'
BADGES = ['🏆 دوري الأبطال ×2', '⭐ أفضل لاعب في دوري الأبطال']
CLUBS = [7755, 8710, 8683, 9875, 9847, 8268]
CONSTS = "const DIN = 'rgba(0,90,170,.45)', NAP = 'rgba(0,120,200,.45)', PSG = 'rgba(0,40,110,.55)', GEO = 'rgba(200,16,46,.45)';"
SC = r'''
  { club: -1, html: '' },
  { club: 0, glow: '#0c1e3a', html: `<div class="yrs" style="font-size:110px">2001</div><div class="vs"><img src="${L(7755)}"></div><div class="ttl">تبليسي، جورجيا</div>${SUB('البداية مع دينامو تبليسي')}` },
  { club: 2, glow: '#3a0c14', html: `<div class="ttl">في روسيا</div><div class="vs"><img src="${L(8710)}"><span class="x">←</span><img src="${L(8683)}"></div><div class="rows">${row('🏆', 'كأس روسيا', '✓')}${row('🗓', 'روبين قازان', '3 مواسم')}</div>` },
  { club: 3, glow: '#0c2a44', html: `<div class="yrs" style="font-size:90px">صيف 2022</div><div class="vs"><img src="${L(8683)}"><span class="x">←</span><img src="${L(9875)}"></div><div class="ttl">إلى نابولي</div>` },
  { ph: 1, club: 3, glow: '#0c2a44', html: head(9875, 'نابولي', 'موسم 2022 - 2023', NAP) + `<div class="rows">${row('🏆', 'الدوري الإيطالي', '✓')}${row('⏳', 'أول لقب منذ', '33 عامًا')}</div>` },
  { club: 3, glow: '#0c2a44', html: head(9875, 'نابولي', '2022 - 2025', NAP) + `<div class="chips">${chip(30, 'هدفًا', 30)}${chip(24, 'تمريرة حاسمة', 24)}${chip(107, 'مباراة', 107)}</div>` },
  { club: 4, glow: '#0c1430', html: `<div class="yrs" style="font-size:90px">يناير 2025</div><div class="vs"><img src="${L(9875)}"><span class="x">←</span><img src="${L(9847)}"></div><div class="ttl">إلى باريس سان جيرمان</div>` },
  { club: 4, glow: '#0c1430', html: `<div class="ttl">في نصف موسم</div><div class="rows">${row('🏆', 'دوري أبطال أوروبا', '✓')}${row('⚽', 'هدف في النهائي', '✓')}${row('🏆', 'الدوري والكأس', '✓')}</div>` },
  { club: 4, glow: '#3a2a10', html: `<div class="ttl">الموسم الماضي</div><div class="rows">${row('🏆', 'دوري الأبطال', '×2')}${row('🏆', 'الدوري الفرنسي', '×2')}${row('⭐', 'أفضل لاعب في دوري الأبطال', '✓')}</div>` },
  { club: 4, glow: '#0c1430', html: head(9847, 'باريس سان جيرمان', 'منذ 2025', PSG) + `<div class="chips">${chip(29, 'هدفًا', 29)}${chip(18, 'تمريرة حاسمة', 18)}${chip(91, 'مباراة', 91)}</div>` },
  { club: 5, glow: '#3a0c14', html: head(8268, 'منتخب جورجيا', 'يورو 2024', GEO) + `<div class="rows">${row('🌍', 'أول بطولة كبرى', '✓')}${row('🏁', 'دور الستة عشر', '✓')}</div>` },
  { club: 5, glow: '#3a0c14', html: `<div class="ttl">مع منتخب جورجيا</div><div class="chips">${chip(23, 'هدفًا', 23)}${chip(54, 'مباراة', 54)}</div>` },
  { club: 5, glow: '#2a1a5e', html: `<div class="vs" style="gap:14px;flex-wrap:wrap;justify-content:center">${CLUBS.map((id) => `<img src="${L(id)}" style="width:92px;height:92px">`).join('<span class="x" style="font-size:40px">←</span>')}</div><div class="ttl" style="margin-top:30px">أي محطة هي<br>الأجمل في رأيك؟</div>${SUB('اكتبها في التعليقات 👇')}` },
'''
