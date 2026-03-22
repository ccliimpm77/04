import requests
import gzip
import xml.etree.ElementTree as ET
from io import BytesIO

# Configurazione
EPG_URL = "https://iptvx.one/epg/epg.xml.gz"
OUTPUT_FILE = "04.epg"

# Mappa di conversione: 
# Se l'ID originale CONTIENE la chiave a sinistra, lo rinominiamo nel valore a destra.
# Usiamo parole chiave semplici per "beccare" qualsiasi variante del fornitore.
SEARCH_MAP = {
    "cnn_international": "CNN International",
    "eurosport_1": "Eurosport 1",
    "eurosport_2": "Eurosport 2"
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def main():
    print("--- 1. Download EPG Sorgente ---")
    try:
        response = requests.get(EPG_URL, headers=HEADERS, timeout=60)
        response.raise_for_status()
        gz_data = BytesIO(response.content)
        print("Download completato. Inizio analisi...")
    except Exception as e:
        print(f"Errore download: {e}")
        return

    # Mappa interna per collegare ID originali -> Nomi nuovi durante la scansione
    # Esempio: {"CNN_International.us": "CNN International"}
    matched_ids = {}

    try:
        with gzip.GzipFile(fileobj=gz_data) as gz:
            # Carichiamo tutto l'albero XML (per i 3 canali la memoria basterà)
            tree = ET.parse(gz)
            root = tree.getroot()
            
            # Creiamo il nuovo file XMLTV
            new_root = ET.Element('tv', {
                'generator-info-name': 'CustomEPG-v4',
                'source-info-name': 'iptvx.one'
            })

            # FASE 1: Scansione dei canali
            print("--- 2. Filtraggio Canali ---")
            for channel in root.findall('channel'):
                orig_id = channel.get('id', '')
                orig_id_low = orig_id.lower()
                
                for key, new_name in SEARCH_MAP.items():
                    if key in orig_id_low:
                        matched_ids[orig_id] = new_name
                        
                        # Creiamo il nuovo tag canale
                        new_ch = ET.Element('channel', {'id': new_name})
                        d_name = ET.SubElement(new_ch, 'display-name')
                        d_name.text = new_name
                        
                        # Copiamo l'icona se esiste
                        icon = channel.find('icon')
                        if icon is not None:
                            new_ch.append(icon)
                            
                        new_root.append(new_ch)
                        print(f"Canale trovato: {orig_id} -> Rinominato: {new_name}")
                        break

            # FASE 2: Scansione dei programmi
            print("--- 3. Filtraggio Programmi ---")
            count_p = 0
            for programme in root.findall('programme'):
                prog_ch_id = programme.get('channel', '')
                
                # Se il programma appartiene a uno degli ID che abbiamo "agganciato" prima
                if prog_ch_id in matched_ids:
                    # Lo cloniamo
                    new_prog = programme 
                    # CAMBIAMO L'ID del programma per farlo corrispondere al nuovo nome del canale
                    new_prog.set('channel', matched_ids[prog_ch_id])
                    
                    new_root.append(new_prog)
                    count_p += 1

            # Scrittura file finale
            print(f"--- 4. Salvataggio: {count_p} programmi trovati ---")
            out_tree = ET.ElementTree(new_root)
            with open(OUTPUT_FILE, 'wb') as f:
                f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write(b'<!DOCTYPE tv SYSTEM "xmltv.dtd">\n')
                out_tree.write(f, encoding='utf-8', xml_declaration=False)
            
            print(f"Fatto! File {OUTPUT_FILE} pronto.")

    except Exception as e:
        print(f"Errore durante l'analisi XML: {e}")

if __name__ == "__main__":
    main()
