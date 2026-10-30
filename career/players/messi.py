NAME = 'ليونيل ميسي'
BADGES = ['⭐ الكرة الذهبية ×8', '🏆 بطل العالم 2022']
CLUBS = [8634, 9847, 960720, 6706]
CONSTS = "const BAR = 'rgba(165,0,68,.45)', PSG = 'rgba(0,65,112,.6)', MIA = 'rgba(247,181,205,.4)', ARG = 'rgba(108,172,228,.45)';"
SC = r'''
  { club: -1, html: '' },
  { club: 0, glow: '#2a0c1e', html: `<div class="yrs" style="font-size:110px">1987</div><div class="vs"><img src="${L(8634)}"></div><div class="ttl">من روزاريو إلى برشلونة</div>${SUB('انتقل إليها وعمره 13 عامًا')}` },
  { ph: 1, club: 0, glow: '#2a0c1e', html: head(8634, 'برشلونة', '2004 - 2021', BAR) + `<div class="chips">${chip(672, 'هدفًا', 672)}${chip(778, 'مباراة', 778)}</div>${SUB('الهداف التاريخي للنادي')}` },
  { ph: 1, club: 0, glow: '#2a0c1e', html: `<div class="ttl">مع برشلونة</div><div class="rows">${row('🏆', 'الدوري الإسباني', '×10')}${row('🏆', 'دوري أبطال أوروبا', '×4')}</div>` },
  { ph: 1, club: 0, glow: '#2a0c1e', html: `<div class="yrs" style="font-size:120px">2012</div><div class="chips">${chip(91, 'هدفًا', 91)}</div><div class="ttl" style="font-size:66px">في عام واحد</div>${SUB('رقم قياسي')}` },
  { club: 1, glow: '#0c1a3a', html: head(9847, '<span style="font-size:84px">باريس سان جيرمان</span>', '2021 - 2023', PSG) + `<div class="rows">${row('🏆', 'الدوري الفرنسي', '×2')}</div>` },
  { ph: 3, club: 2, glow: '#3a1028', html: `<div class="yrs" style="font-size:90px">صيف 2023</div><div class="vs"><img src="${L(9847)}"><span class="x">←</span><img src="${L(960720)}"></div><div class="ttl">إلى إنتر ميامي</div><div class="rows">${row('🏆', 'كأس الدوريات', '2023')}</div>` },
  { ph: 3, club: 2, glow: '#3a1028', html: head(960720, 'إنتر ميامي', 'منذ 2023', MIA) + `<div class="rows">${row('🏆', 'الدوري الأمريكي', '2025')}${row('⭐', 'أفضل لاعب في الدوري', '×2')}</div>${SUB('أول لقب في تاريخ النادي')}` },
  { ph: 2, club: 3, glow: '#0c2a3a', html: head(6706, 'منتخب الأرجنتين', '', ARG) + `<div class="rows">${row('🏆', 'كوبا أمريكا', '2021')}${row('🏆', 'كأس العالم', '2022')}${row('⭐', 'أفضل لاعب في كأس العالم', '✓')}</div>` },
  { ph: 2, club: 3, glow: '#0c2a3a', html: `<div class="yrs" style="font-size:120px">2024</div><div class="ttl" style="font-size:66px">كوبا أمريكا مرة ثانية</div><div class="rows">${row('🏆', 'لقبان متتاليان', '✓')}</div>` },
  { ph: 2, club: 3, glow: '#0c2a3a', html: `<div class="ttl" style="font-size:72px">كأس العالم 2026</div><div class="rows">${row('⚽', 'الهداف التاريخي لكأس العالم', '✓')}${row('🏟️', 'الوصول إلى النهائي', '✓')}</div>${SUB('متخطيًا رقم كلوزه')}` },
  { ph: 2, club: 3, glow: '#0c2a3a', html: `<div class="ttl" style="font-size:66px">الهداف التاريخي للأرجنتين</div><div class="chips">${chip(126, 'هدفًا', 126)}${chip(208, 'مباراة', 208)}</div>${SUB('ثم اعتزل اللعب الدولي')}` },
  { ph: 3, club: 2, glow: '#3a2a10', html: `<div class="yrs" style="font-size:150px">8</div><div class="ttl">كرات ذهبية</div>${SUB('رقم قياسي لم يصل إليه أحد')}` },
  { club: 3, glow: '#2a1a5e', html: `<div class="vs" style="gap:14px;flex-wrap:wrap;justify-content:center">${CLUBS.map((id) => `<img src="${L(id)}" style="width:120px;height:120px">`).join('<span class="x" style="font-size:40px">←</span>')}</div><div class="ttl" style="margin-top:30px">أي محطة هي<br>الأجمل في رأيك؟</div>${SUB('اكتبها في التعليقات 👇')}` },
'''
