import requests
import gzip
import xml.etree.ElementTree as ET
import os
from deep_translator import GoogleTranslator

# CONFIGURAZIONE
URL_SORGENTE = "https://iptvx.one/EPG"
FILE_CANALI = "canali.txt"
FILE_OUTPUT = "04.epg"

def main():
    print("1. Caricamento lista canali da filtrare...")
    if not os.path.exists(FILE_CANALI):
        print(f"Errore: {FILE_CANALI} non trovato!")
        return
    
    with open(FILE_CANALI, "r", encoding="utf-8") as f:
        canali_da_tenere = set(line.strip() for line in f if line.strip())

    print(f"Canali caricati: {len(canali_da_tenere)}")

    print("2. Scaricamento EPG in corso...")
    r = requests.get(URL_SORGENTE, timeout=60)
    with open("temp.xml.gz", "wb") as f:
        f.write(r.content)

    print("3. Decompressione e analisi (Parsing)...")
    translator = GoogleTranslator(source='auto', target='it')
    cache_traduzioni = {} # Per non tradurre due volte la stessa parola

    # Usiamo iterparse per evitare il loop infinito e il consumo di RAM
    with gzip.open("temp.xml.gz", "rb") as f_gz:
        context = ET.iterparse(f_gz, events=("start", "end"))
        
        # Prepariamo il file di output
        with open(FILE_OUTPUT, "wb") as f_out:
            f_out.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
            f_out.write(b'<tv>\n')

            for event, elem in context:
                if event == "end":
                    # Gestione Canali
                    if elem.tag == "channel":
                        channel_id = elem.get("id")
                        if channel_id in canali_da_tenere:
                            f_out.write(ET.tostring(elem, encoding="utf-8"))
                        elem.clear() # Libera memoria per evitare loop/blocchi

                    # Gestione Programmi + Traduzione
                    elif elem.tag == "programme":
                        channel_id = elem.get("channel")
                        if channel_id in canali_da_tenere:
                            # Traduzione Titolo
                            title = elem.find("title")
                            if title is not None and title.text:
                                testo = title.text
                                if testo not in cache_traduzioni:
                                    try:
                                        cache_traduzioni[testo] = translator.translate(testo)
                                    except:
                                        cache_traduzioni[testo] = testo
                                title.text = cache_traduzioni[testo]

                            # Traduzione Descrizione (opzionale, la ometto per velocità se vuoi)
                            desc = elem.find("desc")
                            if desc is not None and desc.text:
                                testo_d = desc.text
                                if testo_d not in cache_traduzioni:
                                    try:
                                        cache_traduzioni[testo_d] = translator.translate(testo_d)
                                    except:
                                        cache_traduzioni[testo_d] = testo_d
                                desc.text = cache_traduzioni[testo_d]

                            f_out.write(ET.tostring(elem, encoding="utf-8"))
                        elem.clear() # Fondamentale per la velocità

            f_out.write(b'</tv>')

    # Pulizia
    if os.path.exists("temp.xml.gz"):
        os.remove("temp.xml.gz")
    
    print(f"--- OPERAZIONE COMPLETATA: {FILE_OUTPUT} creato ---")

if __name__ == "__main__":
    main()
