import requests
import gzip
import xml.etree.ElementTree as ET
from io import BytesIO

# URL dei file
EPG_URL = "https://iptvx.one/epg/epg.xml.gz"
CHANNELS_LIST_URL = "https://raw.githubusercontent.com/ccliimpm77/04/refs/heads/main/canali.txt"
OUTPUT_FILE = "04.epg"

def main():
    print("1. Scaricamento lista canali desiderati...")
    try:
        response_channels = requests.get(CHANNELS_LIST_URL)
        response_channels.raise_for_status()
        # Creiamo un set di ID canali puliti (senza spazi e righe vuote)
        target_channels = set(line.strip() for line in response_channels.text.splitlines() if line.strip())
        print(f"   Trovati {len(target_channels)} canali nel tuo file canali.txt")
    except Exception as e:
        print(f"Errore durante il download della lista canali: {e}")
        return

    print("2. Scaricamento e decompressione EPG (questo potrebbe richiedere tempo)...")
    try:
        response_epg = requests.get(EPG_URL)
        response_epg.raise_for_status()
        
        # Decompressione in memoria
        with gzip.GzipFile(fileobj=BytesIO(response_epg.content)) as gz:
            xml_content = gz.read()
        print("   EPG scaricato e decompresso correttamente.")
    except Exception as e:
        print(f"Errore durante il download dell'EPG: {e}")
        return

    print("3. Filtraggio programmi in corso...")
    try:
        # Analisi dell'XML
        root = ET.fromstring(xml_content)
        
        # Creiamo un nuovo elemento radice per il file di output
        # Copiamo gli attributi del tag <tv> originale (es. generator-info-name)
        new_root = ET.Element('tv', root.attrib)

        # 1. Filtriamo i tag <channel>
        for channel in root.findall('channel'):
            channel_id = channel.get('id')
            if channel_id in target_channels:
                new_root.append(channel)

        # 2. Filtriamo i tag <programme>
        for programme in root.findall('programme'):
            channel_id = programme.get('channel')
            if channel_id in target_channels:
                new_root.append(programme)

        # Scrittura del file finale
        tree = ET.ElementTree(new_root)
        tree.write(OUTPUT_FILE, encoding='utf-8', xml_declaration=True)
        print(f"4. Operazione completata! File creato: {OUTPUT_FILE}")

    except Exception as e:
        print(f"Errore durante il filtraggio XML: {e}")

if __name__ == "__main__":
    main()
