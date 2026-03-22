import requests
import gzip
import xml.etree.ElementTree as ET
from io import BytesIO
import xml.dom.minidom

# Configurazione
EPG_URL = "https://iptvx.one/epg/epg.xml.gz"
CHANNELS_LIST_URL = "https://raw.githubusercontent.com/ccliimpm77/04/refs/heads/main/canali.txt"
OUTPUT_FILE = "04.xml" # Cambiato in .xml per compatibilità

HEADERS = {'User-Agent': 'Mozilla/5.0'}

def prettify(elem):
    """Rende l'XML leggibile con invii a capo e spazi."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = xml.dom.minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def main():
    print("Scaricamento canali...")
    r = requests.get(CHANNELS_LIST_URL, headers=HEADERS)
    target_channels = set(line.strip().lower() for line in r.text.splitlines() if line.strip())

    print("Scaricamento e filtraggio EPG...")
    response = requests.get(EPG_URL, headers=HEADERS)
    
    with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
        tree = ET.parse(gz)
        root = tree.getroot()
        
        # Creiamo un nuovo contenitore XML
        new_root = ET.Element('tv', {
            'generator-info-name': 'CustomEPG',
            'source-info-name': 'iptvx.one'
        })

        # Aggiungiamo i canali
        for channel in root.findall('channel'):
            if channel.get('id', '').lower() in target_channels:
                new_root.append(channel)

        # Aggiungiamo i programmi
        for programme in root.findall('programme'):
            if programme.get('channel', '').lower() in target_channels:
                new_root.append(programme)

    # Scrittura file con formattazione pulita
    print(f"Salvataggio in {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(prettify(new_root))
    
    print("Operazione completata con successo.")

if __name__ == "__main__":
    main()
