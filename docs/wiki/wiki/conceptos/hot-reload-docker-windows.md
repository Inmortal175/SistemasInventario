---
title: "Hot-reload en Docker sobre Windows (inotify y polling)"
tags: [docker, windows, nextjs, entorno-desarrollo, infraestructura]
source_count: 1
---

# Hot-reload en Docker sobre Windows (inotify y polling)

## Definición
Los bind-mounts de Docker Desktop en Windows y macOS **no emiten eventos inotify**. Los
watchers de archivos que dependen de ellos (webpack/`next dev`, `nodemon`, etc.) nunca se
enteran de las ediciones hechas desde el host, y el hot-reload simplemente no ocurre.

## Cómo se manifestó
El dashboard seguía sirviendo el layout viejo tras editarlo. La pista fue el log del dev
server: compilaba páginas **nuevas** (`✓ Compiled /users`) pero nunca **recompilaba** las ya
compiladas. Las páginas nunca visitadas parecían funcionar; las demás quedaban congeladas.

Es la misma familia de problema que el directorio fantasma `frontend/C:/Program Files/Git/pnpm/store`,
creado cuando MSYS (Git Bash) traduce una ruta absoluta estilo Unix (`/pnpm/store`) antes de
pasársela al ejecutable.

## Solución
```yaml
# docker-compose.yml, servicio frontend
environment:
  WATCHPACK_POLLING: "true"
```
`next dev` con webpack usa Watchpack; la variable lo pone a sondear en vez de esperar
eventos. Equivalentes: `CHOKIDAR_USEPOLLING` para chokidar, `--poll` para nodemon.

Tras añadirla y recrear el contenedor, el hot-reload funciona: una edición al `Footer`
recompiló sola, sin reiniciar nada.

## Trampas relacionadas de Git Bash en este proyecto
| Síntoma | Causa | Remedio |
|---|---|---|
| `curl -F "file=@/tmp/x.png"` devuelve HTTP 000 | MSYS traduce `/tmp/...` | usar ruta relativa o `MSYS_NO_PATHCONV=1` |
| Python de Windows no lee `/tmp/a.html` | `/tmp` no es una ruta real de Windows | usar el directorio de scratch |
| Aparece `frontend/C:/Program Files/Git/...` | ruta Unix traducida y creada como relativa | anteponer `//` o usar PowerShell |

## Fuentes que lo mencionan
- [[fuentes/sesion-ajustes-branding-y-paginacion]] — diagnóstico y corrección

## Perspectivas/decisiones
El sondeo consume algo de CPU, pero en desarrollo el coste es irrelevante frente a editar
código que no se refleja. La variable solo se añadió al servicio `frontend` del compose de
desarrollo, no al de producción.

## Contradicciones detectadas
Ninguna.
