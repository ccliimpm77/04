import urllib.request
import gzip
import xml.etree.ElementTree as ET
import sys
from datetime import datetime

# Configurazione - Usa l'URL diretto
SOURCE_URL = "https://raw.githubusercontent.com/ccliimpm77/04/main/04.xml.gz"
OUTPUT_FILE = "04.epg"

def run():
    start_time = datetime.now()
    print(f"[{start_time.strftime('%H:%M:%S')}] Inizio elaborazione...")

    try:
        # 1. Download con Header per evitare blocchi
        req = urllib.request.Request(SOURCE_URL, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, timeout=60)
        
        # 2. Decompressione e parsing immediato (Streaming)
        # Usiamo iterparse per non caricare tutto il file in RAM
        with gzip.GzipFile(fileobj=response) as gzipped:
            context = ET.iterparse(gzipped, events=('start', 'end'))
            
            with open(OUTPUT_FILE, 'wb') as f:
                # Scriviamo l'intestazione manualmente per massima velocità
                f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write(b'<!DOCTYPE tv SYSTEM "xmltv.dtd">\n')
                f.write(b'<tv generator-info-name="FastEPG">\n')

                for event, elem in context:
                    # Quando finisce di leggere un tag 'channel' o 'programme'
                    if event == 'end':
                        tag_name = elem.tag.split('}')[-1] # Gestisce i namespace XML
                        
                        if tag_name in ['channel', 'programme']:
                            # Scrive l'elemento e lo distrugge dalla memoria
                            f.write(ET.tostring(elem, encoding='utf-8'))
                            f.write(b'\n')
                            elem.clear() 
                
                f.write(b'</tv>')

        duration = (datetime.now() - start_time).total_seconds()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Successo! Creato {OUTPUT_FILE} in {duration:.2f}s")

    except Exception as e:
        print(f"!!! ERRORE DURANTE L'ESECUZIONE: {e}")
        sys.exit(1) # Forza l'uscita con errore per il debug di GitHub

if __name__ == "__main__":
    run()
