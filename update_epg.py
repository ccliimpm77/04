import requests
import gzip
import xml.etree.ElementTree as ET
from io import BytesIO

# Configurazione URL
EPG_URL = "https://iptvx.one/epg/epg.xml.gz"
ORI_URL = "https://raw.githubusercontent.com/ccliimpm77/04/refs/heads/main/id.ori.txt"
M3U_URL = "https://raw.githubusercontent.com/ccliimpm77/04/refs/heads/main/id.m3u.txt"

def get_mapping():
    # Scarica i file e pulisce ogni riga da spazi bianchi o caratteri invisibili
    res_ori = requests.get(ORI_URL).text.splitlines()
    res_m3u = requests.get(M3U_URL).text.splitlines()
    
    ori_ids = [line.strip() for line in res_ori if line.strip()]
    m3u_ids = [line.strip() for line in res_m3u if line.strip()]
    
    # Crea un dizionario { 'ID_ORIGINALE': 'ID_NUOVO' }
    mapping = dict(zip(ori_ids, m3u_ids))
    print(f"Mappatura caricata: {len(mapping)} canali configurati.")
    return mapping

def process_epg():
    mapping = get_mapping()
    allowed_ori_ids = set(mapping.keys())

    print(f"Scaricamento EPG da {EPG_URL}...")
    response = requests.get(EPG_URL)
    
    # Decompressione e parsing
    with gzip.open(BytesIO(response.content), 'rb') as f:
        # Usiamo iterparse per gestire file grandi senza saturare la RAM
        context = ET.iterparse(f, events=('start', 'end'))
        
        # Creiamo il nuovo elemento radice
        new_root = ET.Element("tv", {"generator-info-name": "CustomEPG"})
        
        found_channels = 0
        found_programs = 0

        # Iteriamo attraverso l'XML
        for event, elem in context:
            if event == 'end':
                # Gestione CANALI
                if elem.tag == 'channel':
                    chan_id = elem.get('id')
                    if chan_id in allowed_ori_ids:
                        elem.set('id', mapping[chan_id])
                        new_root.append(elem)
                        found_channels += 1
                    else:
                        elem.clear() # Libera memoria
                
                # Gestione PROGRAMMI
                elif elem.tag == 'programme':
                    prog_chan_id = elem.get('channel')
                    if prog_chan_id in allowed_ori_ids:
                        elem.set('channel', mapping[prog_chan_id])
                        new_root.append(elem)
                        found_programs += 1
                    else:
                        elem.clear() # Libera memoria
                
                # Rimuovi elementi processati per risparmiare memoria
                if elem.tag not in ['channel', 'programme', 'tv']:
                    elem.clear()

    print(f"Filtraggio completato: {found_channels} canali e {found_programs} programmi trovati.")

    # Salvataggio file
    new_tree = ET.ElementTree(new_root)
    ET.indent(new_tree, space="  ", level=0)
    new_tree.write("04.xml", encoding="utf-8", xml_declaration=True)
    print("File 04.xml generato correttamente.")

if __name__ == "__main__":
    process_epg()
