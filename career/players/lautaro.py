NAME = 'لاوتارو مارتينيز'
BADGES = ['🏆 بطل العالم 2022', '©️ قائد إنتر']
CLUBS = [10080, 8636, 6706]
CONSTS = "const RAC = 'rgba(110,180,230,.4)', INT = 'rgba(0,80,180,.45)', ARG = 'rgba(117,170,219,.45)';"
SC = r'''
  { club: -1, html: '' },
  { club: 0, glow: '#0c1e3a', html: head(10080, 'راسينغ كلوب', 'مولود 1997', RAC) },
  { club: 1, glow: '#0c1640', html: `<div class="chips">${chip(27, 'هدفًا مع راسينغ', 27)}</div><div class="yrs" style="font-size:90px">صيف 2018</div><div class="vs"><img src="${L(10080)}"><span class="x">←</span><img src="${L(8636)}"></div>` },
  { club: 1, glow: '#0c1640', html: head(8636, 'إنتر', '2021', INT) + `<div class="rows">${row('🏆', 'الدوري الإيطالي', '✓')}</div>` },
  { ph: 2, club: 2, glow: '#0c2a3a', html: head(6706, 'كأس العالم', 'قطر 2022', ARG) + `<div class="rows">${row('🏆', 'بطل العالم مع الأرجنتين', '✓')}</div>` },
  { ph: 1, club: 1, glow: '#0c1640', html: `<div class="ttl">موسمه الأول قائدًا</div><div class="rows">${row('🏆', 'الدوري الإيطالي', '✓')}${row('👟', 'هداف الدوري', '<b data-n="24">24</b>')}</div>` },
  { club: 2, glow: '#0c2a3a', html: head(6706, 'كوبا أمريكا', '2024', ARG) + `<div class="rows">${row('👟', 'هداف البطولة', '✓')}${row('⚽', 'هدف الفوز في النهائي', '✓')}</div>` },
  { club: 1, glow: '#0c1640', html: `<div class="ttl">الهداف التاريخي لإنتر<br>في دوري الأبطال</div>` },
  { club: 1, glow: '#0c1640', html: `<div class="yrs" style="font-size:90px">2026</div><div class="ttl">🏆 الدوري الإيطالي</div>${SUB('للمرة الثالثة')}` },
  { club: 1, glow: '#0c1640', html: head(8636, 'إنتر', 'منذ 2018', INT) + `<div class="chips">${chip(181, 'هدفًا', 181)}</div>${SUB('ثالث هدافي النادي عبر التاريخ')}` },
  { club: 2, glow: '#0c2a3a', html: `<div class="ttl">مع منتخب الأرجنتين</div><div class="chips">${chip(42, 'هدفًا', 42)}</div><div class="rows">${row('🥈', 'نهائي كأس العالم 2026', '✓')}</div>` },
  { club: 1, glow: '#0c1640', html: `<div class="vs"><img src="${L(10080)}"><span class="x">←</span><img src="${L(8636)}"></div><div class="ttl">من راسينغ إلى قيادة إنتر</div>` },
  { club: 2, glow: '#2a1a5e', html: `<div class="vs" style="gap:14px;flex-wrap:wrap;justify-content:center">${CLUBS.map((id) => `<img src="${L(id)}" style="width:100px;height:100px">`).join('<span class="x" style="font-size:40px">←</span>')}</div><div class="ttl" style="margin-top:30px">أي محطة هي<br>الأجمل في رأيك؟</div>${SUB('اكتبها في التعليقات 👇')}` },
'''
