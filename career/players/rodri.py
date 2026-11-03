NAME = 'رودري'
BADGES = ['🏆 بطل العالم 2026', '⭐ الكرة الذهبية 2024']
CLUBS = [10205, 9906, 8456, 8634, 6720]
CONSTS = "const VIL = 'rgba(255,230,0,.35)', CITY = 'rgba(108,171,221,.45)', BAR = 'rgba(165,0,68,.45)', ESP = 'rgba(198,11,30,.45)';"
SC = r'''
  { club: -1, html: '' },
  { club: 0, glow: '#2e2a0c', html: `<div class="yrs" style="font-size:110px">1996</div><div class="vs"><img src="${L(10205)}"></div><div class="ttl">من مدريد إلى فياريال</div>${SUB('بداية المسيرة الاحترافية')}` },
  { club: 2, glow: '#0c2a44', html: `<div class="yrs" style="font-size:90px">صيف 2019</div><div class="vs"><img src="${L(9906)}"><span class="x">←</span><img src="${L(8456)}"></div><div class="ttl">إلى مانشستر سيتي</div>${SUB('بعد موسم مع أتلتيكو مدريد')}` },
  { ph: 1, club: 2, glow: '#0c2a44', html: head(8456, 'مانشستر سيتي', 'الدوري الإنجليزي', CITY) + `<div class="chips">${chip(4, 'ألقاب متتالية', 4)}</div>` },
  { club: 2, glow: '#3a2a10', html: `<div class="yrs" style="font-size:120px">2023</div><div class="rows">${row('⚽', 'هدف الفوز في نهائي الأبطال', '✓')}${row('🏆', 'الثلاثية مع السيتي', '✓')}</div>` },
  { ph: 2, club: 4, glow: '#3a0c0c', html: head(6720, 'منتخب إسبانيا', 'يورو 2024', ESP) + `<div class="rows">${row('🏆', 'بطل أوروبا', '✓')}${row('⭐', 'أفضل لاعب في البطولة', '✓')}</div>` },
  { club: 2, glow: '#3a2a10', html: `<div class="ttl" style="font-size:140px">⭐</div><div class="ttl">الكرة الذهبية</div><div class="yrs">2024</div>${SUB('ثم إصابة قوية في الركبة')}` },
  { club: 2, glow: '#0c2a44', html: head(8456, 'مانشستر سيتي', '2019 - 2026', CITY) + `<div class="chips">${chip(28, 'هدفًا', 28)}${chip(30, 'تمريرة حاسمة', 30)}${chip(298, 'مباراة', 298)}</div>` },
  { club: 4, glow: '#3a2a10', html: `<div class="yrs" style="font-size:120px">2026</div><div class="vs"><img src="${L(6720)}"></div><div class="ttl">بطل العالم قائدًا 🏆</div>${SUB('وأفضل لاعب في البطولة')}` },
  { club: 3, glow: '#2a0c1e', html: `<div class="yrs" style="font-size:90px">صيف 2026</div><div class="vs"><img src="${L(8456)}"><span class="x">←</span><img src="${L(8634)}"></div><div class="ttl">إلى برشلونة</div>${SUB('بعد 7 مواسم في مانشستر')}` },
  { club: 4, glow: '#3a0c0c', html: head(6720, 'منتخب إسبانيا', 'منذ 2018', ESP) + `<div class="chips">${chip(5, 'أهداف', 5)}${chip(74, 'مباراة', 74)}</div>` },
  { club: 4, glow: '#3a0c0c', html: `<div class="ttl">مع إسبانيا أيضًا</div><div class="rows">${row('🏆', 'دوري الأمم الأوروبية', '✓')}</div>` },
  { club: 4, glow: '#2a1a5e', html: `<div class="vs" style="gap:14px;flex-wrap:wrap;justify-content:center">${CLUBS.map((id) => `<img src="${L(id)}" style="width:100px;height:100px">`).join('<span class="x" style="font-size:40px">←</span>')}</div><div class="ttl" style="margin-top:30px">أي محطة هي<br>الأجمل في رأيك؟</div>${SUB('اكتبها في التعليقات 👇')}` },
'''
