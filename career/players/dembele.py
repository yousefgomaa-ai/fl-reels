NAME = 'عثمان ديمبيلي'
BADGES = ['⭐ الكرة الذهبية 2025', '🏆 بطل العالم 2018']
CLUBS = [9851, 9789, 8634, 9847, 6723]
CONSTS = "const REN = 'rgba(226,0,26,.45)', BVB = 'rgba(253,225,0,.4)', BAR = 'rgba(165,0,68,.45)', PSG = 'rgba(0,65,112,.6)', FRA = 'rgba(0,85,164,.55)';"
SC = r'''
  { club: -1, html: '' },
  { ph: 3, club: 0, glow: '#3a0c10', html: `<div class="yrs" style="font-size:110px">1997</div><div class="vs"><img src="${L(9851)}"></div><div class="ttl">ابن فيرنون</div>${SUB('البداية الاحترافية مع رين')}` },
  { ph: 3, club: 0, glow: '#3a0c10', html: head(9851, 'رين', '2015 - 2016', REN) + `<div class="chips">${chip(12, 'هدفًا', 12)}</div>${SUB('في موسمه الأول')}` },
  { club: 1, glow: '#2e2a0c', html: head(9789, '<span style="font-size:84px">بوروسيا دورتموند</span>', '2016 - 2017', BVB) + `<div class="rows">${row('🏆', 'كأس ألمانيا', '✓')}</div><div class="chips">${chip(21, 'تمريرة حاسمة', 21)}</div>` },
  { ph: 1, club: 2, glow: '#2a0c1e', html: `<div class="yrs" style="font-size:90px">صيف 2017</div><div class="vs"><img src="${L(9789)}"><span class="x">←</span><img src="${L(8634)}"></div><div class="ttl">إلى برشلونة</div>` },
  { ph: 1, club: 2, glow: '#2a0c1e', html: head(8634, 'برشلونة', '2017 - 2023', BAR) + `<div class="rows">${row('🏆', 'الدوري الإسباني', '×3')}${row('🏆', 'كأس ملك إسبانيا', '×2')}</div>` },
  { ph: 2, club: 4, glow: '#0c1a3a', html: `<div class="yrs" style="font-size:120px">2018</div><div class="ttl" style="font-size:70px">بطل العالم مع فرنسا</div><div class="vs"><img src="${L(6723)}"></div>${SUB('كأس العالم في روسيا')}` },
  { ph: 0, club: 4, glow: '#0c1a3a', html: `<div class="yrs" style="font-size:120px">2022</div><div class="ttl" style="font-size:66px">نهائي كأس العالم</div><div class="vs"><img src="${L(6723)}"></div>${SUB('مع فرنسا في قطر')}` },
  { club: 3, glow: '#0c1a3a', html: `<div class="yrs" style="font-size:90px">صيف 2023</div><div class="vs"><img src="${L(8634)}"><span class="x">←</span><img src="${L(9847)}"></div><div class="ttl">إلى باريس سان جيرمان</div>` },
  { club: 3, glow: '#0c1a3a', html: `<div class="ttl">مع باريس</div><div class="rows">${row('🏆', 'الدوري الفرنسي', '×3')}${row('🔁', 'متتالية', '2024 - 2026')}${row('🏆', 'كأس فرنسا', '×2')}</div>` },
  { club: 3, glow: '#0c1a3a', html: `<div class="yrs" style="font-size:120px">2025</div><div class="ttl" style="font-size:66px">نهائي دوري أبطال أوروبا</div><div class="rows">${row('🎯', 'صنع هدفين أمام إنتر', '✓')}${row('🏆', 'أول لقب في تاريخ باريس', '✓')}</div>` },
  { club: 3, glow: '#0c1a3a', html: `<div class="yrs" style="font-size:120px">2026</div><div class="ttl" style="font-size:66px">دوري أبطال أوروبا مرة ثانية</div><div class="rows">${row('🏆', 'لقبان متتاليان', '✓')}</div>` },
  { ph: 0, club: 3, glow: '#3a2a10', html: `<div class="yrs" style="font-size:120px">2025</div><div class="ttl">الكرة الذهبية</div>${SUB('أفضل لاعب في العالم')}` },
  { ph: 0, club: 4, glow: '#0c1a3a', html: `<div class="vs"><img src="${L(6723)}"></div><div class="ttl" style="font-size:72px">كأس العالم 2026</div><div class="rows">${row('⚽', 'أهداف في البطولة', '6')}${row('🎩', 'هاتريك أمام النرويج', '✓')}${row('🌍', 'نصف النهائي', '✓')}</div>` },
  { club: 3, glow: '#0c1a3a', html: head(9847, '<span style="font-size:84px">باريس سان جيرمان</span>', 'منذ 2023', PSG) + `<div class="chips">${chip(65, 'هدفًا', 65)}${chip(43, 'تمريرة حاسمة', 43)}${chip(145, 'مباراة', 145)}</div>` },
  { club: 4, glow: '#2a1a5e', html: `<div class="vs" style="gap:14px;flex-wrap:wrap;justify-content:center">${CLUBS.map((id) => `<img src="${L(id)}" style="width:110px;height:110px">`).join('<span class="x" style="font-size:40px">←</span>')}</div><div class="ttl" style="margin-top:30px">أي محطة هي<br>الأجمل في رأيك؟</div>${SUB('اكتبها في التعليقات 👇')}` },
'''
