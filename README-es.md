<div align="center">
  <h1>🚀 Zenith</h1>
  <p><b>Librería de optimización de arranque para aplicaciones Python.</b></p>
  
  [![PyPI Version](https://img.shields.io/pypi/v/alenia-zenith.svg?color=blueviolet)](https://pypi.org/project/alenia-zenith/)
  [![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-darkviolet.svg)](https://github.com/Kaia-Alenia/alenia-zenith)
  [![License](https://img.shields.io/badge/License-Alenia%20Studios%20Tool%201.0-8a2be2.svg)](LICENSE)
  [![Python](https://img.shields.io/badge/Python-3.10%2B-indigo.svg)](#)
  
  *Leer en [Inglés (English)](README.md).*
</div>

---

Zenith reduce el tiempo de importación de tu aplicación combinando **proxies de importación perezosa (lazy imports)** (los módulos no se ejecutan hasta que se accede a su primer atributo) y **precarga especulativa en segundo plano** (un pool de hilos precarga módulos conocidos mientras tu aplicación arranca). Una caché persistente aprende qué módulos usa tu aplicación entre ejecuciones, haciendo que cada arranque posterior sea más rápido.

> **¿Por qué usar Zenith?** Python 3.15 introduce lazy imports, pero Zenith va un paso más allá al *precargar* activamente los módulos en segundo plano basándose en el historial de ejecución, para que estén listos antes de que accedas a ellos.

## ✨ Características Principales y Casos de Uso

* ⚡ **Interfaces de Línea de Comandos (CLIs):** Consigue tiempos de inicio de sub-segundos para herramientas donde una latencia de +200ms arruina la experiencia del usuario.
* ☁️ **APIs Serverless (Cold Starts):** Reduce drásticamente los inicios en frío (cold starts) en entornos serverless (AWS Lambda, Google Cloud Run) permitiendo que el servidor escuche peticiones inmediatamente.
* 📊 **Data Science y Pipelines de ML:** Evita el retraso de inicialización de paquetes pesados (`pandas`, `numpy`, `torch`) durante ejecuciones frecuentes de scripts.
* 🖥️ **Aplicaciones de Escritorio / GUI:** Mejora el rendimiento percibido lanzando la interfaz principal al instante mientras las librerías secundarias cargan de forma asíncrona.

## 📈 Benchmarks

Pruebas ejecutadas en subprocesos aislados (promedio de 5 ejecuciones) cargando librerías pesadas (estándar y de terceros):

| Métrica         | Python Nativo | Zenith (en caliente) | Mejora |
|:----------------|:-------------:|:-------------:|:-----------:|
| Promedio Arranque | ~52ms         | ~37ms         | **~28%** 🚀 |

*(Nota: La primera ejecución construye la caché. Las ejecuciones posteriores se benefician de la precarga especulativa. Los resultados varían según el hardware y los módulos.)*

## 🛠️ Instalación

```bash
pip install alenia-zenith
```
*Para uso a nivel de sistema (Docker, CI/CD), añade `--break-system-packages`.*

## 🚀 Inicio Rápido

Inicializa Zenith en la parte más alta del archivo principal de tu aplicación:

```python
import zenith
zenith.ignite()

# Tus importaciones — servidas de forma perezosa y precargadas en segundo plano
import pandas as pd
import numpy as np
import requests
```

### Inicialización Avanzada

```python
import zenith

zenith.ignite(
    file=__file__,                    # Escanea las importaciones de este archivo y precárgalas
    workers=8,                        # Tamaño del pool de hilos en segundo plano (por defecto: 4)
    verbose=True,                     # Imprime eventos de precarga en stdout
    exclude=["mymodule", "django"],   # Nunca uses carga perezosa para estos paquetes
    cache_path=".cache/zenith.json",  # Ubicación personalizada para la caché
    show_banner=False,                # Oculta el banner ASCII
)

# Precarga explícitamente módulos específicos
zenith.warm("pandas", "numpy", "torch")
```

## ⚙️ Cómo Funciona

1. **Hook de Importación Perezosa (Lazy Import):** Inserta un sistema proxy en `sys.meta_path`. Las declaraciones `import` devuelven un `ZenithLazyModule` ligero en lugar de ejecutarse de inmediato.
2. **Precargador Especulativo:** Un `ThreadPoolExecutor` precarga los módulos cacheados en hilos en segundo plano, saltándose el sistema proxy para cargar los módulos reales.
3. **Caché Persistente:** Al salir, Zenith guarda los módulos utilizados en `.zenith_cache.json` para acelerar futuras ejecuciones.

## 💻 Herramientas CLI

Zenith proporciona un CLI integrado para diagnósticos y benchmarking:

```bash
# Analiza las importaciones en un archivo
zenith analyze myapp/main.py --verbose

# Muestra el estado de la caché
zenith status

# Ejecuta una comparación de rendimiento (benchmark)
zenith benchmark --runs 5 --modules pandas numpy requests

# Limpia la caché
zenith invalidate
```

## ⚠️ Limitaciones Conocidas

- **GIL (Global Interpreter Lock):** Zenith utiliza hilos estándar de Python. Los hilos en segundo plano comparten el GIL con el hilo principal, por lo que la precarga es concurrente, no paralela. La mejora de velocidad proviene de solapar las lecturas de disco (I/O-bound).
- **Primera Ejecución en Frío:** La primera ejecución no tiene caché y no mostrará mejoras de velocidad. La magia ocurre a partir de la segunda ejecución.
- **Extensiones en C:** Algunos módulos de extensiones en C no son seguros para importarse desde un hilo en segundo plano. Usa `zenith.exclude("nombre_modulo")` para estos casos.

## 📜 Licencia

Distribuido bajo la GNU General Public License v3 (GPL v3). Consulta el archivo [LICENSE](LICENSE) para más información.

Contacto: contact.aleniastudios@gmail.com
