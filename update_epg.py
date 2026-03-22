import requests
import gzip
import xml.etree.ElementTree as ET
from io import BytesIO

# Configurazione
EPG_URL = "https://iptvx.one/epg/epg.xml.gz"
CHANNELS_LIST_URL = "https://raw.githubusercontent.com/ccliimpm77/04/refs/heads/main/canali.txt"
OUTPUT_FILE = "04.epg"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def main():
    # 1. Scarica la tua lista canali
    print("Lettura lista canali target...")
    try:
        r = requests.get(CHANNELS_LIST_URL, headers=HEADERS)
        target_channels = set(line.strip() for line in r.text.splitlines() if line.strip())
        print(f"Canali da cercare: {len(target_channels)}")
    except Exception as e:
        print(f"Errore download canali: {e}")
        return

    # 2. Scarica l'EPG
    print("Scaricamento EPG (iptvx.one)...")
    try:
        response = requests.get(EPG_URL, headers=HEADERS, stream=True)
        response.raise_for_status()
        
        # Decomprime lo stream al volo
        compressed_file = BytesIO(response.content)
        decompressed_file = gzip.GzipFile(fileobj=compressed_file)
        
        # 3. Parsing incrementale (Memory Efficient)
        print("Filtraggio dati in corso (questo potrebbe richiedere 1-2 minuti)...")
        
        with open(OUTPUT_FILE, "wb") as f:
            # Scriviamo l'intestazione manuale per essere sicuri
            f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(b'<!DOCTYPE tv SYSTEM "xmltv.dtd">\n')
            f.write(b'<tv>\n')
            
            # Usiamo iterparse per non caricare tutto in RAM
            context = ET.iterparse(decompressed_file, events=('end',))
            
            count_ch = 0
            count_pr = 0
            
            for event, elem in context:
                if elem.tag == 'channel':
                    channel_id = elem.get('id')
                    if channel_id in target_channels:
                        f.write(ET.tostring(elem, encoding='utf-8'))
                        count_ch += 1
                
                elif elem.tag == 'programme':
                    prog_channel_id = elem.get('channel')
                    if prog_channel_id in target_channels:
                        f.write(ET.tostring(elem, encoding='utf-8'))
                        count_pr += 1
                
                # Molto importante: puliamo l'elemento dalla memoria dopo l'uso
                elem.clear()
            
            f.write(b'</tv>\n')
            
        print(f"Fatto! Canali trovati: {count_ch}, Programmi trovati: {count_pr}")
        
        if count_pr == 0:
            print("ATTENZIONE: Nessun programma trovato. Controlla che gli ID in canali.txt siano IDENTICI a quelli del sito.")

    except Exception as e:
        print(f"Errore durante l'elaborazione: {e}")

if __name__ == "__main__":
    main()
