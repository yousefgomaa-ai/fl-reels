NAME = 'لامين يامال'
BADGES = ['🏆 بطل العالم 2026', '⭐ جائزة كوبا ×3']
CLUBS = [8634, 6720]
CONSTS = "const BAR = 'rgba(165,0,68,.45)', ESP = 'rgba(198,11,30,.45)';"
SC = r'''
  { club: -1, html: '' },
  { club: 0, glow: '#2a0c1e', html: `<div class="yrs" style="font-size:110px">2007</div><div class="vs"><img src="${L(8634)}"></div><div class="ttl">من ماتارو<br>إلى لا&nbsp;ماسيا</div>${SUB('في السابعة من عمره')}` },
  { club: 0, glow: '#2a0c1e', html: head(8634, 'برشلونة', 'أبريل 2023', BAR) + `<div class="rows">${row('⚡', 'أول مباراة وعمره', '15 عامًا')}${row('🏆', 'أول لقب للدوري', '✓')}</div>` },
  { ph: 2, club: 1, glow: '#3a0c0c', html: head(6720, 'منتخب إسبانيا', 'يورو 2024', ESP) + `<div class="rows">${row('🏆', 'بطل أوروبا', '✓')}${row('⚽', 'أصغر هداف في تاريخها', '✓')}</div>` },
  { ph: 1, club: 0, glow: '#2a0c1e', html: `<div class="ttl" style="font-size:72px">الثلاثية المحلية</div><div class="rows">${row('🏆', 'الدوري', '✓')}${row('🏆', 'الكأس', '✓')}${row('🏆', 'السوبر', '✓')}</div>${SUB('موسم 2024 - 2025')}` },
  { club: 0, glow: '#3a2a10', html: `<div class="yrs" style="font-size:120px">2025</div><div class="rows">${row('⭐', 'الكرة الذهبية', 'المركز 2')}${row('👕', 'قميص برشلونة', 'رقم 10')}</div>` },
  { club: 0, glow: '#2a0c1e', html: `<div class="ttl">الموسم الماضي</div><div class="rows">${row('🏆', 'الدوري الإسباني', '×3')}${row('🏆', 'السوبر الإسباني', '✓')}${row('⭐', 'أفضل لاعب في الدوري', '✓')}</div>` },
  { ph: 3, club: 1, glow: '#3a2a10', html: `<div class="yrs" style="font-size:120px">2026</div><div class="vs"><img src="${L(6720)}"></div><div class="ttl">بطل العالم 🏆</div>${SUB('بالفوز على الأرجنتين في النهائي')}` },
  { club: 0, glow: '#3a2a10', html: `<div class="ttl">جائزة كوبا</div><div class="chips">${chip(3, 'مرات متتالية', 3)}</div>${SUB('أول لاعب يحققها في التاريخ')}` },
  { club: 0, glow: '#2a0c1e', html: head(8634, 'برشلونة', 'منذ 2023', BAR) + `<div class="chips">${chip(61, 'هدفًا', 61)}${chip(56, 'تمريرة حاسمة', 56)}${chip(165, 'مباراة', 165)}</div>` },
  { club: 1, glow: '#3a0c0c', html: head(6720, 'منتخب إسبانيا', 'منذ 2023', ESP) + `<div class="chips">${chip(11, 'هدفًا', 11)}${chip(12, 'تمريرة حاسمة', 12)}${chip(37, 'مباراة', 37)}</div>` },
  { club: 1, glow: '#2a1a5e', html: `<div class="vs" style="gap:24px;justify-content:center">${CLUBS.map((id) => `<img src="${L(id)}" style="width:150px;height:150px">`).join('<span class="x" style="font-size:40px">←</span>')}</div><div class="ttl" style="margin-top:30px">أي لحظة هي<br>الأجمل في رأيك؟</div>${SUB('اكتبها في التعليقات 👇')}` },
'''
