# One-off sample (owner, 2026-11-11): an AI "motion comic" episode from series/story.json.
# Images: Pollinations (free, no key). Voice: Edge TTS (free, no key). Video: ffmpeg.
import json, os, subprocess, sys, time, urllib.parse, urllib.request
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
D = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(D, 'out')
os.makedirs(OUT, exist_ok=True)
S = json.load(open(os.path.join(D, 'story.json')))
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
REG = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-3000:])
        raise SystemExit(f'failed: {cmd[:4]}')
    return r.stdout


def dur(f):
    return float(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]).strip())


def fetch_img(i, sc):
    path = os.path.join(OUT, f'img{i:02d}.jpg')
    if os.path.exists(path):
        return path
    p = sc['img']
    for k, v in S['characters'].items():
        p = p.replace('{' + k + '}', v)
    p = f"{p}, {S['style']}, vertical composition, no text"
    url = ('https://image.pollinations.ai/prompt/' + urllib.parse.quote(p) +
           f"?width=768&height=1344&seed={sc['seed']}&model=flux&nologo=true")
    for t in range(6):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'series-sample'})
            data = urllib.request.urlopen(req, timeout=180).read()
            if len(data) > 20000:
                open(path, 'wb').write(data)
                Image.open(path).convert('RGB').save(path, quality=92)
                print('image', i, len(data))
                return path
            print('small reply', i, data[:200])
        except Exception as e:
            print('image retry', i, t, e)
        time.sleep(10 + t * 10)
    raise SystemExit(f'no image for scene {i}')


def cover(img):
    im = Image.open(img).convert('RGB')
    r = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2
    return im.crop((x, y, x + W, y + H))


def phone_frame(bg, ph, path):
    # The phone screen is drawn, never generated: AI text comes out garbled.
    im = cover(bg).filter(ImageFilter.GaussianBlur(14))
    im = Image.blend(im, Image.new('RGB', im.size, (0, 0, 0)), 0.45)
    d = ImageDraw.Draw(im)
    px, py, pw, phh = 150, 330, 780, 1260
    d.rounded_rectangle((px - 18, py - 18, px + pw + 18, py + phh + 18), 90, fill=(20, 20, 22))
    d.rounded_rectangle((px, py, px + pw, py + phh), 72, fill=(12, 12, 14))
    f_time, f_name, f_msg = ImageFont.truetype(BOLD, 34), ImageFont.truetype(BOLD, 46), ImageFont.truetype(REG, 44)
    d.text((px + pw / 2, py + 60), ph['time'], font=f_time, fill=(200, 200, 205), anchor='mm')
    d.ellipse((px + pw / 2 - 55, py + 110, px + pw / 2 + 55, py + 220), fill=(90, 90, 98))
    d.text((px + pw / 2, py + 165), ph['from'][0], font=f_name, fill='white', anchor='mm')
    d.text((px + pw / 2, py + 265), ph['from'], font=f_name, fill='white', anchor='mm')
    d.line((px + 40, py + 320, px + pw - 40, py + 320), fill=(45, 45, 50), width=2)
    y = py + 370
    for side, text in ph['msgs']:
        tw = d.textlength(text, font=f_msg)
        bw, bh = tw + 60, 90
        if side == 'in':
            x0, col, fc = px + 40, (58, 58, 62), 'white'
        else:
            x0, col, fc = px + pw - 40 - bw, (10, 132, 255), 'white'
        d.rounded_rectangle((x0, y, x0 + bw, y + bh), 42, fill=col)
        d.text((x0 + 30, y + bh / 2), text, font=f_msg, fill=fc, anchor='lm')
        y += bh + 34
    im.save(path, quality=93)
    return path


def end_frame(bg, path):
    im = cover(bg)
    im = Image.blend(im, Image.new('RGB', im.size, (0, 0, 0)), 0.35)
    d = ImageDraw.Draw(im)
    f1, f2, f3 = ImageFont.truetype(BOLD, 64), ImageFont.truetype(BOLD, 96), ImageFont.truetype(BOLD, 52)
    d.text((W / 2, 520), 'WHO SENT THE TEXT?', font=f1, fill='white', anchor='mm', stroke_width=5, stroke_fill='black')
    d.text((W / 2, 640), 'COMMENT BELOW', font=f3, fill=(255, 200, 60), anchor='mm', stroke_width=4, stroke_fill='black')
    d.rounded_rectangle((180, 1420, 900, 1560), 30, fill=(200, 20, 30))
    d.text((W / 2, 1490), 'PART 2 IN 1 HOUR', font=f3, fill='white', anchor='mm')
    im.save(path, quality=93)
    return path


def caption_pngs(i, text, total):
    # Short word groups timed by their length, like spoken subtitles.
    words, groups, cur = text.split(), [], []
    for w in words:
        cur.append(w)
        if len(cur) >= 4 or w.endswith(('.', '?', ',')):
            groups.append(' '.join(cur)); cur = []
    if cur:
        groups.append(' '.join(cur))
    weights = [len(g) + 4 for g in groups]
    tot, t, out = sum(weights), 0.15, []
    span = total - 0.3
    font = ImageFont.truetype(BOLD, 68)
    for k, g in enumerate(groups):
        dt = span * weights[k] / tot
        im = Image.new('RGBA', (W, 260), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.text((W / 2, 130), g.upper(), font=font, fill='white', anchor='mm', stroke_width=7, stroke_fill='black')
        p = os.path.join(OUT, f'cap{i:02d}_{k}.png')
        im.save(p)
        out.append((p, t, t + dt))
        t += dt
    return out


def tts(text, mp3):
    # Edge TTS first; GitHub's runners are sometimes refused, then Piper (open source, runs on the runner itself).
    for args in (['--rate=-6%', '--pitch=-4Hz'], [], []):
        r = subprocess.run(['edge-tts', '--voice', S['voice'], *args, '--text', text, '--write-media', mp3], capture_output=True, text=True)
        if r.returncode == 0 and os.path.exists(mp3) and os.path.getsize(mp3) > 2000:
            print('voice: edge')
            return
        print('edge-tts failed', r.stderr[-200:])
        time.sleep(4)
    wav = mp3[:-4] + '.wav'
    r = subprocess.run(['piper', '-m', os.path.join(D, 'piper', 'voice.onnx'), '--length_scale', '1.08', '-f', wav], input=text, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-1500:]); raise SystemExit('piper failed')
    run(['ffmpeg', '-y', '-i', wav, '-ar', '44100', '-b:a', '160k', mp3])
    print('voice: piper')


def badge():
    p = os.path.join(OUT, 'badge.png')
    im = Image.new('RGBA', (W, 140), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f, f2 = ImageFont.truetype(BOLD, 40), ImageFont.truetype(BOLD, 30)
    label = f"{S['title']}  ·  EP {S['episode']}"
    tw = d.textlength(label, font=f)
    d.rounded_rectangle((W / 2 - tw / 2 - 30, 30, W / 2 + tw / 2 + 30, 100), 20, fill=(0, 0, 0, 150))
    d.text((W / 2, 65), label, font=f, fill=(255, 255, 255), anchor='mm')
    im.save(p)
    return p


def main():
    segs, bp = [], badge()
    for i, sc in enumerate(S['scenes']):
        img = fetch_img(i, sc)
        time.sleep(3)
        mp3 = os.path.join(OUT, f'say{i:02d}.mp3')
        tts(sc['say'], mp3)
        total = dur(mp3) + 0.55
        frame = img
        if sc.get('phone'):
            frame = phone_frame(img, sc['phone'], os.path.join(OUT, f'phone{i:02d}.jpg'))
        elif sc.get('end'):
            frame = end_frame(img, os.path.join(OUT, f'end{i:02d}.jpg'))
        else:
            cover(img).save(os.path.join(OUT, f'frame{i:02d}.jpg'), quality=93)
            frame = os.path.join(OUT, f'frame{i:02d}.jpg')
        n = int(total * FPS) + 1
        # Slow push in or out, alternating, so no scene stands still (the reel rule).
        if i % 2 == 0:
            z = f"1+0.10*on/{n}"
        else:
            z = f"1.10-0.10*on/{n}"
        drift = ['iw/2-(iw/zoom/2)', f'(iw-iw/zoom)*on/{n}', f'(iw-iw/zoom)*(1-on/{n})'][i % 3]
        caps = [] if sc.get('end') else caption_pngs(i, sc['say'], total)
        inputs = ['-loop', '1', '-framerate', str(FPS), '-i', frame, '-i', bp]
        for c in caps:
            inputs += ['-i', c[0]]
        inputs += ['-i', mp3]
        fc = (f"[0:v]scale={W*2}:{H*2},zoompan=z='{z}':x='{drift}':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},"
              f"vignette=PI/4.5,noise=alls=3:allf=t,eq=contrast=1.05:saturation=0.9[v0];[v0][1:v]overlay=0:40[v1]")
        last = 'v1'
        for k, c in enumerate(caps):
            cy = 1620 if sc.get('phone') else 1380
            fc += f";[{last}][{k+2}:v]overlay=0:{cy}:enable='between(t,{c[1]:.2f},{c[2]:.2f})'[c{k}]"
            last = f'c{k}'
        fc += f";[{last}]fade=t=in:st=0:d=0.25,fade=t=out:st={total-0.3:.2f}:d=0.3,format=yuv420p[vout]"
        a = len(caps) + 2
        fc += f";[{a}:a]adelay=150|150,apad,atrim=0:{total:.2f},aresample=44100,aformat=channel_layouts=stereo[aout]"
        seg = os.path.join(OUT, f'seg{i:02d}.mp4')
        run(['ffmpeg', '-y', *inputs, '-filter_complex', fc, '-map', '[vout]', '-map', '[aout]', '-t', f'{total:.2f}',
             '-c:v', 'libx264', '-preset', 'medium', '-crf', '24', '-r', str(FPS), '-c:a', 'aac', '-b:a', '160k', seg])
        segs.append(seg)
        print('scene', i, f'{total:.1f}s')
    lst = os.path.join(OUT, 'list.txt')
    open(lst, 'w').write(''.join(f"file '{s}'\n" for s in segs))
    voice = os.path.join(OUT, 'voice.mp4')
    run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', voice])
    T = dur(voice)
    # A low synthesised drone under the voice: sine tones only, no noise (the hiss the owner heard, 2026-11-11).
    drone = ("aevalsrc='0.35*sin(2*PI*55*t)*(0.6+0.4*sin(2*PI*0.08*t))+0.22*sin(2*PI*82.41*t)*(0.5+0.5*sin(2*PI*0.05*t+1))"
             f"+0.12*sin(2*PI*110*t)+0.06*sin(2*PI*164.8*t)*(0.5+0.5*sin(2*PI*0.13*t))':s=44100:d={T:.2f}")
    final = os.path.join(D, 'episode1.mp4')
    run(['ffmpeg', '-y', '-i', voice, '-f', 'lavfi', '-i', drone, '-filter_complex',
         "[1:a]lowpass=f=500,volume=0.22,afade=t=in:d=2,aformat=channel_layouts=stereo[m];[0:a][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]",
         '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', final])
    print('done', f'{T:.1f}s', os.path.getsize(final))


main()
