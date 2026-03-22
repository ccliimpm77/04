import urllib.request
import gzip
import shutil
import sys
import os

# CONFIGURAZIONE
SOURCE_URL = "https://iptvx.one/EPG"
OUTPUT_FILE = "04.epg"

def main():
    print(f"--- AVVIO AGGIORNAMENTO EPG ---")
    print(f"Sorgente: {SOURCE_URL}")
    print(f"Destinazione: {OUTPUT_FILE}")

    try:
        # 1. Configurazione richiesta con User-Agent per evitare blocchi dal server
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Encoding': 'gzip'
        }
        req = urllib.request.Request(SOURCE_URL, headers=headers)

        # 2. Apertura connessione
        with urllib.request.urlopen(req, timeout=120) as response:
            # Controlliamo se il server risponde con dati compressi (gzip)
            is_gzipped = response.info().get('Content-Encoding') == 'gzip' or SOURCE_URL.lower().endswith('.gz')
            
            print("Download e scrittura in corso (metodo streaming veloce)...")
            
            with open(OUTPUT_FILE, 'wb') as f_out:
                if is_gzipped:
                    # Decompressione al volo mentre scarica
                    with gzip.GzipFile(fileobj=response) as unzipped:
                        shutil.copyfileobj(unzipped, f_out)
                else:
                    # Scrittura diretta se non è compresso
                    shutil.copyfileobj(response, f_out)

        # 3. Verifica finale
        if os.path.exists(OUTPUT_FILE):
            size = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
            print(f"--- COMPLETATO ---")
            print(f"File creato: {OUTPUT_FILE} ({size:.2f} MB)")
        else:
            print("!!! Errore: Il file non è stato creato.")
            sys.exit(1)

    except Exception as e:
        print(f"!!! ERRORE CRITICO: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
