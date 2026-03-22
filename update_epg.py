import urllib.request
import gzip
import shutil
import os

# Configurazione
URL_SORGENTE = "https://raw.githubusercontent.com/ccliimpm77/04/main/04.xml.gz"
FILE_OUTPUT = "04.epg"

def main():
    print(f"Inizio download e creazione di {FILE_OUTPUT}...")
    try:
        # Scarichiamo e decomprimiamo al volo senza caricare tutto in RAM
        # Questo è il metodo più veloce possibile in Python
        with urllib.request.urlopen(URL_SORGENTE) as response:
            with gzip.GzipFile(fileobj=response) as unzipped:
                with open(FILE_OUTPUT, 'wb') as f_out:
                    shutil.copyfileobj(unzipped, f_out)
        
        print(f"Successo! File {FILE_OUTPUT} creato correttamente.")
    except Exception as e:
        print(f"Errore: {e}")
        exit(1)

if __name__ == "__main__":
    main()
