import os
import requests
import gzip
from lxml import etree
from deep_translator import GoogleTranslator
import time

# --- CONFIGURAZIONE ---
EPG_URL = "https://iptvx.one/epg.xml.gz"  # Assicurati che questo URL sia corretto
CHANNELS_FILE = "canali.txt"
OUTPUT_FILE = "04.epg"

def translate_text(translator, text):
    if not text or len(str(text)) < 2:
        return text
    try:
        # Molto importante: delay per non farsi bloccare da Google
        time.sleep(0.3)
        return translator.translate(text)
    except Exception as e:
        return text

def main():
    print("--- INIZIO SCRIPT ---")
    translator = GoogleTranslator(source='auto', target='it')

    # 1. Verifica file canali.txt
    if not os.path.exists(CHANNELS_FILE):
        print(f"ERRORE: Il file {CHANNELS_FILE} non esiste nel repository.")
        # Creiamo un file di emergenza per non far crashare tutto
        with open(CHANNELS_FILE, "w") as f: f.write("Rai1.it")
        print(f"Creato {CHANNELS_FILE} di emergenza con Rai1.it")

    with open(CHANNELS_FILE, 'r') as f:
        wanted_channels = [line.strip() for line in f if line.strip()]
    
    print(f"Canali da cercare: {wanted_channels}")

    # 2. Download
    print(f"Scaricamento da: {EPG_URL}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36'}
        r = requests.get(EPG_URL, headers=headers, timeout=60)
        r.raise_for_status()
        print(f"Download riuscito. Dimensione file: {len(r.content)} bytes")
    except Exception as e:
        print(f"ERRORE DOWNLOAD: {e}")
        return

    # 3. Parsing XML
    try:
        # Verifica se è compresso GZIP
        if r.content.startswith(b'\x1f\x8b'):
            xml_data = gzip.decompress(r.content)
        else:
            xml_data = r.content
        
        tree = etree.fromstring(xml_data)
        print("Parsing XML completato con successo.")
    except Exception as e:
        print(f"ERRORE PARSING XML: {e}")
        print(f"Primi 100 caratteri ricevuti: {r.content[:100]}")
        return

    # 4. Creazione nuovo EPG
    new_root = etree.Element("tv")
    
    # Filtra Canali
    canali_trovati = 0
    for channel in tree.xpath("//channel"):
        if channel.get("id") in wanted_channels:
            new_root.append(channel)
            canali_trovati += 1
    print(f"Canali aggiunti all'EPG: {canali_trovati}")

    # Filtra e Traduci Programmi
    programmi_trovati = 0
    for prog in tree.xpath("//programme"):
        if prog.get("id") in wanted_channels:
            # Traduzione (opzionale: limitata a 100 per non bloccare l'action)
            if programmi_trovati < 100:
                title = prog.find("title")
                if title is not None: title.text = translate_text(translator, title.text)
                desc = prog.find("desc")
                if desc is not None: desc.text = translate_text(translator, desc.text)
            
            new_root.append(prog)
            programmi_trovati += 1
    
    print(f"Programmi aggiunti all'EPG: {programmi_trovati}")

    # 5. Scrittura file
    try:
        with open(OUTPUT_FILE, "wb") as f:
            f.write(etree.tostring(new_root, encoding="utf-8", xml_declaration=True, pretty_print=True))
        print(f"FILE {OUTPUT_FILE} CREATO CORRETTAMENTE!")
    except Exception as e:
        print(f"ERRORE SCRITTURA FILE: {e}")

    print("--- FINE SCRIPT ---")

if __name__ == "__main__":
    main()
