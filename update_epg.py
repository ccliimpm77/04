import requests
import gzip
import xml.etree.ElementTree as ET
from datetime import datetime
import io
import concurrent.futures

# --- CONFIGURAZIONE: INSERISCI QUI TUTTE LE TUE URL ---
SOURCES = [
    "https://raw.githubusercontent.com/ccliimpm77/04/main/04.xml.gz",
    # Aggiungi qui le altre URL che avevi nel file originale, separate da virgola
]

OUTPUT_FILE = "04.epg"

def fetch_and_extract(url):
    """Scarica, decompressa e trova canali/programmi indipendentemente dal namespace"""
    try:
        print(f"Scarico: {url}")
        with requests.Session() as s:
            r = s.get(url, timeout=60)
            r.raise_for_status()
            
        with gzip.GzipFile(fileobj=io.BytesIO(r.content)) as gzipped:
            xml_data = gzipped.read()
            
        # Parsing flessibile per ignorare i namespace
        root = ET.fromstring(xml_data)
        
        # Cerchiamo i tag ignorando i namespace (metodo più sicuro)
        # Alcuni file EPG usano <channel>, altri <ns:channel>
        channels = [elem for elem in root if 'channel' in elem.tag]
        programs = [elem for elem in root if 'programme' in elem.tag]
        
        print(f"Trovati {len(channels)} canali e {len(programs)} programmi in {url}")
        return channels, programs
    except Exception as e:
        print(f"Errore su {url}: {e}")
        return [], []

def main():
    start_time = datetime.now()
    
    all_channels = []
    all_programs = []

    # Parallelismo per massimizzare la velocità di download
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(SOURCES)) as executor:
        future_to_url = {executor.submit(fetch_and_extract, url): url for url in SOURCES}
        for future in concurrent.futures.as_completed(future_to_url):
            channels, programs = future.result()
            all_channels.extend(channels)
            all_programs.extend(programs)

    if not all_channels and not all_programs:
        print("ATTENZIONE: Nessun dato trovato. Verifica le URL o la struttura XML.")
        return

    # Costruzione veloce dell'XML finale
    new_root = ET.Element("tv")
    new_root.set("generator-info-name", "EPG-Optimizer-v2")

    # Aggiungiamo i dati trovati
    new_root.extend(all_channels)
    new_root.extend(all_programs)

    # Scrittura su file
    tree = ET.ElementTree(new_root)
    with open(OUTPUT_FILE, "wb") as f:
        tree.write(f, encoding="utf-8", xml_declaration=True)

    end_time = datetime.now()
    print(f"\n--- COMPLETATO ---")
    print(f"File creato: {OUTPUT_FILE}")
    print(f"Totale canali: {len(all_channels)}")
    print(f"Totale programmi: {len(all_programs)}")
    print(f"Tempo impiegato: {(end_time - start_time).total_seconds():.2f} secondi.")

if __name__ == "__main__":
    main()
