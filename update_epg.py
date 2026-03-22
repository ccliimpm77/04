import requests
import gzip
import xml.etree.ElementTree as ET
import os

# Configurazione
URL_SORGENTE = "https://raw.githubusercontent.com/ccliimpm77/04/main/04.xml.gz"
FILE_OUTPUT = "04.epg"

def main():
    try:
        print(f"1. Scaricamento file da: {URL_SORGENTE}")
        # Scarichiamo tutto il file in memoria
        response = requests.get(URL_SORGENTE, timeout=30)
        response.raise_for_status()

        print("2. Decompressione in corso...")
        # Decomprimiamo i dati gzip
        xml_data = gzip.decompress(response.content)

        print("3. Analisi XML (Parsing)...")
        # Analizziamo l'XML nel modo standard
        root = ET.fromstring(xml_data)

        print(f"4. Scrittura del file {FILE_OUTPUT}...")
        # Creiamo l'albero XML e lo salviamo
        albero = ET.ElementTree(root)
        with open(FILE_OUTPUT, "wb") as f:
            albero.write(f, encoding="utf-8", xml_declaration=True)

        print("--- OPERAZIONE COMPLETATA CON SUCCESSO ---")

    except Exception as e:
        print(f"ERRORE: {e}")
        # Se c'è un errore, usciamo segnalandolo al sistema
        exit(1)

if __name__ == "__main__":
    main()
