import urllib.request
import gzip
import xml.etree.ElementTree as ET
import os

# Configurazione
URL_SORGENTE = "https://iptvx.one/EPG"
FILE_GZ = "04.xml.gz"
FILE_XML = "04.xml"
FILE_OUTPUT = "04.epg"

def main():
    try:
        # 1. DOWNLOAD (Senza librerie esterne per evitare errori su GitHub)
        print(f"Scaricamento da {URL_SORGENTE}...")
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(URL_SORGENTE, headers=headers)
        with urllib.request.urlopen(req) as response, open(FILE_GZ, 'wb') as f:
            f.write(response.read())

        # 2. DECOMPRESSIONE
        print("Decompressione in corso...")
        with gzip.open(FILE_GZ, 'rb') as f_in:
            with open(FILE_XML, 'wb') as f_out:
                f_out.write(f_in.read())

        # 3. FILTRO CANALI (Basato su canali.txt)
        if os.path.exists("canali.txt"):
            print("Filtraggio canali basato su canali.txt...")
            with open("canali.txt", "r", encoding="utf-8") as f:
                canali_validi = set(line.strip() for line in f if line.strip())
            
            tree = ET.parse(FILE_XML)
            root = tree.getroot()
            
            # Rimuoviamo i canali e i programmi non presenti in canali.txt
            for child in list(root):
                # Controlla l'id per i tag 'channel' e l'attributo 'channel' per i tag 'programme'
                cid = child.get('id') if child.tag == 'channel' else child.get('channel')
                if cid not in canali_validi:
                    root.remove(child)
            
            print(f"Scrittura file filtrato: {FILE_OUTPUT}")
            tree.write(FILE_OUTPUT, encoding="utf-8", xml_declaration=True)
        else:
            # Se canali.txt non esiste, rinomina semplicemente il file
            print("canali.txt non trovato. Creo copia intera.")
            os.replace(FILE_XML, FILE_OUTPUT)

        print("--- OPERAZIONE COMPLETATA ---")

    except Exception as e:
        print(f"ERRORE: {e}")
        exit(1)

if __name__ == "__main__":
    main()
