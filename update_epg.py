import requests
import gzip
import xml.etree.ElementTree as ET
import os

# Configurazione
EPG_URL = "https://iptvx.one/epg/epg.xml.gz"
CHANNELS_LIST_URL = "https://raw.githubusercontent.com/ccliimpm77/04/refs/heads/main/canali.txt"
OUTPUT_FILE = "04.epg"
TEMP_GZ = "temp_epg.xml.gz"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

def main():
    # 1. Scarica la tua lista canali dal tuo GitHub
    print("--- FASE 1: Lettura canali.txt ---")
    try:
        r = requests.get(CHANNELS_LIST_URL, headers=HEADERS)
        r.raise_for_status()
        # Pulizia profonda: togliamo spazi e righe vuote
        target_channels = [line.strip() for line in r.text.splitlines() if line.strip()]
        print(f"Canali che stai cercando: {target_channels}")
    except Exception as e:
        print(f"Errore download canali.txt: {e}")
        return

    # 2. Scarica il file EPG intero
    print("\n--- FASE 2: Download EPG da iptvx.one ---")
    try:
        response = requests.get(EPG_URL, headers=HEADERS, stream=True)
        with open(TEMP_GZ, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download completato.")
    except Exception as e:
        print(f"Errore download EPG: {e}")
        return

    # 3. Processamento XML
    print("\n--- FASE 3: Filtraggio programmi ---")
    count_ch = 0
    count_pr = 0
    available_ids = [] # Per debug in caso di errore

    try:
        with gzip.open(TEMP_GZ, 'rb') as f_in:
            with open(OUTPUT_FILE, 'wb') as f_out:
                f_out.write(b'<?xml version="1.0" encoding="UTF-8"?>\n<tv>\n')
                
                context = ET.iterparse(f_in, events=('end',))
                for event, elem in context:
                    if elem.tag == 'channel':
                        cid = elem.get('id')
                        available_ids.append(cid) # Salviamo per farti vedere cosa c'è dentro
                        if cid in target_channels:
                            f_out.write(ET.tostring(elem, encoding='utf-8'))
                            count_ch += 1
                    
                    elif elem.tag == 'programme':
                        pid = elem.get('channel')
                        if pid in target_channels:
                            f_out.write(ET.tostring(elem, encoding='utf-8'))
                            count_pr += 1
                    
                    elem.clear() # Libera memoria
                
                f_out.write(b'</tv>\n')

        print(f"RISULTATO: Trovati {count_ch} canali e {count_pr} programmi.")

        # --- SEZIONE DEBUG: Se non trova nulla, ti aiuta a capire ---
        if count_pr == 0:
            print("\n!!! ATTENZIONE: Nessun programma trovato !!!")
            print("Probabilmente i nomi in 'canali.txt' sono diversi da quelli dell'EPG.")
            print("Ecco i primi 10 ID reali trovati nel file di iptvx.one (usa questi nel tuo canali.txt):")
            for correct_id in available_ids[:10]:
                print(f" -> {correct_id}")
        # ----------------------------------------------------------

    except Exception as e:
        print(f"Errore durante l'analisi XML: {e}")
    finally:
        if os.path.exists(TEMP_GZ):
            os.remove(TEMP_GZ)

if __name__ == "__main__":
    main()
