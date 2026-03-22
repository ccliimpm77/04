import requests
import gzip
import xml.etree.ElementTree as ET
from io import BytesIO
import sys

# Configurazione URL
EPG_URL = "https://iptvx.one/epg/epg.xml.gz"
CHANNELS_LIST_URL = "https://raw.githubusercontent.com/ccliimpm77/04/refs/heads/main/canali.txt"
OUTPUT_FILE = "04.epg"

# Header per evitare il blocco 403 (Forbidden)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def main():
    print("1. Scaricamento lista canali dal tuo GitHub...")
    try:
        r = requests.get(CHANNELS_LIST_URL, headers=HEADERS)
        r.raise_for_status()
        # Pulizia: rimuove spazi vuoti e converte in set per velocità
        target_channels = set(line.strip() for line in r.text.splitlines() if line.strip())
        print(f"   --> Trovati {len(target_channels)} canali da filtrare nel tuo file.")
    except Exception as e:
        print(f"ERRORE scaricamento canali: {e}")
        return

    print("2. Scaricamento EPG da iptvx.one (con bypass anti-bot)...")
    try:
        response = requests.get(EPG_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        # Decompressione
        with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
            print("   Decompressione XML in corso...")
            xml_content = gz.read()
    except Exception as e:
        print(f"ERRORE scaricamento EPG: {e}")
        print("Il sito potrebbe aver bloccato la richiesta. Verifica l'URL o riprova più tardi.")
        return

    print("3. Analisi e filtraggio XML...")
    try:
        # Carichiamo l'XML
        root = ET.fromstring(xml_content)
        
        # Creiamo il nuovo contenitore XMLTV
        new_root = ET.Element('tv', root.attrib)
        
        count_ch = 0
        count_pr = 0

        # Filtriamo i Canali
        for channel in root.findall('channel'):
            channel_id = channel.get('id')
            if channel_id in target_channels:
                new_root.append(channel)
                count_ch += 1

        # Filtriamo i Programmi
        for programme in root.findall('programme'):
            prog_channel_id = programme.get('channel')
            if prog_channel_id in target_channels:
                new_root.append(programme)
                count_pr += 1

        print(f"   --> Canali aggiunti: {count_ch}")
        print(f"   --> Programmi aggiunti: {count_pr}")

        if count_pr == 0:
            print("\nATTENZIONE: Nessun programma trovato per i canali specificati!")
            print("Verifica che gli ID in canali.txt corrispondano esattamente agli ID dell'EPG.")
            # Stampiamo i primi 3 ID dell'EPG originale per debug
            sample_ids = [c.get('id') for c in root.findall('channel')[:3]]
            print(f"Esempio di ID validi nell'EPG sorgente: {sample_ids}")

        # Salvataggio
        tree = ET.ElementTree(new_root)
        tree.write(OUTPUT_FILE, encoding='utf-8', xml_declaration=True)
        print(f"\n4. Successo! File creato: {OUTPUT_FILE}")

    except Exception as e:
        print(f"ERRORE durante il parsing XML: {e}")

if __name__ == "__main__":
    main()
