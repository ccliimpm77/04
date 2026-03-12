import os
import requests
import gzip
from lxml import etree
from deep_translator import GoogleTranslator
import time

# --- CONFIGURAZIONE ---
EPG_URL = "https://iptvx.one/EPG.xml.gz" 
CHANNELS_FILE = "canali.txt"
OUTPUT_FILE = "04.epg"

# Cache per non tradurre due volte la stessa parola
translation_cache = {}

def translate_text(translator, text):
    if not text or len(str(text)) < 3:
        return text
    
    if text in translation_cache:
        return translation_cache[text]
    
    try:
        # Delay ridotto grazie alla cache
        time.sleep(0.05)
        translated = translator.translate(text)
        translation_cache[text] = translated
        return translated
    except:
        return text

def main():
    print("--- INIZIO PROCESSO EPG (CON CACHE) ---")
    translator = GoogleTranslator(source='auto', target='it')

    # 1. Lettura canali
    if not os.path.exists(CHANNELS_FILE):
        print(f"ERRORE: {CHANNELS_FILE} non trovato!")
        return
    
    with open(CHANNELS_FILE, 'r', encoding='utf-8') as f:
        wanted_list = [line.strip() for line in f if line.strip()]

    # 2. Download
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(EPG_URL, headers=headers, timeout=60)
        r.raise_for_status()
        xml_content = gzip.decompress(r.content) if r.content.startswith(b'\x1f\x8b') else r.content
        tree = etree.fromstring(xml_content)
    except Exception as e:
        print(f"ERRORE DOWNLOAD: {e}")
        return

    # 3. Identificazione ID
    real_channel_ids = []
    new_root = etree.Element("tv")
    new_root.set("generator-info-name", "Custom-IT-EPG")

    for channel in tree.xpath("//channel"):
        c_id = channel.get("id")
        display_name = channel.findtext("display-name")
        if c_id in wanted_list or display_name in wanted_list:
            new_root.append(channel)
            real_channel_ids.append(c_id)
    
    print(f"Canali trovati: {len(real_channel_ids)}")

    # 4. Traduzione con Cache
    print("Inizio traduzione (molto più veloce con la cache)...")
    prog_count = 0
    
    # Prendiamo solo i programmi dei canali scelti
    programmes = [p for p in tree.xpath("//programme") if p.get("channel") in real_channel_ids]
    total_to_process = len(programmes)
    print(f"Programmi totali da elaborare: {total_to_process}")

    for prog in programmes:
        # Titolo
        title = prog.find("title")
        if title is not None and title.text:
            title.text = translate_text(translator, title.text)
        
        # Descrizione
        desc = prog.find("desc")
        if desc is not None and desc.text:
            desc.text = translate_text(translator, desc.text)
        
        new_root.append(prog)
        prog_count += 1
        
        # Feedback ogni 50 programmi
        if prog_count % 50 == 0:
            print(f"Progressi: {prog_count}/{total_to_process} (Cache size: {len(translation_cache)})")

    # 5. Salvataggio
    with open(OUTPUT_FILE, "wb") as f:
        f.write(etree.tostring(new_root, encoding="utf-8", xml_declaration=True, pretty_print=True))
    
    print(f"SUCCESSO: Generato {OUTPUT_FILE} con {prog_count} programmi.")

if __name__ == "__main__":
    main()
