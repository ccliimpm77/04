import urllib.request
import gzip
import xml.etree.ElementTree as ET
from datetime import datetime

# Configurazione
SOURCE_URL = "https://raw.githubusercontent.com/ccliimpm77/04/main/04.xml.gz"
OUTPUT_FILE = "04.epg"

def update_epg():
    start_time = datetime.now()
    print(f"Inizio: {start_time.strftime('%H:%M:%S')}")

    try:
        # 1. Scarica il file in streaming
        print(f"Scaricamento e decompressione di {SOURCE_URL}...")
        response = urllib.request.urlopen(SOURCE_URL, timeout=60)
        
        with gzip.GzipFile(fileobj=response) as gzipped:
            # 2. Inizializza il file di output
            with open(OUTPUT_FILE, 'wb') as f:
                f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write(b'<tv generator-info-name="Optimized-Generator">\n')

                # 3. Parsing iterativo (molto veloce, non occupa RAM)
                # Leggiamo il file a pezzi (event-based)
                context = ET.iterparse(gzipped, events=('end',))
                
                count_ch = 0
                count_pr = 0
                
                for event, elem in context:
                    # Cerchiamo canali o programmi (ignorando namespace)
                    if 'channel' in elem.tag or 'programme' in elem.tag:
                        # Scriviamo l'elemento direttamente nel file
                        f.write(ET.tostring(elem, encoding='utf-8'))
                        f.write(b'\n')
                        
                        if 'channel' in elem.tag: count_ch += 1
                        else: count_pr += 1
                        
                        # Liberiamo la memoria dell'elemento appena processato
                        elem.clear()
                
                f.write(b'</tv>')

        end_time = datetime.now()
        print(f"Completato in: {(end_time - start_time).total_seconds():.2f} secondi")
        print(f"Canali elaborati: {count_ch}")
        print(f"Programmi elaborati: {count_pr}")

    except Exception as e:
        print(f"ERRORE CRITICO: {e}")
        exit(1)

if __name__ == "__main__":
    update_epg()
