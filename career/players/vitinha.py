NAME = 'فيتينيا'
BADGES = ['🏆 دوري الأبطال مرتين', '🥉 ثالث الكرة الذهبية 2025']
CLUBS = [9773, 8602, 9847, 8361]
CONSTS = "const POR = 'rgba(0,70,160,.45)', WOL = 'rgba(253,185,19,.35)', PSG = 'rgba(0,40,110,.5)', PT = 'rgba(200,16,46,.4)';"
SC = r'''
  { club: -1, html: '' },
  { club: 0, glow: '#0c1e3a', html: head(9773, 'أكاديمية بورتو', 'مولود 2000', POR) + `<div class="rows">${row('🏆', 'دوري أبطال أوروبا للشباب', '✓')}</div>` },
  { club: 1, glow: '#3a2a0c', html: `<div class="vs"><img src="${L(9773)}"><span class="x">←</span><img src="${L(8602)}"></div><div class="ttl">إعارة إلى وولفرهامبتون</div><div class="yrs">2020 - 2021</div>` },
  { club: 0, glow: '#0c1e3a', html: head(9773, 'العودة إلى بورتو', '2021 - 2022', POR) + `<div class="rows">${row('🏆', 'الدوري البرتغالي', '✓')}${row('🏆', 'كأس البرتغال', '✓')}</div>` },
  { club: 2, glow: '#0c1640', html: `<div class="yrs" style="font-size:90px">صيف 2022</div><div class="vs"><img src="${L(9773)}"><span class="x">←</span><img src="${L(9847)}"></div><div class="ttl">إلى باريس سان جيرمان</div>` },
  { ph: 1, club: 2, glow: '#0c1640', html: head(9847, 'الدوري الفرنسي', '<span dir="ltr">2023 • 2024 • 2025 • 2026</span>', PSG) + `<div class="rows">${row('🏆', 'أربع مرات متتالية', '×4')}</div>` },
  { club: 2, glow: '#0c1640', html: `<div class="yrs" style="font-size:90px">2025</div><div class="ttl">🏆 دوري أبطال أوروبا</div>${SUB('الأول في تاريخ باريس')}` },
  { club: 2, glow: '#2a2a0c', html: `<div class="ttl" style="font-size:140px">🥉</div><div class="ttl">الكرة الذهبية 2025</div>${SUB('المركز الثالث')}` },
  { club: 2, glow: '#0c1640', html: `<div class="yrs" style="font-size:90px">2026</div><div class="ttl">🏆 دوري الأبطال مرة ثانية</div>${SUB('على حساب آرسنال في النهائي')}` },
  { ph: 2, club: 3, glow: '#3a0c14', html: head(8361, 'منتخب البرتغال', '2025', PT) + `<div class="rows">${row('🏆', 'دوري الأمم الأوروبية', '✓')}</div>` },
  { club: 2, glow: '#0c1640', html: head(9847, 'باريس سان جيرمان', 'منذ 2022', PSG) + `<div class="chips">${chip('+200', 'مباراة')}</div>` },
  { club: 3, glow: '#2a1a5e', html: `<div class="vs" style="gap:14px;flex-wrap:wrap;justify-content:center">${CLUBS.map((id) => `<img src="${L(id)}" style="width:100px;height:100px">`).join('<span class="x" style="font-size:40px">←</span>')}</div><div class="ttl" style="margin-top:30px">أي محطة هي<br>الأجمل في رأيك؟</div>${SUB('اكتبها في التعليقات 👇')}` },
'''
