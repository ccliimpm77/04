import urllib.request
import gzip
import shutil
import os
import sys

# Configurazione
URL_SORGENTE = "https://raw.githubusercontent.com/ccliimpm77/04/main/04.xml.gz"
FILE_OUTPUT = "04.epg"

def main():
    print("--- INIZIO PROCESSO ---")
    try:
        # Impostiamo un User-Agent per evitare che GitHub blocchi la richiesta
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(URL_SORGENTE, headers=headers)
        
        print(f"Scarico il file da: {URL_SORGENTE}")
        with urllib.request.urlopen(req, timeout=60) as response:
            # Leggiamo il file compresso e lo decomprimiamo direttamente nel file di output
            with gzip.GzipFile(fileobj=response) as unzipped:
                print(f"Decompressione e creazione di {FILE_OUTPUT}...")
                with open(FILE_OUTPUT, 'wb') as f_out:
                    # shutil.copyfileobj è il modo più veloce in Python per spostare dati
                    shutil.copyfileobj(unzipped, f_out)
        
        print(f"--- COMPLETATO: {FILE_OUTPUT} creato con successo ---")

    except Exception as e:
        # Se c'è un errore, lo stampiamo chiaramente prima di chiudere
        print("\n!!! ERRORE RISCONTRATO !!!")
        print(f"Dettaglio errore: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
