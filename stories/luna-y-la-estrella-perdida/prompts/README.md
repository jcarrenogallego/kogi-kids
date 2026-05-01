# 🎬 Luna y la Estrella Perdida - MidJourney Workflow

Este documento explica cómo generar las 26 imágenes clave de la historia usando MidJourney V7 con la Web UI y las imágenes de referencia del moodboard.

---

## ⚙️ Setup (Una Sola Vez)

1. **Asegurate de tener una suscripción activa de MidJourney**
2. **Tené las imágenes del moodboard listas**:
   - `../moodboard/luna.png`
   - `../moodboard/estrellita.png`
   - `../moodboard/oliver.png`
   - `../moodboard/luciernaga.png`

3. **Abrí el archivo de prompts**:
   - `prompts.md` (inglés, para MidJourney)
   - `prompts-es.md` (español, para tu revisión)

---

## 📋 Workflow para Cada Prompt (26 Prompts Total)

### Paso 1: Ir a MidJourney Web UI
- URL: https://midjourney.com/imagine
- **NO uses Discord** — la Web UI es necesaria para subir imágenes de referencia

### Paso 2: Subir Imagen de Referencia
1. Hacé clic en el botón **"Image Prompts"** (arriba del campo de prompt)
2. Subí la imagen del personaje según el prompt:
   - **Prompts con Luna**: `moodboard/luna.png`
   - **Prompts con Estrellita**: `moodboard/estrellita.png`
   - **Prompts con Oliver**: `moodboard/oliver.png`
   - **Prompts con Luciérnagas**: `moodboard/luciernaga.png`
   - **Prompts con múltiples personajes**: Subir 2-3 imágenes (ej: Luna + Estrellita)

### Paso 3: Copiar y Pegar el Prompt
1. Abrí `prompts.md` (versión inglés)
2. Encontrá el prompt que querés generar (ej: Prompt 1A)
3. Copiá el texto del bloque de código (todo, incluyendo `/imagine`)
4. Pegá en el campo de prompt de MidJourney
5. **NO modifiques** los parámetros `--ar 16:9 --v 7 --sref 1234567890 --sw 200`

### Paso 4: Generar y Seleccionar
1. Hacé clic en **Generate** (o Enter)
2. Esperá ~60 segundos
3. MidJourney te muestra 4 variaciones
4. Elegí la mejor haciendo clic en **U1**, **U2**, **U3**, o **U4** (upscale)
5. Esperá otros ~30 segundos para la versión en alta resolución

### Paso 5: Descargar y Guardar
1. Descargá la imagen en alta resolución
2. Guardá en la carpeta `renders/` con el nombre apropiado:
   - `1a-bedroom-establishing.png`
   - `1b-luna-closeup-wonder.png`
   - `2a-outside-window-establishing.png`
   - ... y así para los 26 prompts

---

## 🎯 Estructura de Nombres de Archivos

```
renders/
├── 1a-bedroom-establishing.png
├── 1b-luna-closeup-wonder.png
├── 2a-outside-window-establishing.png
├── 2b-estrellita-falling.png
├── 2c-luna-and-estrellita-meet.png
├── 3a-magical-forest-establishing.png
├── 3b-luna-estrellita-walking.png
├── 3c-oliver-appears.png
├── 3d-oliver-closeup.png
├── 3e-trio-group-shot.png
├── 4a-stream-establishing.png
├── 4b-luna-worried-crossing.png
├── 4c-oliver-helps.png
├── 4d-estrellita-glows-brighter.png
├── 5a-crystal-cave-establishing.png
├── 5b-fireflies-appear.png
├── 5c-fireflies-create-constellation.png
├── 5d-trio-group-shot-cave.png
├── 5e-estrellita-transformation.png
├── 6a-night-sky-establishing.png
├── 6b-luna-sad.png
├── 6c-sky-brightens.png
├── 6d-estrellita-shines-bright.png
├── 6e-luna-smiles.png
├── 7a-bedroom-establishing.png
├── 7b-luna-sleeping.png
└── 7c-window-view-estrellita.png
```

---

## 📊 Progreso

Usá esta checklist para trackear tu progreso:

- [ ] **Scene 1 - Bedroom** (2 prompts)
  - [ ] 1A - Bedroom Establishing Shot
  - [ ] 1B - Luna Close-up Wonder

- [ ] **Scene 2 - Outside Window** (3 prompts)
  - [ ] 2A - Outside Window Establishing
  - [ ] 2B - Estrellita Falling
  - [ ] 2C - Luna and Estrellita Meet

- [ ] **Scene 3 - Magical Forest** (5 prompts)
  - [ ] 3A - Magical Forest Establishing
  - [ ] 3B - Luna & Estrellita Walking
  - [ ] 3C - Oliver Appears
  - [ ] 3D - Oliver Close-up
  - [ ] 3E - Trio Group Shot

- [ ] **Scene 4 - Crystal Stream** (4 prompts)
  - [ ] 4A - Stream Establishing
  - [ ] 4B - Luna Worried Crossing
  - [ ] 4C - Oliver Helps
  - [ ] 4D - Estrellita Glows Brighter

- [ ] **Scene 5 - Crystal Cave** (5 prompts)
  - [ ] 5A - Crystal Cave Establishing
  - [ ] 5B - Fireflies Appear
  - [ ] 5C - Fireflies Create Constellation
  - [ ] 5D - Trio Group Shot Cave
  - [ ] 5E - Estrellita Transformation

- [ ] **Scene 6 - Return to Sky** (4 prompts)
  - [ ] 6A - Night Sky Establishing
  - [ ] 6B - Luna Sad
  - [ ] 6C - Sky Brightens
  - [ ] 6D - Estrellita Shines Bright
  - [ ] 6E - Luna Smiles

- [ ] **Scene 7 - Bedroom (Morning)** (3 prompts)
  - [ ] 7A - Bedroom Establishing (Morning)
  - [ ] 7B - Luna Sleeping
  - [ ] 7C - Window View Estrellita

---

## ⏱️ Tiempo Estimado

- **Por prompt**: ~2-3 minutos (upload + generar + seleccionar + descargar)
- **26 prompts**: ~60-90 minutos total
- **Recomendación**: Hacelo en 2-3 sesiones para evitar fatiga

---

## 🎨 Parámetros Técnicos (NO Modificar)

Todos los prompts usan estos parámetros para consistencia visual:

- **`--v 7`**: MidJourney Version 7 (máxima calidad)
- **`--ar 16:9`**: Aspect ratio 16:9 (formato video)
- **`--sref 1234567890`**: Style reference seed (mantiene estilo Disney 3D consistente)
- **`--sw 200`**: Style weight 200 (fuerte adherencia al estilo)

---

## ❓ Troubleshooting

### Problema: "Invalid parameter --cref"
- **Solución**: Asegurate de usar la **Web UI**, NO Discord. La Web UI permite subir imágenes manualmente sin usar `--cref`.

### Problema: El personaje no se parece al moodboard
- **Solución**: Verificá que subiste la imagen correcta en "Image Prompts" ANTES de generar.

### Problema: La imagen está muy oscura/clara
- **Solución**: Probá otras variaciones (U1/U2/U3/U4) o regenerá el prompt.

### Problema: Quiero cambiar algo del prompt
- **Solución**: Editá el prompt en `prompts.md`, pero NO modifiques los parámetros técnicos (`--v 7`, `--sref`, etc.) para mantener consistencia.

---

## 🚀 Próximos Pasos

Una vez que tengas las 26 imágenes en `renders/`:

1. **Revisá la calidad** de todas las imágenes
2. **Animá con Runway Gen-3**:
   - Subí cada imagen a Runway
   - Aplicá el modo "Motion" (duración según el script: 6-10 segundos por shot)
   - Descargá los videos renderizados
3. **Editá el video final** con tu editor preferido (DaVinci Resolve, Premiere, Final Cut)
4. **Agregá audio**: música de fondo + voiceover

---

## 📝 Notas

- Este workflow fue diseñado después de probar múltiples estrategias (Discord con `--cref`, V6 con `--cref`, etc.)
- La combinación **Web UI + V7 + Manual Upload** es la que da mejor calidad Y consistencia de personajes
- Los prompts están en inglés porque MidJourney funciona mejor con inglés técnico
- El archivo `prompts-es.md` es solo para tu revisión, no para copiar a MidJourney
