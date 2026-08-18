# -*- coding: utf-8 -*-
"""Download every Wikimedia Commons photo used by the page into img/.

Wikimedia rate-limits shared CI IPs hard (HTTP 429), so this throttles
requests and backs off exponentially instead of hammering.
"""
import io, json, os, random, sys, time, urllib.error, urllib.request

from PIL import Image

IM = json.load(open("imgs2.json"))
os.makedirs("img", exist_ok=True)

MAXW = int(os.environ.get("MAXW", "1920"))
QUALITY = int(os.environ.get("QUALITY", "84"))
GAP = float(os.environ.get("GAP", "2.0"))        # polite pause between files
TRIES = int(os.environ.get("TRIES", "6"))

# Wikimedia's UA policy wants a descriptive agent with a contact URL.
UA = {
    "User-Agent": (
        "chile-peru-itinerary/1.0 "
        "(+https://github.com/CTlanston/chile-peru-2026) "
        "python-urllib"
    ),
    "Accept": "image/jpeg,image/*;q=0.8",
    "Accept-Encoding": "identity",
}


def fetch(url, tries=TRIES):
    """GET with exponential backoff. Honours Retry-After on 429."""
    delay = 3.0
    last = None
    for attempt in range(1, tries + 1):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 503, 502, 500):
                wait = delay
                ra = e.headers.get("Retry-After") if e.headers else None
                if ra:
                    try:
                        wait = max(wait, float(ra))
                    except ValueError:
                        pass
                wait += random.uniform(0, 1.5)
                print("    %s -> waiting %.1fs (attempt %d/%d)"
                      % (e.code, wait, attempt, tries), flush=True)
                time.sleep(wait)
                delay = min(delay * 2, 60)
                continue
            raise
        except Exception as e:              # transient network trouble
            last = e
            time.sleep(delay)
            delay = min(delay * 2, 60)
    raise last


ok = []
failed = []
for i, (key, meta) in enumerate(sorted(IM.items()), 1):
    dest = os.path.join("img", key + ".jpg")
    if os.path.exists(dest) and os.path.getsize(dest) > 20_000:
        print("cached %s" % key, flush=True)
        ok.append(key)
        continue

    for url in (meta["l"], meta["m"]):
        try:
            raw = fetch(url)
            im = Image.open(io.BytesIO(raw)).convert("RGB")
            if im.width > MAXW:
                im = im.resize((MAXW, round(im.height * MAXW / im.width)),
                               Image.LANCZOS)
            im.save(dest, "JPEG", quality=QUALITY, optimize=True,
                    progressive=True)
            print("ok  %-14s %5dx%-5d %6.0f KB  (%d/%d)"
                  % (key, im.width, im.height,
                     os.path.getsize(dest) / 1024, i, len(IM)), flush=True)
            ok.append(key)
            break
        except Exception as e:
            print("..  %s failed on this size: %s" % (key, e), flush=True)
    else:
        print("FAIL %s" % key, flush=True)
        failed.append(key)

    time.sleep(GAP)

print("\ndownloaded %d / %d" % (len(ok), len(IM)))
if failed:
    print("failed: %s" % ", ".join(failed))
    sys.exit(1)
