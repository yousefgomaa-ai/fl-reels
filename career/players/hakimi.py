NAME = 'أشرف حكيمي'
BADGES = ['🏆 أبطال أوروبا ×3', '©️ قائد المغرب']
CLUBS = [8633, 9789, 8636, 9847, 6262]
CONSTS = "const RM = 'rgba(254,190,16,.35)', BVB = 'rgba(253,225,0,.4)', INT = 'rgba(0,82,159,.55)', PSG = 'rgba(0,65,112,.6)', MAR = 'rgba(193,39,45,.5)';"
SC = r'''
  { club: -1, html: '' },
  { club: 0, glow: '#2e2a10', html: `<div class="yrs" style="font-size:110px">1998</div><div class="vs"><img src="${L(8633)}"></div><div class="ttl">ابن أكاديمية ريال مدريد</div>${SUB('وُلد في مدريد لأبوين مغربيين')}` },
  { club: 0, glow: '#2e2a10', html: head(8633, 'ريال مدريد', '2017 - 2018', RM) + `<div class="rows">${row('🏆', 'دوري أبطال أوروبا', '2018')}</div>${SUB('وعمره 19 عامًا')}` },
  { club: 1, glow: '#2e2a0c', html: head(9789, '<span style="font-size:84px">بوروسيا دورتموند</span>', '2018 - 2020 • إعارة', BVB) + `<div class="chips">${chip(12, 'هدفًا', 12)}${chip(17, 'تمريرة حاسمة', 17)}</div>` },
  { club: 2, glow: '#0c1a3a', html: head(8636, 'إنتر', '2020 - 2021', INT) + `<div class="rows">${row('🏆', 'الدوري الإيطالي', '✓')}</div>` },
  { ph: 1, club: 3, glow: '#0c1a3a', html: `<div class="yrs" style="font-size:90px">صيف 2021</div><div class="vs"><img src="${L(8636)}"><span class="x">←</span><img src="${L(9847)}"></div><div class="ttl">إلى باريس سان جيرمان</div>` },
  { ph: 1, club: 3, glow: '#0c1a3a', html: `<div class="ttl">مع باريس</div><div class="rows">${row('🏆', 'الدوري الفرنسي', '×5')}${row('🔁', 'متتالية', '2022 - 2026')}</div>` },
  { ph: 1, club: 3, glow: '#0c1a3a', html: `<div class="yrs" style="font-size:120px">2025</div><div class="ttl" style="font-size:66px">نهائي دوري أبطال أوروبا</div><div class="vs"><img src="${L(9847)}"><span class="x">×</span><img src="${L(8636)}"></div><div class="rows">${row('⚽', 'سجّل في النهائي', '✓')}${row('🏆', 'أول لقب في تاريخ باريس', '✓')}</div>` },
  { ph: 1, club: 3, glow: '#0c1a3a', html: `<div class="yrs" style="font-size:120px">2026</div><div class="ttl" style="font-size:66px">دوري أبطال أوروبا مرة ثانية</div><div class="rows">${row('🏆', 'لقبان متتاليان', '✓')}${row('🎯', 'بالترجيح أمام آرسنال', '✓')}</div>` },
  { ph: 3, club: 4, glow: '#3a1010', html: `<div class="yrs" style="font-size:120px">2025</div><div class="rows">${row('🌍', 'أفضل لاعب في أفريقيا', '✓')}${row('⭐', 'الكرة الذهبية', 'المركز 6')}</div>` },
  { ph: 1, club: 3, glow: '#0c1a3a', html: head(9847, '<span style="font-size:84px">باريس سان جيرمان</span>', 'منذ 2021', PSG) + `<div class="chips">${chip(28, 'هدفًا', 28)}${chip(41, 'تمريرة حاسمة', 41)}${chip(219, 'مباراة', 219)}</div>` },
  { ph: 2, club: 4, glow: '#3a1010', html: head(6262, 'منتخب المغرب', 'كأس العالم 2022', MAR) + `<div class="rows">${row('🎯', 'ركلة الحسم أمام إسبانيا', '✓')}${row('🌍', 'نصف النهائي', '✓')}</div>` },
  { ph: 3, club: 4, glow: '#3a1010', html: `<div class="ttl" style="font-size:72px">كأس العالم 2026</div><div class="rows">${row('©️', 'قائد المنتخب', '✓')}${row('🌍', 'ربع النهائي', '✓')}</div><div class="chips">${chip(12, 'هدفًا', 12)}${chip(92, 'مباراة', 92)}</div>` },
  { club: 4, glow: '#2a1a5e', html: `<div class="vs" style="gap:14px;flex-wrap:wrap;justify-content:center">${CLUBS.map((id) => `<img src="${L(id)}" style="width:110px;height:110px">`).join('<span class="x" style="font-size:40px">←</span>')}</div><div class="ttl" style="margin-top:30px">أي محطة هي<br>الأجمل في رأيك؟</div>${SUB('اكتبها في التعليقات 👇')}` },
'''
