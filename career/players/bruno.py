NAME = 'برونو فيرنانديز'
BADGES = ['🅰️ رقم قياسي: 21 تمريرة حاسمة', '🏆 أفضل لاعب في إنجلترا 2026']
CLUBS = [6269, 8600, 9882, 9768, 10260, 8361]
CONSTS = "const NOV = 'rgba(0,70,160,.4)', UDI = 'rgba(255,255,255,.25)', SAM = 'rgba(0,90,170,.4)', SCP = 'rgba(0,128,80,.45)', MUN = 'rgba(218,41,28,.45)', POR = 'rgba(200,16,46,.4)';"
SC = r'''
  { club: -1, html: '' },
  { club: 0, glow: '#0c1e3a', html: head(6269, 'نوفارا', 'مولود 1994 • البداية في إيطاليا', NOV) },
  { club: 1, glow: '#2a2a2a', html: `<div class="vs"><img src="${L(8600)}"><span class="x">←</span><img src="${L(9882)}"></div><div class="ttl">أودينيزي ثم سامبدوريا</div><div class="yrs">2013 - 2017</div>` },
  { club: 3, glow: '#0c3a22', html: `<div class="yrs" style="font-size:90px">صيف 2017</div><div class="vs"><img src="${L(9882)}"><span class="x">←</span><img src="${L(9768)}"></div><div class="ttl">العودة إلى البرتغال</div>` },
  { club: 3, glow: '#0c3a22', html: head(9768, 'سبورتينغ لشبونة', '2017 - 2020', SCP) + `<div class="rows">${row('⚽', 'أهداف', '+60')}${row('🏆', 'كأس البرتغال', '✓')}${row('🏆', 'كأس الرابطة', '×2')}</div>` },
  { club: 4, glow: '#3a0c0c', html: `<div class="yrs" style="font-size:90px">يناير 2020</div><div class="vs"><img src="${L(9768)}"><span class="x">←</span><img src="${L(10260)}"></div><div class="ttl">إلى مانشستر يونايتد</div>` },
  { ph: 1, club: 4, glow: '#3a0c0c', html: head(10260, 'مانشستر يونايتد', '2023', MUN) + `<div class="rows">${row('🏆', 'كأس الرابطة الإنجليزية', '✓')}${row('©️', 'قائد الفريق', '✓')}</div>` },
  { club: 4, glow: '#3a0c0c', html: `<div class="yrs" style="font-size:90px">2024</div><div class="ttl">كأس الاتحاد الإنجليزي</div><div class="rows">${row('🏆', 'الفوز على مانشستر سيتي في النهائي', '✓')}</div>` },
  { club: 4, glow: '#3a0c0c', html: `<div class="ttl">موسم 2025 - 2026</div><div class="chips">${chip(21, 'تمريرة حاسمة', 21)}</div>${SUB('رقم قياسي في موسم واحد بالدوري الإنجليزي')}` },
  { club: 4, glow: '#3a0c0c', html: `<div class="ttl">أفضل لاعب في<br>الدوري الإنجليزي</div><div class="yrs">موسم 2025 - 2026</div>` },
  { club: 4, glow: '#3a0c0c', html: head(10260, 'مانشستر يونايتد', 'منذ 2020', MUN) + `<div class="chips">${chip('+110', 'هدفًا')}${chip('+330', 'مباراة')}</div>` },
  { ph: 2, club: 5, glow: '#3a0c14', html: head(8361, 'منتخب البرتغال', '2019 • 2025', POR) + `<div class="rows">${row('🏆', 'دوري الأمم الأوروبية', '×2')}</div>` },
  { club: 5, glow: '#2a1a5e', html: `<div class="vs" style="gap:14px;flex-wrap:wrap;justify-content:center">${CLUBS.map((id) => `<img src="${L(id)}" style="width:100px;height:100px">`).join('<span class="x" style="font-size:40px">←</span>')}</div><div class="ttl" style="margin-top:30px">أي محطة هي<br>الأجمل في رأيك؟</div>${SUB('اكتبها في التعليقات 👇')}` },
'''
