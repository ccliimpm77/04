import requests
import gzip
import xml.etree.ElementTree as ET
from io import BytesIO

# Configurazione
EPG_URL = "https://iptvx.one/epg/epg.xml.gz"
CHANNELS_LIST_URL = "https://raw.githubusercontent.com/ccliimpm77/04/refs/heads/main/canali.txt"
OUTPUT_FILE = "04.epg"

# Mappa di conversione: 
# A SINISTRA: ID che troviamo nell'EPG originale
# A DESTRA: Come vogliamo che appaiano nel tuo file 04.epg
REPLACEMENT_MAP = {
    "eurosport1": "Eurosport 1",
    "eurosport2": "Eurosport 2",
    "cnni": "CNN International",
    "cnn_international": "CNN International", # Aggiunto ID alternativo
    "cnn": "CNN International"                # Aggiunto ID alternativo
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

def main():
    print("--- 1. Download canali da GitHub ---")
    try:
        r = requests.get(CHANNELS_LIST_URL, headers=HEADERS)
        # Carichiamo gli ID dal tuo file e aggiungiamo le varianti CNN per sicurezza
        target_ids = set(line.strip().lower() for line in r.text.splitlines() if line.strip())
        target_ids.update(["cnn_international", "cnn", "cnni"]) # Forza la ricerca di CNN
        print(f"ID ricercati: {target_ids}")
    except Exception as e:
        print(f"Errore canali.txt: {e}")
        return

    print("\n--- 2. Elaborazione EPG ---")
    try:
        response = requests.get(EPG_URL, headers=HEADERS, stream=True)
        response.raise_for_status()
        
        with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
            with open(OUTPUT_FILE, 'wb') as f_out:
                f_out.write(b'<?xml version="1.0" encoding="UTF-8"?>\n<tv>\n')
                
                count_ch = 0
                count_pr = 0
                
                context = ET.iterparse(gz, events=('end',))
                for event, elem in context:
                    
                    if elem.tag == 'channel':
                        orig_id = elem.get('id', '').lower()
                        if orig_id in target_ids:
                            new_id = REPLACEMENT_MAP.get(orig_id, orig_id)
                            elem.set('id', new_id)
                            f_out.write(ET.tostring(elem, encoding='utf-8'))
                            count_ch += 1
                            print(f"Trovato canale: {orig_id} -> rinominato in {new_id}")
                    
                    elif elem.tag == 'programme':
                        orig_id = elem.get('channel', '').lower()
                        if orig_id in target_ids:
                            new_id = REPLACEMENT_MAP.get(orig_id, orig_id)
                            elem.set('channel', new_id)
                            f_out.write(ET.tostring(elem, encoding='utf-8'))
                            count_pr += 1
                    
                    elem.clear()
                
                f_out.write(b'</tv>\n')

        print(f"\nFINITO! Programmi estratti: {count_pr}")

    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    main()
