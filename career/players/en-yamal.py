# English cut for FB Legends (owner, 2026-11-15). Facts read on Wikipedia 2026-11-15 (club stats as of 8 November 2026).
# Spain's totals left out (the page's table stops in October, before this month's matches).
LANG = 'en'
NAME = 'LAMINE YAMAL'
BADGES = ['🏆 WORLD CHAMPION 2026', '⭐ KOPA TROPHY ×3']
CLUBS = [8634, 6720]
CONSTS = "const BAR = 'rgba(165,0,68,.45)', ESP = 'rgba(198,11,30,.45)';"
SC = r'''
  { club: -1, html: '' },
  { ph: 1, club: 0, glow: '#2a0c1e', html: `<div class="yrs" style="font-size:150px">2007</div><div class="vs"><img src="${L(8634)}"></div><div class="ttl">ROCAFONDA TO LA MASIA</div>${SUB('Spotted by Barcelona at six')}` },
  { ph: 1, club: 0, glow: '#2a0c1e', html: head(8634, 'BARCELONA', 'APRIL 2023', BAR) + `<div class="rows">${row('⚡', 'Debut at', '15')}${row('🏆', 'La Liga', '✓')}</div>` },
  { ph: 2, club: 1, glow: '#3a0c0c', html: head(6720, 'SPAIN', '2023', ESP) + `<div class="rows">${row('⚡', 'Youngest Spain player ever', '16')}</div>` },
  { ph: 2, club: 1, glow: '#3a0c0c', html: head(6720, 'SPAIN', 'EURO 2024', ESP) + `<div class="rows">${row('🏆', 'European champion', '✓')}${row('⚽', 'Youngest Euro scorer ever', '✓')}${row('⭐', 'Young Player of the Tournament', '✓')}</div>` },
  { ph: 1, club: 0, glow: '#2a0c1e', html: `<div class="ttl">DOMESTIC TREBLE</div><div class="rows">${row('🏆', 'La Liga', '✓')}${row('🏆', 'Copa del Rey', '✓')}${row('🏆', 'Super Cup', '✓')}</div>` },
  { ph: 1, club: 0, glow: '#3a2a10', html: `<div class="yrs" style="font-size:150px">2025</div><div class="rows">${row('⭐', "Ballon d'Or", '2nd')}${row('👕', 'Barcelona shirt', 'No. 10')}</div>` },
  { ph: 1, club: 0, glow: '#2a0c1e', html: `<div class="ttl">LAST SEASON</div><div class="rows">${row('🏆', 'La Liga', '×3')}${row('⭐', 'La Liga Player of the Season', '✓')}</div>` },
  { ph: 0, club: 1, glow: '#3a2a10', html: `<div class="yrs" style="font-size:150px">2026</div><div class="vs"><img src="${L(6720)}"></div><div class="ttl">WORLD CHAMPION 🏆</div>${SUB('Spain 1-0 Argentina in the final')}` },
  { ph: 0, club: 1, glow: '#3a2a10', html: `<div class="ttl">YOUNGEST EVER</div><div class="rows">${row('🏆', 'World Cup', '✓')}${row('🏆', 'Euros', '✓')}</div>${SUB('To win both')}` },
  { ph: 3, club: 0, glow: '#3a2a10', html: `<div class="rows">${row('⭐', 'Kopa Trophy', '×3')}${row('⚽', 'Top-scoring teenager in UCL history', '14')}</div>${SUB('The first to win the Kopa three times')}` },
  { ph: 1, club: 0, glow: '#2a0c1e', html: head(8634, 'BARCELONA', 'SINCE 2023', BAR) + `<div class="chips">${chip(62, 'goals', 62)}${chip(167, 'games', 167)}</div><div class="rows">${row('✍️', 'Contract until', '2031')}</div>` },
  { club: 1, glow: '#2a1a5e', html: `<div class="vs" style="gap:24px;justify-content:center">${CLUBS.map((id) => `<img src="${L(id)}" style="width:150px;height:150px">`).join('<span class="x" style="font-size:60px">+</span>')}</div><div class="ttl" style="margin-top:30px">WHICH MOMENT IS<br>YOUR FAVOURITE?</div>${SUB('Tell us in the comments 👇')}` },
'''
