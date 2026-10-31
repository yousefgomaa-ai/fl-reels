NAME = 'رافينيا'
BADGES = ['©️ قائد برشلونة', '⭐ خامس الكرة الذهبية 2025']
CLUBS = [7844, 9768, 9851, 8463, 8634, 8256]
CONSTS = "const VSC = 'rgba(255,255,255,.25)', SCP = 'rgba(0,128,87,.5)', LEE = 'rgba(255,205,0,.35)', BAR = 'rgba(165,0,68,.45)', BRA = 'rgba(0,155,58,.5)';"
SC = r'''
  { club: -1, html: '' },
  { club: 0, glow: '#1e1e1e', html: `<div class="yrs" style="font-size:110px">1996</div><div class="vs"><img src="${L(8256)}"><span class="x">←</span><img src="${L(7844)}"></div><div class="ttl">من بورتو أليغري إلى البرتغال</div>${SUB('مع فيتوريا غيماريش وعمره 19 عامًا')}` },
  { club: 1, glow: '#0c3a24', html: head(9768, '<span style="font-size:84px">سبورتينغ لشبونة</span>', '2018 - 2019', SCP) + `<div class="rows">${row('🏆', 'كأس البرتغال', '✓')}${row('🏆', 'كأس الرابطة', '✓')}</div>${SUB('ثم إلى رين الفرنسي')}` },
  { ph: 1, club: 3, glow: '#2e2a0c', html: head(8463, 'ليدز يونايتد', '2020 - 2022', LEE) + `<div class="chips">${chip(17, 'هدفًا', 17)}${chip(67, 'مباراة', 67)}</div>` },
  { club: 4, glow: '#2a0c1e', html: `<div class="yrs" style="font-size:90px">صيف 2022</div><div class="vs"><img src="${L(8463)}"><span class="x">←</span><img src="${L(8634)}"></div><div class="ttl">إلى برشلونة</div>` },
  { club: 4, glow: '#2a0c1e', html: `<div class="ttl">مع برشلونة</div><div class="rows">${row('🏆', 'الدوري الإسباني', '×3')}${row('🔁', 'آخرها لقبان متتاليان', '✓')}</div>${SUB('2025 و2026')}` },
  { club: 4, glow: '#2a0c1e', html: `<div class="ttl" style="font-size:66px">موسم الثلاثية المحلية</div><div class="chips">${chip(34, 'هدفًا', 34)}</div><div class="rows">${row('🏆', 'الدوري والكأس والسوبر', '✓')}</div>` },
  { club: 4, glow: '#3a2a10', html: `<div class="yrs" style="font-size:120px">2025</div><div class="rows">${row('⭐', 'الكرة الذهبية', 'المركز 5')}</div>${SUB('أفضل موسم في مسيرته')}` },
  { club: 4, glow: '#2a0c1e', html: head(8634, 'برشلونة', 'منذ 2022', BAR) + `<div class="chips">${chip(90, 'هدفًا', 90)}${chip(55, 'تمريرة حاسمة', 55)}${chip(189, 'مباراة', 189)}</div>` },
  { club: 4, glow: '#2a0c1e', html: `<div class="ttl">قائد برشلونة</div><div class="vs"><img src="${L(8634)}"></div><div class="rows">${row('©️', 'أول برازيلي قائدًا أساسيًا', '✓')}</div>` },
  { club: 4, glow: '#2a0c1e', html: `<div class="ttl" style="font-size:66px">تجديد العقد</div><div class="yrs" style="font-size:130px">2030</div>${SUB('مع برشلونة')}` },
  { ph: 2, club: 5, glow: '#0c3a1e', html: head(8256, 'منتخب البرازيل', 'كأس العالم مرتين', BRA) + `<div class="chips">${chip(12, 'هدفًا', 12)}${chip(43, 'مباراة', 43)}</div>` },
  { club: 5, glow: '#2a1a5e', html: `<div class="vs" style="gap:14px;flex-wrap:wrap;justify-content:center">${CLUBS.map((id) => `<img src="${L(id)}" style="width:110px;height:110px">`).join('<span class="x" style="font-size:40px">←</span>')}</div><div class="ttl" style="margin-top:30px">أي محطة هي<br>الأجمل في رأيك؟</div>${SUB('اكتبها في التعليقات 👇')}` },
'''
