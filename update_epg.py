import requests
import gzip
import xml.etree.ElementTree as ET
import os
from io import BytesIO

# Configurazione
EPG_URL = "https://iptvx.one/epg/epg.xml.gz"
CHANNELS_LIST_URL = "https://raw.githubusercontent.com/ccliimpm77/04/refs/heads/main/canali.txt"
OUTPUT_FILE = "04.epg"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def main():
    print("--- 1. Caricamento lista canali desiderati ---")
    try:
        r = requests.get(CHANNELS_LIST_URL, headers=HEADERS)
        r.raise_for_status()
        # Convertiamo tutto in minuscolo per evitare errori di battitura
        target_channels = set(line.strip().lower() for line in r.text.splitlines() if line.strip())
        print(f"Canali richiesti: {target_channels}")
    except Exception as e:
        print(f"Errore: impossibile leggere canali.txt: {e}")
        return

    print("\n--- 2. Download e analisi EPG (iptvx.one) ---")
    try:
        response = requests.get(EPG_URL, headers=HEADERS, stream=True)
        response.raise_for_status()
        
        # Decompressione in memoria dello stream
        with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
            with open(OUTPUT_FILE, 'wb') as f_out:
                # Scrittura intestazione XMLTV
                f_out.write(b'<?xml version="1.0" encoding="UTF-8"?>\n<tv>\n')
                
                count_ch = 0
                count_pr = 0
                
                # Parsing incrementale per risparmiare RAM
                context = ET.iterparse(gz, events=('end',))
                for event, elem in context:
                    # Controlla i tag <channel>
                    if elem.tag == 'channel':
                        channel_id = elem.get('id', '').lower()
                        if channel_id in target_channels:
                            f_out.write(ET.tostring(elem, encoding='utf-8'))
                            count_ch += 1
                    
                    # Controlla i tag <programme>
                    elif elem.tag == 'programme':
                        prog_id = elem.get('channel', '').lower()
                        if prog_id in target_channels:
                            f_out.write(ET.tostring(elem, encoding='utf-8'))
                            count_pr += 1
                    
                    # Pulisce la memoria
                    elem.clear()
                
                f_out.write(b'</tv>\n')

        print(f"OPERAZIONE COMPLETATA!")
        print(f"-> Canali estratti: {count_ch}")
        print(f"-> Programmi estratti: {count_pr}")
        
        if count_pr == 0:
            print("\n!!! ATTENZIONE: Il file è vuoto.")
            print("Verifica che in canali.txt ci siano gli ID corretti: cnni, eurosport1, eurosport2")

    except Exception as e:
        print(f"Errore durante l'elaborazione: {e}")

if __name__ == "__main__":
    main()
