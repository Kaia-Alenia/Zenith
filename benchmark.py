import sys
import time

def ejecutar_carga(usar_zenith):
    inicio = time.time()

    if usar_zenith:
        import zenith
        zenith.ignite()

    import nerve
    import json
    import sqlite3
    import urllib.request
    import xml.etree.ElementTree
    import multiprocessing
    
    nerve_version = getattr(nerve, '__version__', 'desconocida')
    
    fin = time.time()
    return fin - inicio

if __name__ == '__main__':
    modo = sys.argv[1] if len(sys.argv) > 1 else "tradicional"
    
    if modo == "--zenith":
        tiempo = ejecutar_carga(usar_zenith=True)
        print(f"Arranque CON Zenith: {tiempo:.5f} segundos")
    else:
        tiempo = ejecutar_carga(usar_zenith=False)
        print(f"Arranque SIN Zenith: {tiempo:.5f} segundos")