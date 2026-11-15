# English cut for FB Legends (owner, 2026-11-15). Facts read on Wikipedia 2026-11-15 (club stats as of 8 November 2026,
# Brazil as of 29 September 2026). The 2025 Ballon d'Or placing is left out (not on the page).
LANG = 'en'
NAME = 'RAPHINHA'
BADGES = ['©️ BARCELONA CAPTAIN', '⚽ 94 BARÇA GOALS']
CLUBS = [7844, 9768, 9851, 8463, 8634, 8256]
CONSTS = "const VSC = 'rgba(255,255,255,.25)', SCP = 'rgba(0,128,87,.5)', LEE = 'rgba(255,205,0,.35)', BAR = 'rgba(165,0,68,.45)', BRA = 'rgba(0,155,58,.5)';"
SC = r'''
  { club: -1, html: '' },
  { ph: 2, club: 0, glow: '#1e1e1e', html: `<div class="yrs" style="font-size:150px">1996</div><div class="vs"><img src="${L(8256)}"><span class="x">→</span><img src="${L(7844)}"></div><div class="ttl">PORTO ALEGRE TO PORTUGAL</div>${SUB('Vitória de Guimarães at 19')}` },
  { club: 1, glow: '#0c3a24', html: head(9768, 'SPORTING CP', '2018 - 2019', SCP) + `<div class="rows">${row('🏆', 'Portuguese Cup', '✓')}${row('🏆', 'League Cup', '✓')}</div>${SUB('Then on to Rennes')}` },
  { ph: 1, club: 3, glow: '#2e2a0c', html: head(8463, 'LEEDS UNITED', '2020 - 2022', LEE) + `<div class="chips">${chip(17, 'goals', 17)}${chip(67, 'games', 67)}</div>` },
  { club: 4, glow: '#2a0c1e', html: `<div class="yrs" style="font-size:110px">SUMMER 2022</div><div class="vs"><img src="${L(8463)}"><span class="x">→</span><img src="${L(8634)}"></div><div class="ttl">BARCELONA</div>` },
  { ph: 4, club: 4, glow: '#2a0c1e', html: `<div class="yrs" style="font-size:110px">2022 - 2023</div><div class="ttl">FIRST SEASON</div><div class="rows">${row('🏆', 'La Liga', '✓')}</div>` },
  { ph: 4, club: 4, glow: '#2a0c1e', html: `<div class="ttl">THE BEST SEASON</div><div class="chips">${chip(34, 'goals', 34)}</div><div class="rows">${row('🏆', 'La Liga', '✓')}${row('🏆', 'Copa del Rey', '✓')}${row('🏆', 'Super Cup', '✓')}</div>` },
  { ph: 4, club: 4, glow: '#3a2a10', html: `<div class="yrs" style="font-size:110px">2024 - 2025</div><div class="rows">${row('👟', 'UCL joint top scorer', '<b data-n="13">13</b>')}${row('⭐', 'La Liga Player of the Season', '✓')}</div>` },
  { ph: 4, club: 4, glow: '#2a0c1e', html: `<div class="yrs" style="font-size:110px">2025 - 2026</div><div class="ttl">THIRD LA LIGA TITLE</div><div class="rows">${row('🏆', 'La Liga with Barça', '×3')}</div>` },
  { ph: 4, club: 4, glow: '#2a0c1e', html: `<div class="ttl">BARCELONA CAPTAIN</div><div class="vs"><img src="${L(8634)}"></div><div class="rows">${row('©️', 'First Brazilian captain', '✓')}</div>` },
  { ph: 4, club: 4, glow: '#2a0c1e', html: `<div class="ttl">RECORD START</div><div class="chips">${chip(14, 'goals', 14)}${chip(8, 'games', 8)}</div>${SUB('A Barcelona record for the start of a season')}` },
  { ph: 4, club: 4, glow: '#2a0c1e', html: head(8634, 'BARCELONA', 'SINCE 2022', BAR) + `<div class="chips">${chip(94, 'goals', 94)}${chip(191, 'games', 191)}</div><div class="rows">${row('✍️', 'Contract until', '2030')}</div>` },
  { ph: 3, club: 5, glow: '#0c3a1e', html: head(8256, 'BRAZIL', 'WORLD CUPS 2022 & 2026', BRA) + `<div class="chips">${chip(12, 'goals', 12)}${chip(43, 'games', 43)}</div>` },
  { club: 5, glow: '#2a1a5e', html: `<div class="vs" style="gap:14px;flex-wrap:wrap;justify-content:center">${CLUBS.map((id) => `<img src="${L(id)}" style="width:110px;height:110px">`).join('<span class="x" style="font-size:50px">→</span>')}</div><div class="ttl" style="margin-top:30px">WHICH STOP IS<br>YOUR FAVOURITE?</div>${SUB('Tell us in the comments 👇')}` },
'''
