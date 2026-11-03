// One-off check (2026-11-03): every moving reel kind drawn on a GitHub runner, from real logo and photo addresses.
import { mkdtemp, copyFile, mkdir } from 'node:fs/promises';
import { tmpdir } from 'node:os'; import { join } from 'node:path';
import { execFileSync } from 'node:child_process';
import { makeAnim } from '../make.mjs';
const L = (id) => `https://images.fotmob.com/image_resources/logo/teamlogo/${id}.png`;
const jobs = {
  table: { kind: 'table', slug: 'egy.1', league: 'الدوري المصري', sub: 'بعد مباريات الأحد 2 نوفمبر', top: 2, bottom: 3, topLabel: 'المقاعد القارية',
    rows: [...Array(21)].map((_, i) => ({ n: ['الأهلي', 'الزمالك', 'بيراميدز', 'المصري'][i % 4] + ' ' + (i + 1), logo: L([101757, 9931, 8455, 8686][i % 4]), r: i + 1, p: i % 3 === 0 ? i + 2 > 21 ? i + 1 : i + 2 : i % 3 === 1 ? i : i + 1, pl: 10, w: 7, d: 1, l: 2, gd: 10 - i, pts: 40 - i, pp: 37 - i })) },
  schedule: { kind: 'schedule', label: 'الإثنين 3 نوفمبر', big: { league: 'الدوري الإسباني', home: 'ريال مدريد', away: 'برشلونة', homeLogo: L(8633), awayLogo: L(8634), time: '22:00', tv: 'beIN SPORTS 1' },
    rows: [...Array(12)].map((_, i) => ({ league: 'الدوري الإنجليزي', home: 'آرسنال', away: 'ليفربول', homeLogo: L(9825), awayLogo: L(8650), time: `1${i % 10}:00`, tv: i % 2 ? null : 'beIN SPORTS 2' })) },
  prematch: { kind: 'prematch', chip: 'مباراة اليوم • الدوري الإسباني', home: 'ريال مدريد', away: 'برشلونة', homeLogo: L(8633), awayLogo: L(8634), when: 'اليوم 22:00 بتوقيت القاهرة', tv: 'beIN SPORTS 1',
    h2h: { label: 'آخر 5 مواجهات', home: 2, draws: 1, away: 2 }, form: { home: 'WWDWL', away: 'WLWWW' }, table: null },
  lineup: { kind: 'lineup', chip: 'التشكيلة الرسمية • الدوري الإنجليزي', sides: [
    { team: 'آرسنال', logo: L(9825), formation: '4-3-3', players: ['رايا', 'وايت', 'صليبا', 'غابرييل', 'كالافيوري', 'رايس', 'أوديغارد', 'ميرينو', 'ساكا', 'جيوكيريس', 'مارتينيلي'].map((n, i) => ({ n, num: String(i + 1) })) },
    { team: 'ليفربول', logo: L(8650), formation: '4-2-3-1', players: ['أليسون', 'فريمبونغ', 'كوناتي', 'فان دايك', 'كيركيز', 'خرافنبيرخ', 'ماك أليستر', 'صلاح', 'فيرتس', 'غاكبو', 'إيكيتيكي'].map((n, i) => ({ n, num: String(i + 1) })) }] },
  fulltime: { kind: 'fulltime', chip: 'نهاية المباراة • الدوري الإنجليزي', home: 'آرسنال', away: 'ليفربول', homeLogo: L(9825), awayLogo: L(8650), hs: 3, as: 1, end: 90, pens: '',
    goals: [{ m: '23', n: 'ساكا', s: 'h' }, { m: '41', n: 'صلاح', s: 'a', pen: true }, { m: '45+2', n: 'أوديغارد', s: 'h' }, { m: '88', n: '', s: 'h', og: true }],
    stats: [['الاستحواذ %', 58, 42], ['التسديدات', 15, 8], ['على المرمى', 7, 3]], motm: { name: 'ساكا', rating: 8.7 }, cta: 'من رجل المباراة في رأيك؟' },
  star: { kind: 'star', name: 'محمد صلاح', sub: 'ليفربول • الدوري الإنجليزي', photo: 'https://commons.wikimedia.org/wiki/Special:FilePath/Mohamed_Salah_Argentina_v_Egypt_7_July_2026-161_(cropped).jpg?width=960', credit: 'Bryan Berlin (CC BY-SA 4.0)',
    tiles: [{ stat: '9', text: 'من أصل 30 سجلها برشلونة' }, { stat: '16', text: 'مساهمة تهديفية في الدوري' }, { stat: '41', text: 'فرصة صنعها للتسجيل' }], note: 'المركز الأول في صناعة الفرص بالدوري', q: 'هل هو الأفضل في الدوري الإسباني الآن؟' },
};
await mkdir('test/out', { recursive: true });
let bad = 0;
for (const [k, anim] of Object.entries(jobs).filter(([k]) => !process.env.ONLY || process.env.ONLY.split(',').includes(k))) {
  const t = Date.now();
  try {
    const dir = await mkdtemp(join(tmpdir(), 'at-'));
    const out = await makeAnim({ id: 'test-' + k, anim }, dir);
    await copyFile(out, `test/out/${k}.mp4`);
    const d = execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', out]).toString().trim();
    for (const s of [2, 5, 8]) execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-ss', String(s), '-i', out, '-frames:v', '1', '-vf', 'scale=360:640', `test/out/${k}-${s}.jpg`]);
    console.log(`OK ${k}: ${d}s in ${Math.round((Date.now() - t) / 1000)}s`);
  } catch (e) { bad++; console.log(`FAIL ${k}: ${e.message}`); }
}
process.exit(bad ? 1 : 0);
