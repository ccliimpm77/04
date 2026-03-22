import requests
import gzip
import xml.etree.ElementTree as ET
from io import BytesIO

# Configurazione
EPG_URL = "https://iptvx.one/epg/epg.xml.gz"
CHANNELS_LIST_URL = "https://raw.githubusercontent.com/ccliimpm77/04/refs/heads/main/canali.txt"
OUTPUT_FILE = "04.epg"

# Dizionario di sostituzione (Mappa gli ID tecnici ai nomi che vuoi tu)
REPLACEMENT_MAP = {
    "eurosport1": "Eurosport 1",
    "eurosport2": "Eurosport 2",
    "cnni": "CNN International"
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def main():
    print("--- 1. Download canali target ---")
    try:
        r = requests.get(CHANNELS_LIST_URL, headers=HEADERS)
        # Leggiamo gli ID originali dal file (es. cnni, eurosport1)
        target_ids = set(line.strip().lower() for line in r.text.splitlines() if line.strip())
        print(f"ID da cercare nel sorgente: {target_ids}")
    except Exception as e:
        print(f"Errore canali.txt: {e}")
        return

    print("\n--- 2. Elaborazione EPG con rinomina ID ---")
    try:
        response = requests.get(EPG_URL, headers=HEADERS, stream=True)
        response.raise_for_status()
        
        with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
            with open(OUTPUT_FILE, 'wb') as f_out:
                # Scrittura intestazione standard
                f_out.write(b'<?xml version="1.0" encoding="UTF-8"?>\n<tv>\n')
                
                count_ch = 0
                count_pr = 0
                
                # Parsing incrementale per non saturare la RAM
                context = ET.iterparse(gz, events=('end',))
                for event, elem in context:
                    
                    # --- FILTRAGGIO E RINOMINA CANALI (<channel>) ---
                    if elem.tag == 'channel':
                        orig_id = elem.get('id', '').lower()
                        if orig_id in target_ids:
                            # Se l'ID è nella mappa di sostituzione, lo cambiamo
                            new_id = REPLACEMENT_MAP.get(orig_id, orig_id)
                            elem.set('id', new_id)
                            
                            f_out.write(ET.tostring(elem, encoding='utf-8'))
                            count_ch += 1
                    
                    # --- FILTRAGGIO E RINOMINA PROGRAMMI (<programme>) ---
                    elif elem.tag == 'programme':
                        orig_id = elem.get('channel', '').lower()
                        if orig_id in target_ids:
                            # Se l'ID è nella mappa di sostituzione, lo cambiamo
                            new_id = REPLACEMENT_MAP.get(orig_id, orig_id)
                            elem.set('channel', new_id)
                            
                            f_out.write(ET.tostring(elem, encoding='utf-8'))
                            count_pr += 1
                    
                    elem.clear() # Libera memoria
                
                f_out.write(b'</tv>\n')

        print(f"\nFINITO!")
        print(f"-> Canali scritti: {count_ch}")
        print(f"-> Programmi scritti: {count_pr}")
        print(f"-> File generato: {OUTPUT_FILE}")
        print("\nGli ID sono stati rinominati come richiesto per il tuo player.")

    except Exception as e:
        print(f"Errore durante l'elaborazione: {e}")

if __name__ == "__main__":
    main()
