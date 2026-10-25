# AI CAD Bridge para Codex

Descarga la [versi�n instalable](https://github.com/Korz0/ai-cad-bridge/releases/tag/v0.2.0).

Plugin local para crear y modificar piezas y ensamblajes de Autodesk Inventor desde Codex, trabajando en **milímetros**.

**Versión 0.2.0 beta.** Inventor 2022 dispone de pruebas reales. Se habilitan Inventor 2017–2021 y 2023–2027 como **candidatos por compatibilidad de API**, pendientes de pruebas en esas versiones. No se presenta esa compatibilidad documental como certificación.

## Instalación sencilla

1. Ten instalados Windows, Inventor con licencia, Python de 64 bits 3.11–3.14 y Codex con soporte de plugins. Usa una versión de Windows admitida por tu Inventor.
2. Descarga el ZIP de este repositorio y extráelo en una carpeta permanente.
3. Ejecuta **INSTALL.cmd**. Prepara un entorno Python aislado, descarga dependencias, registra el catálogo local e instala el plugin. No requiere administrador.
4. Abre Inventor, reinicia Codex y comienza un chat local nuevo seleccionando **AI CAD Bridge**.

Los archivos se guardan por defecto en `Documentos\AI CAD Bridge`. Coloca allí también las fotos, planos y piezas de entrada. El instalador indica la ruta real, incluyendo carpetas Documentos redirigidas.

Si Codex no aparece en PATH, consulta [instalación manual y diagnóstico](docs/INSTALL.md). Para cambiar la carpeta:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Workspace "D:\Mis modelos"
```

## Ejemplos de solicitudes

> Crea un bloque de 40 × 30 × 10 mm, en un solo sólido y una sola operación. Pinta la cara superior azul y las demás negras. Guarda el IPT y una imagen de vista previa, y verifica las dimensiones.

> Modela esta carcasa según las fotos. Usa las medidas verificadas para la envolvente y marca como estimados los detalles calculados por proporción. Necesito un IPT monolítico con colores por cara.

> Modifica el parámetro Width de esta pieza a 120 mm y guarda una copia con un nombre nuevo.

Codex interpreta las imágenes; el puente ejecuta comandos CAD validados. Las proporciones de una foto no sustituyen medidas exactas. Los colores son apariencias visuales, no distintos materiales físicos dentro de un sólido.

Incluye croquis, restricciones, extrusiones, revoluciones, agujeros, redondeos, chaflanes, patrones, simetrías, planos, ensamblajes sencillos, exportación STEP/STL y vistas previas. La consolidación monolítica conserva el sólido y elimina el historial editable; conserva el comando JSON para reconstruirlo.

## Documentación

- [Compatibilidad y fuentes oficiales de Autodesk](docs/COMPATIBILITY.md)
- [Instalación, actualización y desinstalación](docs/INSTALL.md)
- [Formato de comandos](docs/COMMANDS.md)
- [Pruebas por versión](docs/TESTING.md)
- [Privacidad](PRIVACY.md) y [licencia MIT](LICENSE)

Este paquete está preparado para distribución mediante GitHub e instalación manual. No está publicado ni aprobado en el directorio oficial de OpenAI. No incluye Inventor, licencias de Autodesk ni modelos/fotografías personales del creador.
