# English cut for FB Legends (owner, 2026-11-15). Facts read on Wikipedia 2026-11-15 (Norway: as of 14 November 2026;
# City all competitions: 176 goals in 211 games); "fastest to 50 Champions League goals" left out (not confirmed).
LANG = 'en'
NAME = 'ERLING HAALAND'
BADGES = ['⚽ 36 IN ONE PL SEASON', '🏆 TREBLE 2023']
CLUBS = [8531, 9917, 10013, 9789, 8456, 8492]
CONSTS = "const SAL = 'rgba(204,0,51,.45)', BVB = 'rgba(253,225,0,.4)', MCI = 'rgba(108,171,221,.5)', NOR = 'rgba(186,12,47,.5)';"
SC = r'''
  { club: -1, html: '' },
  { club: 0, glow: '#2a1010', html: `<div class="yrs" style="font-size:150px">2000</div><div class="vs"><img src="${L(8531)}"></div><div class="ttl">BORN IN LEEDS</div>${SUB('Grew up in Bryne, Norway')}` },
  { club: 1, glow: '#0c1a3a', html: `<div class="vs"><img src="${L(9917)}"><span class="x">→</span><img src="${L(10013)}"></div><div class="ttl">MOLDE TO SALZBURG</div>` },
  { club: 2, glow: '#3a0c14', html: head(10013, 'RED BULL SALZBURG', '2019', SAL) + `<div class="chips">${chip(29, 'goals', 29)}${chip(27, 'games', 27)}</div>` },
  { ph: 1, club: 3, glow: '#2e2a0c', html: head(9789, 'BORUSSIA DORTMUND', '2020 - 2022', BVB) + `<div class="chips">${chip(86, 'goals', 86)}${chip(89, 'games', 89)}</div><div class="rows">${row('🏆', 'German Cup', '2021')}</div>` },
  { club: 4, glow: '#0c2a3a', html: `<div class="yrs" style="font-size:110px">SUMMER 2022</div><div class="vs"><img src="${L(9789)}"><span class="x">→</span><img src="${L(8456)}"></div><div class="ttl">MANCHESTER CITY</div>` },
  { ph: 3, club: 4, glow: '#0c2a3a', html: `<div class="ttl">FIRST SEASON</div><div class="chips">${chip(36, 'PL goals', 36)}</div>${SUB('A Premier League record for one season')}` },
  { ph: 3, club: 4, glow: '#0c2a3a', html: `<div class="yrs" style="font-size:150px">2023</div><div class="ttl">THE TREBLE</div><div class="rows">${row('🏆', 'Premier League', '✓')}${row('🏆', 'FA Cup', '✓')}${row('🏆', 'Champions League', '✓')}</div>` },
  { ph: 3, club: 4, glow: '#0c2a3a', html: `<div class="ttl">MORE SILVERWARE</div><div class="rows">${row('🏆', 'Premier League', '×2')}${row('🏆', 'FA Cup', '×2')}${row('🏆', 'League Cup', '2026')}${row('👟', 'Golden Boot', '×3')}</div>` },
  { ph: 3, club: 4, glow: '#0c2a3a', html: head(8456, 'MANCHESTER CITY', 'SINCE 2022', MCI) + `<div class="chips">${chip(176, 'goals', 176)}${chip(211, 'games', 211)}</div>` },
  { ph: 2, club: 5, glow: '#3a1010', html: head(8492, 'NORWAY', 'WORLD CUP 2026', NOR) + `<div class="rows">${row('🌍', 'First World Cup since 1998', '✓')}${row('⚽', 'Goals at the finals', '7')}</div>` },
  { ph: 2, club: 5, glow: '#3a1010', html: `<div class="ttl">ROUND OF 16</div><div class="rows">${row('⚽', 'Two goals v Brazil', '2-1')}${row('🌍', 'First ever quarter-final', '✓')}</div>` },
  { ph: 2, club: 5, glow: '#3a1010', html: `<div class="ttl">NORWAY'S RECORD SCORER</div><div class="chips">${chip(66, 'goals', 66)}${chip(60, 'games', 60)}</div>` },
  { club: 5, glow: '#2a1a5e', html: `<div class="vs" style="gap:14px;flex-wrap:wrap;justify-content:center">${CLUBS.map((id) => `<img src="${L(id)}" style="width:110px;height:110px">`).join('<span class="x" style="font-size:50px">→</span>')}</div><div class="ttl" style="margin-top:30px">WHICH STOP IS<br>YOUR FAVOURITE?</div>${SUB('Tell us in the comments 👇')}` },
'''
