# Zenith 2.0

Un framework de optimización de inicio adaptativo, observable y conservador para aplicaciones Python.

## ¿Qué es Zenith?
Zenith optimiza la **ruta de inicio** de las aplicaciones Python. Aprende de ejecuciones repetidas, identifica estrategias seguras de optimización y las aplica (como `PRELOAD` o `LAZY`) para reducir el tiempo de inicio de forma segura.

## Modos
- **PROFILE**: Mide y analiza con la semántica de importación normal.
- **SAFE**: Aprendizaje en tiempo de ejecución y optimizaciones explícitamente seguras (por defecto).
- **LAZY**: Habilita la carga perezosa para módulos explícitamente elegibles.
- **ADAPTIVE**: Utiliza evidencia acumulada para seleccionar entre EAGER, PRELOAD, LAZY o PROTECTED.
