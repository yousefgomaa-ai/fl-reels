# Builds a career page from Kane's (the approved design), with a player's hook, logos, scenes and photos.
import json, sys, importlib.util, shutil, os
spec_path, out_dir = sys.argv[1], sys.argv[2]
sp = importlib.util.spec_from_file_location('spec', spec_path); S = importlib.util.module_from_spec(sp); sp.loader.exec_module(S)
L = open(os.path.join(os.path.dirname(__file__), 'template.html')).read().split('\n')
import html as H
cred = [dict(c, artist=H.unescape(c['artist']).strip(), license=H.unescape(c['license'])) for c in json.load(open(os.path.join(out_dir, 'ph/credits.json')))]
by = {c['n']: c for c in cred}
h = by.get(0) or cred[0]
L[52] = f'<div id="hook"><div class="ph"><img src="ph/00.jpg"></div><div class="nm">{S.NAME}</div>'
L[53] = '<div class="bd">' + ''.join(f'<div>{b}</div>' for b in S.BADGES) + '</div></div>'
L[56] = f'<div id="credit">Photo: {h["artist"]}, {h["license"]}, via Wikimedia Commons</div>'
L[58] = '<script>window.PHOTOS=' + json.dumps([{'n': c['n'], 'artist': c['artist'], 'license': c['license']} for c in cred], ensure_ascii=False) + ';</script>'
L[61] = 'const CLUBS = ' + json.dumps(S.CLUBS) + ';'
L[67] = S.CONSTS
import re
sc_text = re.sub(r'(\d{4})\s*-\s*(\d{4})', '<span dir="ltr">\\1 - \\2</span>', S.SC.strip())
html = '\n'.join(L[:69] + ['const SC = ['] + [l.rstrip() for l in sc_text.split('\n')] + ['];'] + L[89:])
assert html.count('const SC = [') == 1
open(os.path.join(out_dir, 'page.html'), 'w').write(html)
for f in ('cairo700.woff2', 'cairo900.woff2'): shutil.copy(os.path.join(os.path.dirname(__file__), f), out_dir)
print('ok', len(S.SC.strip().split('\n')), 'scenes')
