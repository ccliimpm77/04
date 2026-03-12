import os
import requests
import gzip
from lxml import etree
from deep_translator import GoogleTranslator
import time

# Configurazione
EPG_URL = "https://iptvx.one/epg.xml.gz"
CHANNELS_FILE = "canali.txt"
OUTPUT_FILE = "04.epg"

def translate_text(translator, text):
    if not text or len(text) < 2:
        return text
    try:
        # Aggiunto un piccolo delay per non essere bannati da Google
        time.sleep(0.1)
        return translator.translate(text)
    except Exception as e:
        print(f"Errore traduzione: {e}")
        return text

def main():
    translator = GoogleTranslator(source='auto', target='it')
    
    # 1. Carica lista canali
    if not os.path.exists(CHANNELS_FILE):
        print(f"Errore: {CHANNELS_FILE} non trovato.")
        return
    
    with open(CHANNELS_FILE, 'r') as f:
        wanted_channels = [line.strip() for line in f if line.strip()]

    # 2. Scarica EPG con Headers per evitare blocchi
    print(f"Scaricamento EPG da {EPG_URL}...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        r = requests.get(EPG_URL, headers=headers, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"Errore durante il download: {e}")
        return

    with open("temp_epg.xml.gz", "wb") as f:
        f.write(r.content)
    
    # 3. Parsing
    print("Decompressione e analisi XML...")
    try:
        with gzip.open("temp_epg.xml.gz", 'rb') as f_in:
            tree = etree.parse(f_in)
    except Exception as e:
        print(f"Errore nel leggere il file XML: {e}")
        return

    root = tree.getroot()
    new_root = etree.Element("tv")
    
    # Copia attributi originali
    for key, value in root.attrib.items():
        new_root.set(key, value)

    # 4. Filtra Canali
    print(f"Filtraggio per {len(wanted_channels)} canali...")
    for channel in root.findall("channel"):
        if channel.get("id") in wanted_channels:
            new_root.append(channel)

    # 5. Filtra e Traduci Programmi
    print("Inizio traduzione programmi...")
    count = 0
    for prog in root.findall("programme"):
        channel_id = prog.get("id")
        if channel_id in wanted_channels:
            # Traduci Titolo
            title = prog.find("title")
            if title is not None and title.text:
                title.text = translate_text(translator, title.text)
            
            # Traduci Descrizione
            desc = prog.find("desc")
            if desc is not None and desc.text:
                desc.text = translate_text(translator, desc.text)
                
            new_root.append(prog)
            count += 1
            if count % 20 == 0:
                print(f"Processati {count} programmi...")

    # 6. Salvataggio
    print(f"Salvataggio in {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "wb") as f:
        f.write(etree.tostring(new_root, encoding="utf-8", xml_declaration=True, pretty_print=True))
    
    if os.path.exists("temp_epg.xml.gz"):
        os.remove("temp_epg.xml.gz")
        
    print("Operazione completata con successo.")

if __name__ == "__main__":
    main()
