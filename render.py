# -*- coding: utf-8 -*-
"""Render page.tmpl.html into three flavours:
   remote  -> hotlinks upload.wikimedia.org        (small file, needs internet)
   local   -> img/<key>.jpg next to the html       (self-contained site, used by GitHub Pages)
   inline  -> base64 data: URIs inside the html    (one single portable file)
"""
import json, re, sys, os, base64

IM = json.load(open(os.path.join(os.path.dirname(__file__), 'imgs2.json')))
TMPL = open(os.path.join(os.path.dirname(__file__), 'page.tmpl.html'), encoding='utf-8').read()
TOK = re.compile(r'IMGSRC::([a-z0-9_]+)::([lm])')

def render(mode, imgdir='img', out='index.html'):
    cache = {}
    def sub(m):
        key, size = m.group(1), m.group(2)
        if mode == 'remote':
            return IM[key]['l' if size == 'l' else 'm']
        if mode == 'local':
            return '%s/%s.jpg' % (imgdir, key)
        if key in cache:
            return cache[key]
        p = os.path.join(imgdir, key + '.jpg')
        b = base64.b64encode(open(p, 'rb').read()).decode()
        cache[key] = 'data:image/jpeg;base64,' + b
        return cache[key]
    html = TOK.sub(sub, TMPL)
    open(out, 'w', encoding='utf-8').write(html)
    print(mode, '->', out, round(len(html.encode()) / 1024, 1), 'KB')

if __name__ == '__main__':
    render(sys.argv[1] if len(sys.argv) > 1 else 'remote',
           sys.argv[2] if len(sys.argv) > 2 else 'img',
           sys.argv[3] if len(sys.argv) > 3 else 'index.html')
