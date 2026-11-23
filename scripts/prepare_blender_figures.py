#!/usr/bin/env python3
"""Crop and label the author's Blender screenshots; no generative image tools.

The screenshot pixels are only cropped and resized. Text and leaders are drawn explicitly; the camera workflow is HTML/SVG
in the chapter. Originals are retained under scripts/data.
The selected Empty's orange rectangle is a reference image, not a camera frame.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'scripts/data/blender-screenshots'
OUTPUT = ROOT / 'book/assets/blender'
PAPER = '#fefdfb'
INK = '#252823'
GOLD = '#9a7422'
BLUE = '#5b8db8'


def font(size):
    candidates = [Path('/System/Library/Fonts/Supplemental/Arial.ttf'),
                  Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
    return ImageFont.truetype(str(next(p for p in candidates if p.exists())), size)


def crop(name, rect, target_width):
    image = Image.open(SOURCE / name).convert('RGB').crop(rect)
    height = round(image.height * target_width / image.width)
    return image.resize((target_width, height), Image.Resampling.LANCZOS)


def annotated(name, rect, filename, labels):
    """Fit both modeling views into matching frames without stretching or clipping."""
    width = 880
    source = Image.open(SOURCE / name).convert('RGB').crop(rect)
    scale = min(width / source.width, width / source.height)
    photo = source.resize((round(source.width * scale), round(source.height * scale)), Image.Resampling.LANCZOS)
    left, top = (width - photo.width) // 2, 112 + (width - photo.height) // 2
    canvas = Image.new('RGB', (width, width + 112), PAPER)
    ImageDraw.Draw(canvas).rectangle((0, 112, width, width + 112), fill='#303030')
    canvas.paste(photo, (left, top))
    draw = ImageDraw.Draw(canvas)
    for text, x, point, color in labels:
        draw.text((x, 25), text, fill=INK, font=font(34))
        start = (x + draw.textlength(text, font=font(34)) / 2, 75)
        px = left + (point[0] - rect[0]) * photo.width / source.width
        py = top + (point[1] - rect[1]) * photo.height / source.height
        draw.line([start, (start[0], 85), (px, py)], fill=color, width=4)
        draw.ellipse((px-6, py-6, px+6, py+6), fill=color, outline=PAPER, width=2)
    canvas.save(OUTPUT / filename, quality=92, subsampling=0)


def camera_view(name, title, camera_point=None):
    """Keep the full screenshot, with an equal-size frame and optional camera label."""
    source = Image.open(SOURCE / name).convert('RGB')
    scale = min(880 / source.width, 880 / source.height)
    photo = source.resize((round(source.width*scale), round(source.height*scale)), Image.Resampling.LANCZOS)
    canvas = Image.new('RGB', (880, 992), PAPER)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 112, 880, 992), fill='#3b3b3b')
    left, top = (880-photo.width)//2, 112+(880-photo.height)//2
    canvas.paste(photo, (left, top))
    text_x = 40 if camera_point is None or camera_point[0] < source.width/2 else 500
    draw.text((text_x, 25), title, fill=INK, font=font(34))
    if camera_point:
        start = (text_x+draw.textlength(title, font=font(34))/2, 75)
        point = (left+camera_point[0]*scale, top+camera_point[1]*scale)
        draw.line([start, (start[0], 90), point], fill='#e0bd69', width=4)
        px, py = point
        draw.ellipse((px-6, py-6, px+6, py+6), fill='#e0bd69', outline=PAPER, width=2)
    canvas.save(OUTPUT/Path(name).with_suffix('.jpg').name, quality=94, subsampling=0)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    annotated('reference-front.png', (490, 310, 1540, 1340), 'mesh-reference.jpg', [
        ('3D mesh', 45, (880, 792), BLUE),
        ('2D reference image', 500, (1474, 490), GOLD),
    ])
    annotated('mesh-oblique.png', (45, 110, 710, 948), 'mesh-oblique.jpg', [
        ('Small flat faces', 48, (240, 469), BLUE),
        ('Reference image', 530, (701, 288), GOLD),
    ])
    crop('workspace.png', (1230, 530, 1835, 1210), 880).save(OUTPUT/'scene-viewport.jpg', quality=92, subsampling=0)
    crop('workspace.png', (240, 800, 1100, 1630), 880).save(OUTPUT/'render-gray.jpg', quality=92, subsampling=0)
    crop('render-color.png', (170, 410, 1010, 1245), 1000).save(OUTPUT/'render-color.jpg', quality=93, subsampling=0)
    camera_view('camera-setup-a.png', 'Virtual camera', (21, 79))
    camera_view('camera-view-a.png', 'View A · viewport preview')
    camera_view('camera-setup-b.png', 'Virtual camera', (333, 218))
    camera_view('camera-view-b.png', 'View B · viewport preview')
    print('Prepared nine annotated or cropped screenshots.')


if __name__ == '__main__':
    main()
