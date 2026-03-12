import os
import requests
import gzip
from lxml import etree
from deep_translator import GoogleTranslator

# Configurazione
EPG_URL = "https://iptvx.one/epg.xml.gz" # URL tipico di iptvx.one
CHANNELS_FILE = "canali.txt"
OUTPUT_FILE = "04.epg"

def translate_text(text, target_lang='it'):
    if not text or len(text) < 3:
        return text
    try:
        return GoogleTranslator(source='auto', target=target_lang).translate(text)
    except:
        return text

def main():
    # 1. Carica lista canali desiderati
    if not os.path.exists(CHANNELS_FILE):
        print(f"Errore: {CHANNELS_FILE} non trovato.")
        return
    
    with open(CHANNELS_FILE, 'r') as f:
        wanted_channels = [line.strip() for line in f if line.strip()]

    # 2. Scarica e decomprime EPG
    print("Scaricamento EPG...")
    r = requests.get(EPG_URL, stream=True)
    with open("temp_epg.xml.gz", "wb") as f:
        f.write(r.content)
    
    with gzip.open("temp_epg.xml.gz", 'rb') as f_in:
        xml_content = f_in.read()

    # 3. Parsing XML
    tree = etree.fromstring(xml_content)
    new_root = etree.Element("tv")
    
    # Copia attributi originali (es. generator-info-name)
    for key, value in tree.attrib.items():
        new_root.set(key, value)

    # 4. Filtra Canali
    print("Filtraggio canali...")
    for channel in tree.xpath("//channel"):
        if channel.get("id") in wanted_channels:
            new_root.append(channel)

    # 5. Filtra e Traduci Programmi
    print("Traduzione programmi (potrebbe richiedere tempo)...")
    programmes = tree.xpath("//programme")
    count = 0
    
    for prog in programmes:
        channel_id = prog.get("id")
        if channel_id in wanted_channels:
            # Traduzione Titolo
            title_node = prog.find("title")
            if title_node is not None:
                title_node.text = translate_text(title_node.text)
            
            # Traduzione Descrizione
            desc_node = prog.find("desc")
            if desc_node is not None:
                desc_node.text = translate_text(desc_node.text)
                
            new_root.append(prog)
            count += 1
            if count % 50 == 0:
                print(f"Processati {count} programmi...")

    # 6. Salvataggio
    with open(OUTPUT_FILE, "wb") as f:
        f.write(etree.tostring(new_root, encoding="utf-8", xml_declaration=True, pretty_print=True))
    
    print(f"Completato! File {OUTPUT_FILE} creato.")

if __name__ == "__main__":
    main()