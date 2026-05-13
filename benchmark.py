import sys
import time

def execute_load(use_zenith):
    start = time.time()

    if use_zenith:
        import zenith
        zenith.ignite()

    import nerve
    import json
    import sqlite3
    import urllib.request
    import xml.etree.ElementTree
    import multiprocessing
    
    nerve_version = getattr(nerve, '__version__', 'unknown')
    
    end = time.time()
    return end - start

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else "traditional"
    
    if mode == "--zenith":
        time_taken = execute_load(use_zenith=True)
        print(f"Boot WITH Zenith: {time_taken:.5f} seconds")
    else:
        time_taken = execute_load(use_zenith=False)
        print(f"Boot WITHOUT Zenith: {time_taken:.5f} seconds")