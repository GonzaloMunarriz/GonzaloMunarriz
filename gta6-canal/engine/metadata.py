"""Genera PUBLICAR.md con títulos, descripciones (con capítulos reales), etiquetas y calendario."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..")
DISCLAIMER = ("Canal de fans no afiliado con Rockstar Games ni Take-Two Interactive. "
              "Grand Theft Auto y GTA son marcas de Take-Two Interactive. Todos los gráficos, la música y el "
              "mapa esquemático de este vídeo son originales.")

VIDEOS = [
    {
        "slug": "v1_gta6_todo_lo_que_debes_saber",
        "hora": "Jueves 19 · 00:30 (hora de España)",
        "titulos": [
            "GTA 6: TODO lo que debes saber ANTES de jugar (hora, precio, tamaño, PC y online)",
            "GTA 6 ya está aquí: hora de salida, cuánto ocupa y qué edición comprar",
            "No juegues a GTA 6 sin ver esto (hora de desbloqueo, 212 GB, PC y online)",
        ],
        "intro": ("GTA 6 sale el jueves 19 de noviembre de 2026. En este vídeo: a qué hora se desbloquea en España "
                  "y Latinoamérica, cuánto ocupa, Standard vs Ultimate, qué pasa con el PC y con GTA Online, y un "
                  "checklist para el día 1. Separando siempre lo confirmado de lo que es suposición."),
        "tags": "gta 6, gta vi, gta 6 hora de salida, gta 6 precio, gta 6 cuanto ocupa, gta 6 precarga, gta 6 pc, gta 6 online, gta 6 ultimate edition, gta 6 españa, gta 6 lanzamiento, grand theft auto 6",
    },
    {
        "slug": "v2_gta6_mapa_leonida_explicado",
        "hora": "Jueves 19 · 12:00 (hora de España)",
        "titulos": [
            "El MAPA de GTA 6 explicado: las 6 regiones de Leonida (y su versión real)",
            "GTA 6: así es el mapa de Leonida, región por región",
            "Vice City, Keys, Grassrivers… el mapa de GTA 6 explicado sin spoilers",
        ],
        "intro": ("Recorremos las 6 regiones confirmadas de Leonida en GTA 6: Vice City, Leonida Keys, Grassrivers, "
                  "Port Gellhorn, Ambrosia y Mount Kalaga. Qué ha enseñado Rockstar, en qué lugar real de Florida "
                  "se inspira cada una y qué podrás hacer allí. El mapa del vídeo es un esquema orientativo, no el oficial."),
        "tags": "gta 6 mapa, gta 6 map, leonida, vice city gta 6, gta 6 regiones, gta 6 mapa completo, gta 6 florida, leonida keys, grassrivers, port gellhorn, ambrosia, mount kalaga, gta vi",
    },
    {
        "slug": "v3_gta6_personajes_jason_lucia",
        "hora": "Jueves 19 · 18:00 (hora de España)",
        "titulos": [
            "GTA 6: Jason, Lucia y TODOS los personajes explicados (sin spoilers)",
            "¿Quién es quién en GTA 6? Guía de personajes antes de jugar",
            "Lucia y Jason: lo que debes saber de los protagonistas de GTA 6",
        ],
        "intro": ("Guía sin spoilers de los personajes de GTA 6 presentados oficialmente por Rockstar: Lucia Caminos, "
                  "Jason Duval, Brian Heder, Cal Hampton, Boobie Ike, Dre'Quan Priest, Real Dimez y Raul Bautista. "
                  "Sin filtraciones: solo información oficial y lo que se ve en los tráilers."),
        "tags": "gta 6 personajes, jason gta 6, lucia gta 6, gta 6 protagonistas, gta 6 historia, lucia caminos, jason duval, boobie ike, real dimez, raul bautista, cal hampton, brian heder, gta vi",
    },
    {
        "slug": "v4_gta6_pc_cuando_sale",
        "hora": "Viernes 20 · 18:00 (hora de España)",
        "titulos": [
            "¿Cuándo sale GTA 6 en PC? La respuesta honesta (con datos de Rockstar)",
            "GTA 6 PC: fecha estimada, requisitos y CUIDADO con las estafas",
            "GTA 6 no sale en PC… ¿esperar o comprar consola?",
        ],
        "intro": ("GTA 6 no tiene versión de PC anunciada. Repasamos cuánto tardó cada juego de Rockstar en llegar a "
                  "PC (GTA III, Vice City, San Andreas, GTA IV, GTA V y Red Dead Redemption 2) para estimar una ventana "
                  "realista, cómo evitar las descargas falsas y si te compensa esperar o comprar una consola. "
                  "La estimación es del canal, no oficial."),
        "tags": "gta 6 pc, gta 6 pc fecha, cuando sale gta 6 pc, gta 6 pc requisitos, gta 6 pc descargar, gta 6 pc estafa, gta 6 consola o pc, gta vi pc, rockstar pc",
    },
]


def main():
    out = ["# Paquete de publicación — GTA 6\n",
           "Sube cada vídeo **programado** en YouTube Studio con antelación y adjunta el `.srt` como subtítulos en español.\n",
           "**Antes de programar los vídeos, revisa la lista de comprobación de datos que está al final de este archivo.**\n"]
    for v in VIDEOS:
        cap_path = os.path.join(BASE, "salida", v["slug"] + "_capitulos.txt")
        caps = open(cap_path).read().strip() if os.path.exists(cap_path) else "(capítulos pendientes)"
        dur_line = ""
        mp4 = os.path.join(BASE, "salida", v["slug"] + ".mp4")
        out.append(f"\n---\n\n## {v['slug']}\n")
        out.append(f"- **Archivo:** `salida/{v['slug']}.mp4`  ·  **Subtítulos:** `salida/{v['slug']}.srt`  ·  **Miniatura:** `miniaturas/{v['slug']}.jpg`")
        out.append(f"- **Publicación recomendada:** {v['hora']}")
        out.append("\n**Título (elige uno; el primero es el recomendado):**\n")
        for t in v["titulos"]:
            out.append(f"- {t}  _({len(t)} caracteres)_")
        out.append("\n**Descripción (copiar y pegar):**\n")
        out.append("```")
        out.append(v["intro"])
        out.append("")
        out.append("CAPÍTULOS")
        out.append(caps)
        out.append("")
        out.append("Suscríbete: cobertura diaria de GTA 6 durante todo el lanzamiento.")
        out.append("")
        out.append(DISCLAIMER)
        out.append("")
        out.append("#GTA6 #GTAVI #Leonida")
        out.append("```")
        out.append(f"\n**Etiquetas:** {v['tags']}\n")
    open(os.path.join(BASE, "PUBLICAR.md"), "w").write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
