NAME = 'كريستيانو رونالدو'
BADGES = ['🏆 الكرة الذهبية ×5', '⭐ أبطال أوروبا ×5', '⚽ +950']
CLUBS = [9768, 10260, 8633, 9885, 101918, 8361]
CONSTS = "const MU = 'rgba(218,41,28,.5)', RM = 'rgba(254,190,16,.35)', JUV = 'rgba(255,255,255,.25)', NAS = 'rgba(250,200,20,.4)', POR = 'rgba(200,16,46,.5)';"
SC = r'''
  { club: -1, html: '' },
  { ph: 1, club: 1, glow: '#2a1010', html: `<div class="yrs" style="font-size:90px">صيف 2003</div><div class="vs"><img src="${L(9768)}"><span class="x">←</span><img src="${L(10260)}"></div><div class="ttl">من لشبونة إلى مانشستر</div>${SUB('وعمره 18 عامًا')}` },
  { ph: 2, club: 1, glow: '#3a0c0c', html: head(10260, 'مانشستر يونايتد', 'موسم 2007-2008', MU) + `<div class="chips">${chip(31, 'في الدوري', 31)}${chip(42, 'في كل البطولات', 42)}</div><div class="rows">${row('🏆', 'دوري أبطال أوروبا', '✓')}${row('⭐', 'الكرة الذهبية', 'الأولى')}</div>` },
  { ph: 1, club: 1, glow: '#3a0c0c', html: head(10260, 'مانشستر يونايتد', '2003 - 2009', MU) + `<div class="chips">${chip(107, 'أهداف', 107)}${chip(3, 'ألقاب الدوري', 3)}</div>` },
  { ph: 3, club: 2, glow: '#2e2a10', html: `<div class="yrs" style="font-size:90px">صيف 2009</div><div class="vs"><img src="${L(10260)}"><span class="x">←</span><img src="${L(8633)}"></div><div class="ttl">أغلى صفقة في العالم وقتها</div>` },
  { ph: 3, club: 2, glow: '#2e2a10', html: head(8633, 'ريال مدريد', 'موسم 2014-2015', RM) + `<div class="chips">${chip(61, 'هدفًا', 61)}${chip(48, 'في الدوري', 48)}</div>` },
  { ph: 11, club: 2, glow: '#2e2a10', html: `<div class="ttl">مع ريال مدريد</div><div class="rows">${row('🏆', 'دوري أبطال أوروبا', '×4')}${row('🔁', 'ثلاث مرات متتالية', '2016-2018')}${row('⭐', 'الكرة الذهبية', '×4')}</div>` },
  { ph: 3, club: 2, glow: '#2e2a10', html: head(8633, 'ريال مدريد', '2009 - 2018', RM) + `<div class="chips">${chip(450, 'هدفًا', 450)}${chip(438, 'مباراة', 438)}</div><div class="rows">${row('🥇', 'الهداف التاريخي للنادي', '✓')}</div>` },
  { ph: 4, club: 3, glow: '#1a1a1a', html: head(9885, 'يوفنتوس', '2018 - 2021', JUV) + `<div class="chips">${chip(101, 'هدف', 101)}${chip(134, 'مباراة', 134)}</div><div class="rows">${row('🏆', 'الدوري الإيطالي', '×2')}</div>` },
  { ph: 1, club: 3, glow: '#3a0c0c', html: head(10260, 'العودة إلى يونايتد', '2021-2022', MU) + `<div class="chips">${chip(24, 'هدفًا في موسمه الأول', 24)}</div>` },
  { ph: 6, club: 4, glow: '#2e2a10', html: head(101918, 'النصر', 'منذ يناير 2023', NAS) + `<div class="chips">${chip(35, 'في الدوري 2023-2024', 35)}</div><div class="rows">${row('📈', 'رقم قياسي للدوري السعودي', '✓')}</div>` },
  { ph: 7, club: 4, glow: '#2e2a10', html: `<div class="yrs" style="font-size:90px">2025-2026</div><div class="ttl">🏆 الدوري السعودي</div><div class="chips">${chip(28, 'هدفًا', 28)}</div><div class="rows">${row('⚽', 'هدفان في مباراة التتويج', '✓')}</div>` },
  { ph: 6, club: 4, glow: '#2e2a10', html: head(101918, 'النصر', 'حتى الآن', NAS) + `<div class="chips">${chip(134, 'هدفًا', 134)}${chip(159, 'مباراة', 159)}</div>` },
  { ph: 8, club: 5, glow: '#3a0c14', html: head(8361, 'منتخب البرتغال', '', POR) + `<div class="rows">${row('🥇', 'الهداف التاريخي للمنتخبات', '✓')}${row('🏆', 'أمم أوروبا', '2016')}${row('🏆', 'دوري الأمم الأوروبية', '×2')}</div>` },
  { ph: 9, club: 5, glow: '#3a0c14', html: `<div class="ttl" style="font-size:72px">كأس العالم 2026</div><div class="yrs" style="font-size:220px;line-height:1"><b data-n="6">6</b></div><div class="ttl" style="font-size:54px">أول لاعب يسجّل في 6 نسخ</div>` },
  { ph: 3, club: 5, glow: '#14204a', html: `<div class="ttl" style="font-size:150px">⭐</div><div class="ttl">دوري أبطال أوروبا</div><div class="rows">${row('🥇', 'الهداف التاريخي للبطولة', '✓')}${row('🏆', 'ألقاب', '×5')}</div>` },
  { club: 5, glow: '#2a1a5e', html: `<div class="vs" style="gap:14px;flex-wrap:wrap;justify-content:center">${CLUBS.map((id) => `<img src="${L(id)}" style="width:118px;height:118px">`).join('<span class="x" style="font-size:40px">←</span>')}</div><div class="ttl" style="margin-top:30px">أي محطة هي<br>الأجمل في رأيك؟</div>${SUB('اكتبها في التعليقات 👇')}` },
'''
