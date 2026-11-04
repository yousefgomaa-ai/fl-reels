// Renders sample jobs (a JSON list of {id, anim}) with make.mjs's recorder into the given folder; photo jobs as JPEGs.
import { makeAnim, makeImage } from '../make.mjs';
import { mkdtemp, copyFile, readFile } from 'node:fs/promises';
import { join } from 'node:path';
const [jobsFile, out] = process.argv.slice(2);
for (const j of JSON.parse(await readFile(jobsFile, 'utf8'))) {
  const dir = await mkdtemp('/tmp/fl-');
  try { await copyFile(j.image ? await makeImage(j, dir) : await makeAnim(j, dir), join(out, j.id + (j.image ? '.jpg' : '.mp4'))); console.log('ok', j.id); } catch (e) { console.log('FAIL', j.id, e.message); }
}
