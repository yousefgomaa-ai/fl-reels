NAME = 'عمر مرموش'
BADGES = ['🏆 كأس الرابطة', '🏆 كأس الاتحاد', '⚽ 12 لمصر']
CLUBS = [205190, 8721, 8152, 10269, 9810, 8456, 8586, 10255]
CONSTS = "const WOB = 'rgba(101,179,46,.45)', SGE = 'rgba(225,0,15,.45)', MCI = 'rgba(108,171,221,.5)', EGY = 'rgba(200,16,46,.45)', GRY = 'rgba(255,255,255,.25)';"
SC = r'''
  { club: -1, html: '' },
  { ph: 1, club: 1, glow: '#10301a', html: `<div class="yrs" style="font-size:110px">2017</div><div class="vs"><img src="${L(205190)}"><span class="x">←</span><img src="${L(8721)}"></div><div class="ttl">من القاهرة إلى ألمانيا</div>${SUB('وعمره 18 عامًا')}` },
  { ph: 1, club: 2, glow: '#2a1a10', html: head(8152, 'سانت باولي', '2021 • إعارة', GRY) + `<div class="chips">${chip(7, 'أهداف', 7)}${chip(21, 'مباراة', 21)}</div>${SUB('في نصف موسم')}` },
  { club: 3, glow: '#3a0c0c', html: head(10269, 'شتوتجارت', '2021-2022 • إعارة', SGE) + `<div class="chips">${chip(3, 'أهداف', 3)}${chip(5, 'تمريرات حاسمة', 5)}</div>` },
  { club: 3, glow: '#10301a', html: head(8721, 'فولفسبورج', '2022-2023', WOB) + `<div class="chips">${chip(6, 'أهداف', 6)}${chip(36, 'مباراة', 36)}</div>` },
  { ph: 2, club: 4, glow: '#3a0c0c', html: head(9810, 'آينتراخت فرانكفورت', 'موسم 2023-2024', SGE) + `<div class="chips">${chip(17, 'هدفًا', 17)}${chip(41, 'مباراة', 41)}</div>` },
  { ph: 2, club: 4, glow: '#3a0c0c', html: `<div class="yrs" style="font-size:90px">2024-2025</div><div class="ttl">النصف الأول من الموسم</div><div class="chips">${chip(20, 'هدفًا', 20)}${chip(13, 'تمريرة حاسمة', 13)}${chip(26, 'مباراة', 26)}</div>` },
  { ph: 2, club: 4, glow: '#3a0c0c', html: `<div class="ttl">في الدوري الألماني وحده</div><div class="chips">${chip(15, 'هدفًا', 15)}${chip(9, 'تمريرات حاسمة', 9)}</div>` },
  { ph: 3, club: 5, glow: '#10284a', html: head(8456, 'مانشستر سيتي', 'يناير 2025', MCI) + `<div class="rows">${row('⚽', 'هاتريك في مرمى نيوكاسل', '✓')}</div>` },
  { ph: 3, club: 5, glow: '#10284a', html: `<div class="yrs" style="font-size:90px">2025-2026</div><div class="rows">${row('🏆', 'كأس الرابطة الإنجليزية', '✓')}${row('🏆', 'كأس الاتحاد الإنجليزي', '✓')}${row('⚽', 'هدفان في نصف نهائي الرابطة', '✓')}</div>` },
  { ph: 3, club: 5, glow: '#10284a', html: head(8456, 'مانشستر سيتي', '2025 - 2026', MCI) + `<div class="chips">${chip(16, 'هدفًا', 16)}${chip(62, 'مباراة', 62)}</div>` },
  { club: 6, glow: '#101a44', html: head(8586, 'توتنهام', 'منذ صيف 2026 • إعارة', 'rgba(19,34,87,.6)') },
  { ph: 4, club: 7, glow: '#3a1010', html: head(10255, 'منتخب مصر', '', EGY) + `<div class="chips">${chip(12, 'هدفًا', 12)}${chip(58, 'مباراة', 58)}</div><div class="rows">${row('🌍', 'كأس العالم 2026', '✓')}${row('🏆', 'أمم أفريقيا', '3 مشاركات')}</div>` },
  { club: 7, glow: '#2a1a5e', html: `<div class="vs" style="gap:12px;flex-wrap:wrap;justify-content:center">${CLUBS.map((id) => `<img src="${L(id)}" style="width:104px;height:104px">`).join('<span class="x" style="font-size:36px">←</span>')}</div><div class="ttl" style="margin-top:30px">أي محطة هي<br>الأجمل في رأيك؟</div>${SUB('اكتبها في التعليقات 👇')}` },
'''
