import requests
import gzip
import xml.etree.ElementTree as ET
from datetime import datetime
import io
import concurrent.futures # Per l'esecuzione parallela

# Configurazione
SOURCES = [
    "https://raw.githubusercontent.com/ccliimpm77/04/main/04.xml.gz",
    # Aggiungi qui altre URL se presenti nel tuo file originale
]

OUTPUT_FILE = "04.epg"

def fetch_and_process(url):
    """Scarica e processa una singola sorgente"""
    try:
        session = requests.Session()
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        # Decompressione in memoria
        with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as gzipped:
            xml_content = gzipped.read()
            
        root = ET.fromstring(xml_content)
        channels = root.findall('channel')
        programs = root.findall('programme')
        
        return channels, programs
    except Exception as e:
        print(f"Errore durante l'elaborazione di {url}: {e}")
        return [], []

def main():
    start_time = datetime.now()
    print(f"Inizio aggiornamento EPG: {start_time}")

    all_channels = []
    all_programs = []

    # Utilizzo di ThreadPoolExecutor per scaricare i file in parallelo
    # max_workers=5 è un buon compromesso per non sovraccaricare la rete
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(fetch_and_process, SOURCES))

    # Accorpa i risultati
    for channels, programs in results:
        all_channels.extend(channels)
        all_programs.extend(programs)

    # Creazione del nuovo file XML (EPG)
    new_root = ET.Element("tv")
    new_root.set("generator-info-name", "Custom EPG Generator Optimized")

    # Aggiunta canali e programmi
    for channel in all_channels:
        new_root.append(channel)
    for program in all_programs:
        new_root.append(program)

    # Scrittura veloce su file
    tree = ET.ElementTree(new_root)
    with open(OUTPUT_FILE, "wb") as f:
        # L'uso di encoding='utf-8' e xml_declaration=True è standard
        tree.write(f, encoding="utf-8", xml_declaration=True)

    end_time = datetime.now()
    duration = end_time - start_time
    print(f"File {OUTPUT_FILE} creato con successo in {duration.total_seconds():.2f} secondi.")

if __name__ == "__main__":
    main()
