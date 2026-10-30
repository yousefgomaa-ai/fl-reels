NAME = 'إيرلينغ هالاند'
BADGES = ['⚽ 36 هدفًا في موسم', '🏆 الثلاثية 2023']
CLUBS = [8531, 9917, 10013, 9789, 8456, 8492]
CONSTS = "const SAL = 'rgba(204,0,51,.45)', BVB = 'rgba(253,225,0,.4)', MCI = 'rgba(108,171,221,.5)', NOR = 'rgba(186,12,47,.5)';"
SC = r'''
  { club: -1, html: '' },
  { club: 0, glow: '#2a1010', html: `<div class="yrs" style="font-size:110px">2000</div><div class="vs"><img src="${L(8531)}"></div><div class="ttl">وُلد في ليدز</div>${SUB('ونشأ في براين النرويجية')}` },
  { club: 1, glow: '#0c1a3a', html: `<div class="vs"><img src="${L(9917)}"><span class="x">←</span><img src="${L(10013)}"></div><div class="ttl">من مولده إلى سالزبورغ</div>` },
  { club: 2, glow: '#3a0c14', html: head(10013, 'سالزبورغ', '2019', SAL) + `<div class="chips">${chip(29, 'هدفًا', 29)}${chip(27, 'مباراة', 27)}</div>` },
  { ph: 1, club: 3, glow: '#2e2a0c', html: head(9789, '<span style="font-size:84px">بوروسيا دورتموند</span>', '2020 - 2022', BVB) + `<div class="chips">${chip(86, 'هدفًا', 86)}${chip(89, 'مباراة', 89)}</div><div class="rows">${row('🏆', 'كأس ألمانيا', '✓')}</div>` },
  { club: 4, glow: '#0c2a3a', html: `<div class="yrs" style="font-size:90px">صيف 2022</div><div class="vs"><img src="${L(9789)}"><span class="x">←</span><img src="${L(8456)}"></div><div class="ttl">إلى مانشستر سيتي</div>` },
  { ph: 3, club: 4, glow: '#0c2a3a', html: `<div class="ttl" style="font-size:66px">في موسمه الأول</div><div class="chips">${chip(36, 'هدفًا', 36)}</div>${SUB('رقم قياسي في الدوري الإنجليزي')}` },
  { ph: 3, club: 4, glow: '#0c2a3a', html: `<div class="yrs" style="font-size:120px">2023</div><div class="ttl">الثلاثية</div><div class="rows">${row('🏆', 'الدوري الإنجليزي', '✓')}${row('🏆', 'كأس إنجلترا', '✓')}${row('🏆', 'دوري أبطال أوروبا', '✓')}</div>` },
  { ph: 3, club: 4, glow: '#0c2a3a', html: `<div class="ttl">مع سيتي</div><div class="rows">${row('🏆', 'الدوري الإنجليزي', '×2')}${row('🏆', 'كأس إنجلترا', '×2')}${row('🏆', 'كأس الرابطة', '2026')}</div>` },
  { ph: 3, club: 4, glow: '#0c2a3a', html: head(8456, 'مانشستر سيتي', 'منذ 2022', MCI) + `<div class="chips">${chip(175, 'هدفًا', 175)}${chip(209, 'مباراة', 209)}</div>` },
  { ph: 3, club: 4, glow: '#0c2a3a', html: `<div class="chips">${chip(50, 'هدفًا', 50)}</div><div class="ttl" style="font-size:66px">الأسرع إليها</div>${SUB('في دوري أبطال أوروبا')}` },
  { ph: 2, club: 5, glow: '#3a1010', html: head(8492, 'منتخب النرويج', 'كأس العالم 2026', NOR) + `<div class="rows">${row('🌍', 'أول مشاركة منذ 1998', '✓')}</div><div class="chips">${chip(7, 'أهداف', 7)}</div>` },
  { ph: 2, club: 5, glow: '#3a1010', html: `<div class="ttl" style="font-size:72px">دور الستة عشر</div><div class="rows">${row('⚽', 'هدفان أمام البرازيل', '✓')}${row('🌍', 'ربع النهائي لأول مرة', '✓')}</div>` },
  { ph: 2, club: 5, glow: '#3a1010', html: `<div class="ttl" style="font-size:66px">الهداف التاريخي للنرويج</div><div class="chips">${chip(65, 'هدفًا', 65)}${chip(59, 'مباراة', 59)}</div>` },
  { club: 5, glow: '#2a1a5e', html: `<div class="vs" style="gap:14px;flex-wrap:wrap;justify-content:center">${CLUBS.map((id) => `<img src="${L(id)}" style="width:110px;height:110px">`).join('<span class="x" style="font-size:40px">←</span>')}</div><div class="ttl" style="margin-top:30px">أي محطة هي<br>الأجمل في رأيك؟</div>${SUB('اكتبها في التعليقات 👇')}` },
'''
