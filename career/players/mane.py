NAME = 'ساديو ماني'
BADGES = ['🏆 أبطال أوروبا 2019', '🌍 بطل أفريقيا']
CLUBS = [8550, 10013, 8466, 8650, 9823, 101918, 6395]
CONSTS = "const SAL = 'rgba(204,0,51,.45)', SOU = 'rgba(215,25,32,.45)', LIV = 'rgba(200,16,46,.5)', NAS = 'rgba(255,214,0,.4)', SEN = 'rgba(0,133,63,.5)';"
SC = r'''
  { club: -1, html: '' },
  { club: 0, glow: '#1a1a3a', html: `<div class="yrs" style="font-size:110px">1992</div><div class="vs"><img src="${L(6395)}"><span class="x">←</span><img src="${L(8550)}"></div><div class="ttl">من السنغال إلى ميتز</div>${SUB('بداية المشوار في أوروبا')}` },
  { club: 1, glow: '#3a0c14', html: head(10013, 'سالزبورغ', '2012 - 2014', SAL) + `<div class="chips">${chip(45, 'هدفًا', 45)}</div><div class="rows">${row('🏆', 'الدوري والكأس', '✓')}</div>` },
  { club: 2, glow: '#3a0c10', html: head(8466, 'ساوثهامبتون', '2014 - 2016', SOU) + `<div class="rows">${row('⚡', 'أسرع هاتريك في الدوري الإنجليزي', '<span dir="ltr">2:56</span>')}</div>${SUB('دقيقتان و56 ثانية')}` },
  { ph: 1, club: 3, glow: '#3a0c10', html: `<div class="yrs" style="font-size:90px">صيف 2016</div><div class="vs"><img src="${L(8466)}"><span class="x">←</span><img src="${L(8650)}"></div><div class="ttl">إلى ليفربول</div>` },
  { ph: 1, club: 3, glow: '#3a0c10', html: `<div class="ttl">مع ليفربول</div><div class="rows">${row('🏆', 'دوري أبطال أوروبا', '2019')}${row('🏆', 'الدوري الإنجليزي', '2020')}</div>${SUB('بعد انتظار 30 عامًا')}` },
  { ph: 1, club: 3, glow: '#3a0c10', html: `<div class="ttl" style="font-size:66px">هداف الدوري الإنجليزي</div><div class="chips">${chip(22, 'هدفًا', 22)}</div>${SUB('لقب مشترك')}` },
  { ph: 1, club: 3, glow: '#3a0c10', html: head(8650, 'ليفربول', '2016 - 2022', LIV) + `<div class="chips">${chip(120, 'هدفًا', 120)}${chip(269, 'مباراة', 269)}</div>` },
  { club: 4, glow: '#3a0c14', html: `<div class="vs"><img src="${L(9823)}"><span class="x">←</span><img src="${L(101918)}"></div><div class="rows">${row('🏆', 'الدوري الألماني مع بايرن', '✓')}</div>${SUB('ثم إلى النصر السعودي')}` },
  { ph: 3, club: 5, glow: '#3a320c', html: head(101918, 'النصر', 'منذ 2023', NAS) + `<div class="rows">${row('🏆', 'الدوري السعودي', '2026')}${row('⚽', 'سجّل في مباراة التتويج', '✓')}</div>` },
  { ph: 2, club: 6, glow: '#0c3a1e', html: head(6395, 'منتخب السنغال', '', SEN) + `<div class="rows">${row('🏆', 'كأس الأمم الأفريقية', '✓')}${row('🎯', 'ركلة الترجيح الحاسمة في النهائي', '✓')}</div>` },
  { ph: 2, club: 6, glow: '#3a2a10', html: `<div class="rows">${row('🌍', 'أفضل لاعب في أفريقيا', '×2')}${row('⭐', 'الكرة الذهبية', 'المركز 2')}</div>` },
  { ph: 2, club: 6, glow: '#0c3a1e', html: `<div class="ttl" style="font-size:72px">بعد كأس العالم الأخيرة</div>${SUB('اعتزل اللعب الدولي')}` },
  { club: 6, glow: '#2a1a5e', html: `<div class="vs" style="gap:12px;flex-wrap:wrap;justify-content:center">${CLUBS.map((id) => `<img src="${L(id)}" style="width:96px;height:96px">`).join('<span class="x" style="font-size:36px">←</span>')}</div><div class="ttl" style="margin-top:30px">أي محطة هي<br>الأجمل في رأيك؟</div>${SUB('اكتبها في التعليقات 👇')}` },
'''
