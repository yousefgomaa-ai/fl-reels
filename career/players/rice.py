NAME = 'ديكلان رايس'
BADGES = ['🏆 بطل إنجلترا 2026', '🎯 ثنائية في الريال']
CLUBS = [8654, 9825, 8491]
CONSTS = "const WHU = 'rgba(122,38,58,.5)', ARS = 'rgba(239,1,7,.45)', ENG = 'rgba(255,255,255,.3)', IRL = 'rgba(22,155,98,.4)';"
SC = r'''
  { club: -1, html: '' },
  { club: 0, glow: '#3a0c1a', html: head(8654, 'وست هام', 'مولود 1999', WHU) + `<div class="rows">${row('⚽', 'البداية الاحترافية', '✓')}</div>` },
  { club: 2, glow: '#1a1a3a', html: `<div class="vs"><img src="${L(5791)}"><span class="x">←</span><img src="${L(8491)}"></div><div class="ttl">من أيرلندا إلى إنجلترا</div>${SUB('3 مباريات مع أيرلندا أولًا')}` },
  { ph: 1, club: 0, glow: '#3a0c1a', html: head(8654, 'دوري المؤتمر الأوروبي', '2023', WHU) + `<div class="rows">${row('🏆', 'أول لقب منذ 43 عامًا', '✓')}</div>` },
  { club: 1, glow: '#3a0c0c', html: `<div class="yrs" style="font-size:90px">صيف 2023</div><div class="vs"><img src="${L(8654)}"><span class="x">←</span><img src="${L(9825)}"></div><div class="ttl">أغلى صفقة في تاريخ آرسنال</div>` },
  { ph: 2, club: 2, glow: '#1a1a3a', html: head(8491, 'كأس أوروبا', '2024', ENG) + `<div class="rows">${row('🥈', 'الوصول إلى النهائي', '✓')}</div>` },
  { club: 1, glow: '#3a0c0c', html: `<div class="yrs" style="font-size:90px">أبريل 2025</div><div class="ttl">🎯🎯 ركلتان حرتان</div>${SUB('في مرمى ريال مدريد')}` },
  { club: 1, glow: '#3a0c0c', html: `<div class="ttl">الأول في التاريخ</div>${SUB('هدفان من ركلات حرة مباشرة في مباراة إقصائية بدوري الأبطال')}` },
  { club: 1, glow: '#3a0c0c', html: head(9825, 'الدوري الإنجليزي', '2025 - 2026', ARS) + `<div class="rows">${row('🏆', 'الأول منذ 22 عامًا', '✓')}</div>` },
  { club: 1, glow: '#3a0c0c', html: `<div class="ttl">نهائي دوري الأبطال</div><div class="yrs">2026</div>` },
  { club: 2, glow: '#1a1a3a', html: head(8491, 'منتخب إنجلترا', 'منذ 2019', ENG) + `<div class="chips">${chip('+70', 'مباراة')}</div>` },
  { club: 2, glow: '#2a1a5e', html: `<div class="vs" style="gap:14px;flex-wrap:wrap;justify-content:center">${CLUBS.map((id) => `<img src="${L(id)}" style="width:100px;height:100px">`).join('<span class="x" style="font-size:40px">←</span>')}</div><div class="ttl" style="margin-top:30px">أي محطة هي<br>الأجمل في رأيك؟</div>${SUB('اكتبها في التعليقات 👇')}` },
'''
