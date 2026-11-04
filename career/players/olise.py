NAME = 'مايكل أوليسيه'
BADGES = ['🏆 بطل ألمانيا مرتين', '🥈 فضية الأولمبياد 2024']
CLUBS = [9798, 9826, 9823, 6723]
CONSTS = "const REA = 'rgba(0,70,160,.4)', CRY = 'rgba(27,69,143,.45)', FCB = 'rgba(220,5,45,.45)', FRA = 'rgba(0,35,149,.45)';"
SC = r'''
  { club: -1, html: '' },
  { club: 0, glow: '#0c1e3a', html: head(9798, 'ريدينغ', 'مولود في لندن 2001', REA) + `<div class="rows">${row('⚽', 'البداية الاحترافية', '2019')}</div>` },
  { club: 1, glow: '#0c1e3a', html: `<div class="yrs" style="font-size:90px">صيف 2021</div><div class="vs"><img src="${L(9798)}"><span class="x">←</span><img src="${L(9826)}"></div><div class="ttl">إلى كريستال بالاس</div>` },
  { club: 1, glow: '#0c1e3a', html: head(9826, 'كريستال بالاس', '2021 - 2024', CRY) + `<div class="chips">${chip(16, 'هدفًا', 16)}${chip(90, 'مباراة', 90)}</div>` },
  { club: 2, glow: '#3a0c14', html: `<div class="yrs" style="font-size:90px">صيف 2024</div><div class="vs"><img src="${L(9826)}"><span class="x">←</span><img src="${L(9823)}"></div><div class="ttl">إلى بايرن ميونخ</div>` },
  { ph: 2, club: 3, glow: '#0c1640', html: head(6723, 'فرنسا', 'أولمبياد 2024', FRA) + `<div class="rows">${row('🥈', 'الميدالية الفضية', '✓')}</div>` },
  { club: 2, glow: '#3a0c14', html: `<div class="ttl">الموسم الأول</div><div class="rows">${row('🏆', 'الدوري الألماني', '✓')}${row('⭐', 'أفضل لاعب في بايرن', '✓')}</div>` },
  { ph: 1, club: 2, glow: '#3a0c14', html: `<div class="ttl">موسم 2025 - 2026</div><div class="chips">${chip(25, 'هدفًا', 25)}${chip(28, 'تمريرة حاسمة', 28)}</div><div class="rows">${row('🏆', 'الدوري والكأس', '✓')}</div>` },
  { club: 2, glow: '#3a0c14', html: `<div class="ttl">أفضل لاعب في بايرن</div><div class="yrs">للمرة الثانية على التوالي</div>` },
  { club: 2, glow: '#3a0c14', html: head(9823, 'بايرن ميونخ', 'منذ 2024', FCB) + `<div class="chips">${chip('+50', 'هدفًا')}${chip('+50', 'تمريرة حاسمة')}</div>` },
  { club: 3, glow: '#0c1640', html: `<div class="ttl">مع منتخب فرنسا</div><div class="chips">${chip(11, 'هدفًا', 11)}${chip(29, 'مباراة', 29)}</div>${SUB('ومشاركة في كأس العالم')}` },
  { club: 3, glow: '#2a1a5e', html: `<div class="vs" style="gap:14px;flex-wrap:wrap;justify-content:center">${CLUBS.map((id) => `<img src="${L(id)}" style="width:100px;height:100px">`).join('<span class="x" style="font-size:40px">←</span>')}</div><div class="ttl" style="margin-top:30px">أي محطة هي<br>الأجمل في رأيك؟</div>${SUB('اكتبها في التعليقات 👇')}` },
'''
