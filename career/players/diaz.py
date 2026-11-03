NAME = 'لويس دياز'
BADGES = ['🏆 بطل إنجلترا وألمانيا', '👟 هداف كوبا أمريكا']
CLUBS = [2254, 9773, 8650, 9823, 8258]
CONSTS = "const JUN = 'rgba(200,16,46,.4)', POR = 'rgba(0,80,160,.45)', LIV = 'rgba(200,16,46,.45)', FCB = 'rgba(220,5,45,.45)', COL = 'rgba(252,209,22,.35)';"
SC = r'''
  { club: -1, html: '' },
  { club: 0, glow: '#3a0c0c', html: head(2254, 'جونيور بارانكيا', 'مولود 1997', JUN) + `<div class="rows">${row('🏆', 'الدوري الكولومبي', '✓')}</div>` },
  { club: 1, glow: '#0c1e3a', html: `<div class="yrs" style="font-size:90px">صيف 2019</div><div class="vs"><img src="${L(2254)}"><span class="x">←</span><img src="${L(9773)}"></div><div class="rows">${row('🏆', 'الدوري والكأس في البرتغال', '✓')}</div>` },
  { ph: 2, club: 4, glow: '#3a3a0c', html: head(8258, 'كوبا أمريكا', '2021', COL) + `<div class="rows">${row('👟', 'هداف البطولة مع ميسي', '✓')}</div>` },
  { club: 2, glow: '#3a0c0c', html: `<div class="yrs" style="font-size:90px">يناير 2022</div><div class="vs"><img src="${L(9773)}"><span class="x">←</span><img src="${L(8650)}"></div><div class="rows">${row('🏆', 'كأس الاتحاد الإنجليزي', '✓')}${row('🏆', 'كأس الرابطة', '✓')}</div>` },
  { ph: 1, club: 2, glow: '#3a0c0c', html: head(8650, 'ليفربول', 'موسم 2024 - 2025', LIV) + `<div class="rows">${row('🏆', 'الدوري الإنجليزي', '✓')}</div>` },
  { club: 2, glow: '#3a0c0c', html: head(8650, 'ليفربول', '2022 - 2025', LIV) + `<div class="chips">${chip(41, 'هدفًا', 41)}${chip(16, 'تمريرة حاسمة', 16)}${chip(148, 'مباراة', 148)}</div>` },
  { club: 3, glow: '#3a0c14', html: `<div class="yrs" style="font-size:90px">صيف 2025</div><div class="vs"><img src="${L(8650)}"><span class="x">←</span><img src="${L(9823)}"></div><div class="ttl">إلى بايرن ميونخ</div>` },
  { club: 3, glow: '#3a0c14', html: `<div class="ttl">الموسم الأول</div><div class="rows">${row('🏆', 'الدوري الألماني', '✓')}${row('🏆', 'كأس ألمانيا', '✓')}</div>` },
  { club: 3, glow: '#3a0c14', html: head(9823, 'بايرن ميونخ', 'منذ 2025', FCB) + `<div class="chips">${chip(31, 'هدفًا', 31)}${chip(20, 'تمريرة حاسمة', 20)}${chip(62, 'مباراة', 62)}</div>` },
  { club: 4, glow: '#3a3a0c', html: head(8258, 'منتخب كولومبيا', 'كوبا أمريكا 2024', COL) + `<div class="rows">${row('🥈', 'الوصول إلى النهائي', '✓')}</div>` },
  { club: 4, glow: '#3a3a0c', html: `<div class="ttl">مع منتخب كولومبيا</div><div class="chips">${chip(23, 'هدفًا', 23)}${chip(79, 'مباراة', 79)}</div>` },
  { club: 4, glow: '#2a1a5e', html: `<div class="vs" style="gap:14px;flex-wrap:wrap;justify-content:center">${CLUBS.map((id) => `<img src="${L(id)}" style="width:100px;height:100px">`).join('<span class="x" style="font-size:40px">←</span>')}</div><div class="ttl" style="margin-top:30px">أي محطة هي<br>الأجمل في رأيك؟</div>${SUB('اكتبها في التعليقات 👇')}` },
'''
