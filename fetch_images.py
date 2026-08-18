# -*- coding: utf-8 -*-
"""Download every Wikimedia Commons photo used by the page into img/.
Runs on GitHub Actions (which has unrestricted internet)."""
import json, os, urllib.request, sys
from PIL import Image
import io

IM = json.load(open('imgs2.json'))
os.makedirs('img', exist_ok=True)
UA = {'User-Agent': 'chile-peru-itinerary/1.0 (personal travel page; contact via GitHub)'}
MAXW = int(os.environ.get('MAXW', '1920'))

ok = fail = 0
for k, v in IM.items():
    dest = 'img/%s.jpg' % k
    if os.path.exists(dest) and os.path.getsize(dest) > 20000:
        ok += 1
        continue
    for url in (v['l'], v['m']):
        try:
            raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90).read()
            im = Image.open(io.BytesIO(raw)).convert('RGB')
            if im.width > MAXW:
                im = im.resize((MAXW, round(im.height * MAXW / im.width)), Image.LANCZOS)
            im.save(dest, 'JPEG', quality=84, optimize=True, progressive=True)
            print('ok  %-14s %5dx%-5d %6.0f KB' % (k, im.width, im.height, os.path.getsize(dest) / 1024))
            ok += 1
            break
        except Exception as e:
            print('..  %s retry (%s)' % (k, e))
    else:
        print('FAIL', k); fail += 1

print('downloaded %d, failed %d' % (ok, fail))
sys.exit(1 if fail else 0)
