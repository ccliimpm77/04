import requests
import gzip
import xml.etree.ElementTree as ET
from io import BytesIO

# Configurazione
EPG_URL = "https://iptvx.one/epg/epg.xml.gz"
CHANNELS_LIST_URL = "https://raw.githubusercontent.com/ccliimpm77/04/refs/heads/main/canali.txt"
OUTPUT_FILE = "04.epg" # Puoi rinominarlo in 04.xml se il player fa storie

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def main():
    print("--- 1. Download lista canali ---")
    try:
        r = requests.get(CHANNELS_LIST_URL, headers=HEADERS)
        # Pulizia: togliamo spazi, righe vuote e convertiamo in minuscolo
        target_channels = set(line.strip().lower() for line in r.text.splitlines() if line.strip())
        print(f"Canali richiesti: {target_channels}")
    except Exception as e:
        print(f"Errore canali.txt: {e}")
        return

    print("\n--- 2. Analisi EPG Sorgente ---")
    try:
        response = requests.get(EPG_URL, headers=HEADERS, timeout=60)
        response.raise_for_status()
        
        with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
            # Creiamo il file di output con l'intestazione corretta per i player
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
                f_out.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f_out.write('<!DOCTYPE tv SYSTEM "xmltv.dtd">\n')
                f_out.write('<tv generator-info-name="CustomEPG">\n')
                
                count_ch = 0
                count_pr = 0
                
                # Iteriamo l'XML
                context = ET.iterparse(gz, events=('end',))
                for event, elem in context:
                    # Gestione Canali
                    if elem.tag == 'channel':
                        channel_id = elem.get('id', '').lower()
                        if channel_id in target_channels:
                            # Convertiamo l'elemento in stringa e lo scriviamo
                            xml_str = ET.tostring(elem, encoding='unicode')
                            f_out.write(f"  {xml_str}\n")
                            count_ch += 1
                    
                    # Gestione Programmi
                    elif elem.tag == 'programme':
                        prog_id = elem.get('channel', '').lower()
                        if prog_id in target_channels:
                            xml_str = ET.tostring(elem, encoding='unicode')
                            f_out.write(f"  {xml_str}\n")
                            count_pr += 1
                    
                    elem.clear() # Libera RAM
                
                f_out.write('</tv>')
        
        print(f"SUCCESSO! Creato {OUTPUT_FILE}")
        print(f"Canali: {count_ch} | Programmi: {count_pr}")

    except Exception as e:
        print(f"Errore durante l'elaborazione: {e}")

if __name__ == "__main__":
    main()
