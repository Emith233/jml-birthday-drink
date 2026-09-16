from itertools import combinations
from pathlib import Path
import json, math, random
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageEnhance

ROOT = Path(__file__).resolve().parents[1]
MATERIAL_DIR = ROOT / '素材' / '调酒材料' / '独立版'
OUT_DIR = ROOT / '素材' / '饮品' / '220组合图'
OUT_DIR.mkdir(parents=True, exist_ok=True)

materials = [
    ('strawberry','草莓','01-草莓.png'), ('lemon','柠檬','02-柠檬.png'),
    ('mint','薄荷','03-薄荷.png'), ('honey','蜂蜜','04-蜂蜜.png'),
    ('soda','气泡水','05-气泡水.png'), ('star','星星糖','06-星星糖.png'),
    ('blueberry','蓝莓','07-蓝莓.png'), ('peach','桃子','08-桃子.png'),
    ('coffee','咖啡豆','09-咖啡豆.png'), ('cream','奶油','10-奶油.png'),
    ('orange','橙子','11-橙子.png'), ('cherry','樱桃','12-樱桃.png'),
]
palette = {
    'strawberry': (224, 112, 103), 'lemon': (242, 196, 70), 'mint': (129, 170, 119),
    'honey': (221, 158, 55), 'soda': (116, 190, 195), 'star': (232, 177, 66),
    'blueberry': (111, 111, 184), 'peach': (235, 156, 129), 'coffee': (127, 77, 48),
    'cream': (239, 226, 199), 'orange': (236, 143, 54), 'cherry': (180, 65, 72),
}

def rounded_material(path, size=184):
    src = Image.open(path).convert('RGB')
    src = ImageOps.fit(src, (size, size), method=Image.Resampling.LANCZOS)
    mask = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((2,2,size-3,size-3), radius=30, fill=255)
    card = Image.new('RGB', (size, size), '#f4e9d2')
    card.paste(src, (0,0), mask)
    return card

def make_image(combo, index):
    W = H = 900
    bg = Image.new('RGB', (W,H), '#fff8e9')
    draw = ImageDraw.Draw(bg)
    seed = sum((i + 1) * ord(c) for i, c in enumerate('|'.join(combo)))
    rng = random.Random(seed)
    colors = [palette[x] for x in combo]
    # soft table shadow
    shadow = Image.new('RGBA', (W,H), (0,0,0,0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse((260, 760, 640, 835), fill=(139, 103, 75, 32))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    bg = Image.alpha_composite(bg.convert('RGBA'), shadow)
    # Rotate through the 12 genuinely different independent drink illustrations.
    # Small deterministic variations keep every combination visually distinct.
    # The combination, rather than the sequential number, chooses the base style.
    # This keeps related ingredients visually coherent while avoiding a 12-image loop.
    base_no = (sum((materials.index(next(m for m in materials if m[0] == item)) + 1) * (n + 3)
                   for n, item in enumerate(combo)) % 12) + 1
    base_path = next((ROOT / '素材' / '饮品' / '独立版').glob(f'{base_no:02d}-*.png'))
    drink = Image.open(base_path).convert('RGB')
    # Deterministic per-combination variation: no two output files share all settings.
    size = 535 + rng.randint(0, 115)
    drink = ImageEnhance.Color(drink).enhance(0.78 + rng.random() * 0.48)
    drink = ImageEnhance.Brightness(drink).enhance(0.91 + rng.random() * 0.17)
    drink = ImageEnhance.Contrast(drink).enhance(0.92 + rng.random() * 0.2)
    drink = ImageOps.fit(drink, (size, size), method=Image.Resampling.LANCZOS)
    if rng.random() > 0.5:
        drink = ImageOps.mirror(drink)
    drink = drink.rotate(rng.uniform(-4.5, 4.5), resample=Image.Resampling.BICUBIC, expand=True, fillcolor='#fff8e9')
    bg.paste(drink, ((W-drink.width)//2 + rng.randint(-24,24), 12 + rng.randint(0, 32)))
    draw = ImageDraw.Draw(bg)
    # three exact materials, displayed as small watercolor ingredient swatches
    positions = [120, 358, 596]
    for x, material in zip(positions, combo):
        card = rounded_material(MATERIAL_DIR / next(m[2] for m in materials if m[0] == material), 184)
        bg.alpha_composite(card.convert('RGBA'), (x, 675))
    # small decorative dots, no drink name and no message baked into the art
    for _ in range(14):
        x, y = rng.randint(55,845), rng.randint(45,125)
        r = rng.randint(2,5)
        draw.ellipse((x-r,y-r,x+r,y+r), fill=(*colors[rng.randrange(3)], 75))
    return bg.convert('RGB')

rows = []
for index, combo in enumerate(combinations([m[0] for m in materials], 3), start=1):
    names = [next(m[1] for m in materials if m[0] == item) for item in combo]
    filename = f'{index:03d}-' + '_'.join(names) + '.png'
    make_image(combo, index).save(OUT_DIR / filename, optimize=True)
    rows.append({'id': f'combo_{index:03d}', 'ingredients': list(combo), 'ingredient_names': names, 'name': '', 'message': '', 'file': filename})

(OUT_DIR / '组合映射.json').write_text(json.dumps({'date':'9.17','count':len(rows),'items':rows}, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'generated {len(rows)} images')
