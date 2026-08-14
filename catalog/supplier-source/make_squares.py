import os
from PIL import Image, ImageOps

SRC = "/tmp/extract_fresh2/images"
DST = "/tmp/thumbs_square"
os.makedirs(DST, exist_ok=True)

TARGET = 500  # output square size

def autocrop_and_square(path, out_path):
    im = Image.open(path).convert("RGB")
    # find bbox of non-near-white content
    gray = im.convert("L")
    # threshold: pixel darker than 245 counts as content
    bbox = gray.point(lambda p: 255 if p < 245 else 0).getbbox()
    if bbox is None:
        cropped = im
    else:
        x0,y0,x1,y1 = bbox
        # add margin
        mw = int((x1-x0) * 0.18) + 6
        mh = int((y1-y0) * 0.18) + 6
        x0 = max(0, x0-mw); y0 = max(0, y0-mh)
        x1 = min(im.width, x1+mw); y1 = min(im.height, y1+mh)
        cropped = im.crop((x0,y0,x1,y1))
    # pad to square (white bg), centered
    w,h = cropped.size
    side = max(w,h)
    canvas = Image.new("RGB", (side, side), (255,255,255))
    canvas.paste(cropped, ((side-w)//2, (side-h)//2))
    canvas = canvas.resize((TARGET,TARGET), Image.LANCZOS)
    canvas.save(out_path, "JPEG", quality=88)

files = sorted(os.listdir(SRC))
ok = 0
for f in files:
    try:
        out = os.path.join(DST, f.replace(".png",".jpg"))
        autocrop_and_square(os.path.join(SRC,f), out)
        ok += 1
    except Exception as e:
        print("FAIL", f, e)
print("done", ok, "/", len(files))
