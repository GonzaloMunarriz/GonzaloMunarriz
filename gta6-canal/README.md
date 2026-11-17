# Canal GTA 6 — 4 vídeos listos para el lanzamiento (19/11/2026)

Nombre provisional del canal: **MODO LEONIDA**. Para cambiarlo, vuelve a renderizar con `CHANNEL="TU NOMBRE"`.

| # | Vídeo | Búsqueda que ataca | Publicar |
|---|-------|--------------------|----------|
| 1 | Todo lo que debes saber antes de jugar | hora de salida, precio, cuánto ocupa, precarga | Jue 19 · 00:30 |
| 2 | El mapa de Leonida explicado | gta 6 mapa, regiones, vice city | Jue 19 · 12:00 |
| 3 | Jason, Lucia y todos los personajes | gta 6 personajes, quién es lucia | Jue 19 · 18:00 |
| 4 | ¿Cuándo sale GTA 6 en PC? | gta 6 pc, fecha pc, descargar pc | Vie 20 · 18:00 |

Todo lo necesario para subir los vídeos (títulos, descripciones con capítulos y etiquetas) está en **PUBLICAR.md**.

## Estructura
- `guiones/` — los guiones. Cada escena contiene el texto narrado (`say`) y el gráfico que la acompaña (`v`).
- `engine/render.py` — encadena guion → voz (Piper TTS, en local) → motion graphics → subtítulos → mezcla de música con *ducking* → MP4 1080p30 a −14 LUFS.
- `engine/music.py` — música synthwave generada por código. Es original, así que no hay riesgo de reclamaciones de Content ID.
- `engine/thumbs.py` — genera las miniaturas de 1280×720.
- `salida/` — los MP4, los `.srt` y los capítulos.

Para volver a renderizar un vídeo después de editar su guion:
```
pip install piper-tts pillow numpy
VOICE=/ruta/es_ES-voz.onnx python3 engine/render.py guiones/v1_todo_lo_que_saber.py salida/
```

## ⚠️ Comprobar los datos antes de publicar
Las afirmaciones siguientes proceden de prensa publicada antes del lanzamiento. Contrástalas con la web o las redes de Rockstar la noche del 18:
1. **Hora de desbloqueo: medianoche, hora local, en cada región.** Algunas plataformas usan una hora global. Si cambia, edita la escena "clock" del vídeo 1.
2. **Precio: 79,99 $ la Standard y 99,99 $ la Ultimate** (EE. UU.).
3. **Tamaño: "hasta ~212 GB".** La cifra viene de una sola fuente (Forbes, citada por buscadores).
4. **Precarga disponible desde el 10 de noviembre.**
5. **GTA Online sin anuncio oficial para el día 1.** Si Rockstar lo anuncia, el capítulo 5 del vídeo 1 queda obsoleto.
6. **Sin anuncio de versión para PC.** Si se anuncia, el vídeo 4 queda obsoleto (y lo que toca es un vídeo nuevo).

Los datos históricos (fechas de lanzamiento en PC de GTA III a RDR2, el lanzamiento de GTA Online en octubre de 2013, las descripciones oficiales de los personajes de mayo de 2025 y las 6 regiones) son sólidos.

## Lo que este paquete NO resuelve
- **Voz:** el modelo libre de Piper que estaba disponible (`es-mls_10246-low`) suena sintético y tiene acento castellano. Lo ideal es grabar tú mismo la narración leyendo `say`. Si es posible, conviene más voz humana que esta.
- **Política de YouTube:** desde 2025 los vídeos repetitivos o producidos en serie con voz IA pueden quedar fuera del Programa de Socios. Usa estos 4 vídeos para arrancar, pero a medio plazo el canal necesita tu voz, tu opinión o tu gameplay.
- **Gameplay:** no hay imágenes del juego, a propósito, para evitar reclamaciones de copyright de Rockstar y Take-Two. Desde el jueves, las grabaciones propias del juego son lo que más hará crecer el canal.
