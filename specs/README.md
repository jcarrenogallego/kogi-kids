# Specifications Directory

Este directorio contiene las especificaciones generadas por el workflow `video-generator-orchestrator`.

## Estructura

```
specs/
├── workflows/
│   └── {story-slug}/
│       ├── 00-style-selection.md
│       ├── 01-characters.md
│       ├── 02-dialogue.md
│       ├── 03-scenography.md
│       ├── 04-cinematography.md
│       ├── 05-script.md
│       └── 06-midjourney-prompts.md
└── README.md
```

## Propósito

- **Versionado**: Todas las especificaciones están bajo control de versiones (Git)
- **Trazabilidad**: Historial completo de cada workflow ejecutado
- **Recuperación**: Si Engram falla, las especificaciones persisten en archivos
- **Revisión**: Fácil comparación entre versiones usando diff de Git
- **Compartir**: Los archivos .md se pueden compartir con el equipo sin acceso a Engram

## Persistencia Dual

- **Engram**: Estado en memoria para recuperación entre sesiones (topic keys: `video-gen/{story-slug}/phase-{N}`)
- **Archivos .md**: Especificaciones versionadas en Git para trazabilidad y compartir

## Naming Convention

- `{story-slug}`: Título de la historia en kebab-case (ej: `luna-y-la-estrella-perdida`)
- `{NN}`: Número de fase (00-06) con zero-padding
- Fase 00: Style Selection (nueva)
- Fases 01-06: Agentes especializados
