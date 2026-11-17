"""Genera miniaturas 1280x720 para YouTube (originales, sin arte de Rockstar)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import render as R
from PIL import Image, ImageDraw

THUMBS = [
    ("v1_gta6_todo_lo_que_debes_saber", "ANTES DE JUGAR", "GTA 6", "Hora · Precio · 212 GB", R.YELLOW, 0, "stat"),
    ("v2_gta6_mapa_leonida_explicado", "6 REGIONES", "EL MAPA", "Leonida explicado", R.CYAN, 1, "map"),
    ("v3_gta6_personajes_jason_lucia", "¿QUIÉN ES QUIÉN?", "JASON + LUCIA", "Todos los personajes", R.PINK, 2, "card"),
    ("v4_gta6_pc_cuando_sale", "¿Y EN PC?", "¿CUÁNDO?", "La respuesta honesta", R.ORANGE, 0, "bars"),
]
out = sys.argv[1]
for slug, kicker, big, sub, col, var, kind in THUMBS:
    fr = Image.new("RGBA", (R.W, R.H), R.BG + (255,))
    if kind == "map":
        R.scene_map(fr, {"t": "map", "hl": "vice"}, 5, 10, 2.0)
        fr.alpha_composite(Image.new("RGBA", (R.W, R.H), (8, 4, 20, 90)))
    else:
        sky, hz = R.sunset_sky(var)
        fr.alpha_composite(sky)
        R.draw_grid(fr, hz, 0.3)
        fr.alpha_composite(Image.new("RGBA", (R.W, R.H), (8, 4, 20, 70)))
    d = ImageDraw.Draw(fr)
    # banda de color del "kicker"
    k = R.text_img(kicker, R.F_BLACK, 92, (15, 10, 30))
    kw = k.width - 2 * k.info["pad"] + 60
    d.polygon([(70, 90), (70 + kw + 40, 90), (70 + kw, 220), (70, 220)], fill=col + (255,))
    R.paste(fr, k, 100, 105)
    b = R.text_img(big, R.F_ITAL, 300 if len(big) < 10 else 210, R.WHITE, glow=col, stroke=8)
    R.paste(fr, b, 80, 300)
    s = R.text_img(sub, R.F_BLACK, 80, col, stroke=6)
    R.paste(fr, s, 100, 300 + b.height - 2 * b.info["pad"] + 30)
    fr.convert("RGB").resize((1280, 720), Image.LANCZOS).save(f"{out}/{slug}.jpg", quality=92)
print("ok")
