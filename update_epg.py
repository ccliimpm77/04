import requests
import gzip
import xml.etree.ElementTree as ET
from io import BytesIO

# Configurazione
EPG_URL = "https://iptvx.one/epg/epg.xml.gz"
OUTPUT_FILE = "04.epg"

# Mappa di ricerca: se l'ID del sito contiene la "CHIAVE", lo rinominiamo nel "VALORE"
SEARCH_MAP = {
    "cnn_international": "CNN International",
    "eurosport_1": "Eurosport 1",
    "eurosport_2": "Eurosport 2"
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def main():
    print("--- 1. Download EPG (iptvx.one) ---")
    try:
        response = requests.get(EPG_URL, headers=HEADERS, timeout=60)
        response.raise_for_status()
        gz_data = BytesIO(response.content)
    except Exception as e:
        print(f"Errore download: {e}")
        return

    # Inizializziamo i contatori e una lista per gli ID effettivamente trovati
    found_source_ids = {} # Mappa: ID_Sorgente -> Nome_Nuovo
    count_ch = 0
    count_pr = 0

    print("--- 2. Filtraggio e Rinomina in corso ---")
    try:
        with gzip.GzipFile(fileobj=gz_data) as gz:
            with open(OUTPUT_FILE, 'wb') as f_out:
                f_out.write(b'<?xml version="1.0" encoding="UTF-8"?>\n<tv>\n')
                
                # Usiamo iterparse per processare il file enorme riga per riga
                context = ET.iterparse(gz, events=('start', 'end'))
                
                for event, elem in context:
                    # FASE A: Identifichiamo i CANALI e salviamo l'ID esatto usato dal sito
                    if event == 'end' and elem.tag == 'channel':
                        orig_id = elem.get('id', '')
                        orig_id_low = orig_id.lower()
                        
                        for key, new_name in SEARCH_MAP.items():
                            if key in orig_id_low:
                                found_source_ids[orig_id] = new_name
                                elem.set('id', new_name)
                                # Rinominiamo anche il nome visualizzato se esiste
                                display_name = elem.find('display-name')
                                if display_name is not None:
                                    display_name.text = new_name
                                
                                f_out.write(ET.tostring(elem, encoding='utf-8'))
                                count_ch += 1
                                print(f"Canale agganciato: {orig_id} -> {new_name}")
                        elem.clear()

                    # FASE B: Identifichiamo i PROGRAMMI usando la mappa creata sopra
                    elif event == 'end' and elem.tag == 'programme':
                        prog_channel = elem.get('channel', '')
                        
                        if prog_channel in found_source_ids:
                            # Rinominiamo l'attributo channel con il nome "pulito"
                            elem.set('channel', found_source_ids[prog_channel])
                            f_out.write(ET.tostring(elem, encoding='utf-8'))
                            count_pr += 1
                        elem.clear()

                f_out.write(b'</tv>\n')

        print(f"\n--- RISULTATO FINALE ---")
        print(f"Canali scritti: {count_ch}")
        print(f"Programmi scritti: {count_pr}")
        
        if count_pr == 0:
            print("ERRORE: Nonostante i canali, non sono stati trovati programmi.")
            print("Questo succede se l'ID dei programmi è diverso da quello dei canali nell'XML.")

    except Exception as e:
        print(f"Errore analisi XML: {e}")

if __name__ == "__main__":
    main()
