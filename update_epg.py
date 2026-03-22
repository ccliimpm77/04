import urllib.request
import gzip

# Configurazione
URL_SORGENTE = "https://iptvx.one/EPG"
FILE_OUTPUT = "04.epg"

def main():
    print(f"Scaricamento da: {URL_SORGENTE}")
    
    # 1. Scarica il file (legge tutto il contenuto compresso)
    response = urllib.request.urlopen(URL_SORGENTE)
    compressed_data = response.read()
    
    # 2. Decomprime i dati
    print("Decompressione in corso...")
    uncompressed_data = gzip.decompress(compressed_data)
    
    # 3. Salva il file finale
    print(f"Salvataggio in {FILE_OUTPUT}...")
    with open(FILE_OUTPUT, "wb") as f:
        f.write(uncompressed_data)

    print("Operazione completata.")

if __name__ == "__main__":
    main()
