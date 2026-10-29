NAME = 'كيليان مبابي'
BADGES = ['🏆 مونديال 2018', '🥇 هداف المونديال', '⚽ 67 لفرنسا']
CLUBS = [9829, 9847, 8633, 6723]
CONSTS = "const MON = 'rgba(226,0,26,.45)', PSG = 'rgba(0,65,112,.6)', RM = 'rgba(254,190,16,.35)', FRA = 'rgba(0,35,149,.55)';"
SC = r'''
  { club: -1, html: '' },
  { club: 0, glow: '#3a0c10', html: `<div class="yrs" style="font-size:110px">2015</div><div class="vs"><img src="${L(9829)}"></div><div class="ttl">البداية مع موناكو</div>${SUB('وعمره 16 عامًا')}` },
  { club: 0, glow: '#3a0c10', html: head(9829, 'موناكو', '2015 - 2017', MON) + `<div class="chips">${chip(27, 'هدفًا', 27)}${chip(60, 'مباراة', 60)}</div><div class="rows">${row('🏆', 'الدوري الفرنسي', '2017')}</div>` },
  { ph: 1, club: 1, glow: '#0c1a3a', html: `<div class="yrs" style="font-size:90px">صيف 2017</div><div class="vs"><img src="${L(9829)}"><span class="x">←</span><img src="${L(9847)}"></div><div class="rows">${row('🏆', 'بطل العالم 2018', '✓')}${row('⚽', 'هدف في النهائي', '✓')}</div>${SUB('وعمره 19 عامًا')}` },
  { ph: 1, club: 1, glow: '#0c1a3a', html: head(9847, '<span style="font-size:84px">باريس سان جيرمان</span>', '2017 - 2024', PSG) + `<div class="chips">${chip(256, 'هدفًا', 256)}${chip(308, 'مباراة', 308)}</div><div class="rows">${row('🥇', 'الهداف التاريخي للنادي', '✓')}</div>` },
  { ph: 2, club: 1, glow: '#0c1a3a', html: `<div class="ttl">مع باريس</div><div class="rows">${row('🏆', 'الدوري الفرنسي', '×6')}${row('🏆', 'كأس فرنسا', '×4')}</div>` },
  { ph: 4, club: 3, glow: '#0c1440', html: `<div class="ttl" style="font-size:72px">نهائي كأس العالم 2022</div><div class="yrs" style="font-size:220px;line-height:1"><b data-n="3">3</b></div><div class="ttl" style="font-size:54px">أهداف أمام الأرجنتين</div>${SUB('وخسرت فرنسا بركلات الترجيح')}` },
  { ph: 3, club: 2, glow: '#2e2a10', html: `<div class="yrs" style="font-size:90px">صيف 2024</div><div class="vs"><img src="${L(9847)}"><span class="x">←</span><img src="${L(8633)}"></div><div class="rows">${row('👟', 'الحذاء الذهبي الأوروبي', '✓')}</div>${SUB('في موسمه الأول')}` },
  { ph: 3, club: 2, glow: '#2e2a10', html: `<div class="yrs" style="font-size:90px">2025-2026</div><div class="rows">${row('👟', 'هداف الدوري الإسباني', '<b data-n="25">25</b>')}${row('👟', 'هداف دوري أبطال أوروبا', '<b data-n="15">15</b>')}</div>` },
  { ph: 3, club: 2, glow: '#2e2a10', html: head(8633, 'ريال مدريد', 'منذ 2024', RM) + `<div class="chips">${chip(100, 'هدف', 100)}${chip(116, 'مباراة', 116)}</div>` },
  { ph: 4, club: 3, glow: '#0c1440', html: `<div class="ttl" style="font-size:72px">كأس العالم 2026</div><div class="chips">${chip(10, 'أهداف', 10)}</div><div class="rows">${row('👟', 'هداف البطولة', '✓')}</div>` },
  { ph: 0, club: 3, glow: '#0c1440', html: `<div class="yrs" style="font-size:220px;line-height:1"><b data-n="22">22</b></div><div class="ttl">هدفًا في كؤوس العالم</div><div class="rows">${row('🥇', 'الهداف التاريخي للمونديال', '✓')}</div>` },
  { ph: 4, club: 3, glow: '#0c1440', html: head(6723, 'منتخب فرنسا', '', FRA) + `<div class="chips">${chip(67, 'هدفًا', 67)}${chip(107, 'مباراة', 107)}</div><div class="rows">${row('🥇', 'الهداف التاريخي للمنتخب', '✓')}</div>` },
  { club: 3, glow: '#2a1a5e', html: `<div class="vs" style="gap:14px;flex-wrap:wrap;justify-content:center">${CLUBS.map((id) => `<img src="${L(id)}" style="width:118px;height:118px">`).join('<span class="x" style="font-size:40px">←</span>')}</div><div class="ttl" style="margin-top:30px">أي محطة هي<br>الأجمل في رأيك؟</div>${SUB('اكتبها في التعليقات 👇')}` },
'''
