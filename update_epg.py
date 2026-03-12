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

def translate_text(translator, text):
    if not text or len(str(text)) < 3:
        return text
    try:
        # Piccolo delay per stabilità
        time.sleep(0.1)
        return translator.translate(text)
    except:
        return text

def main():
    print("--- INIZIO PROCESSO EPG ---")
    translator = GoogleTranslator(source='auto', target='it')

    # 1. Lettura canali da filtrare
    if not os.path.exists(CHANNELS_FILE):
        print(f"ERRORE: {CHANNELS_FILE} non trovato!")
        return
    
    with open(CHANNELS_FILE, 'r', encoding='utf-8') as f:
        wanted_list = [line.strip() for line in f if line.strip()]
    print(f"Canali richiesti da canali.txt: {len(wanted_list)}")

    # 2. Download
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(EPG_URL, headers=headers, timeout=60)
        r.raise_for_status()
        xml_content = gzip.decompress(r.content) if r.content.startswith(b'\x1f\x8b') else r.content
        tree = etree.fromstring(xml_content)
        print("XML scaricato e analizzato.")
    except Exception as e:
        print(f"ERRORE DOWNLOAD/PARSING: {e}")
        return

    # 3. Identificazione ID Canali corretti
    # Dobbiamo mappare i nomi in canali.txt con gli ID reali del file XML
    real_channel_ids = []
    new_root = etree.Element("tv")
    new_root.set("generator-info-name", "Custom-IT-EPG")

    for channel in tree.xpath("//channel"):
        c_id = channel.get("id")
        display_name = channel.findtext("display-name")
        
        if c_id in wanted_list or display_name in wanted_list:
            new_root.append(channel)
            real_channel_ids.append(c_id)
    
    print(f"ID canali identificati nell'XML: {real_channel_ids}")

    # 4. Filtra e Traduce Programmi
    # NOTA: Nei programmi l'attributo si chiama 'channel', non 'id'!
    print("Ricerca e traduzione programmi...")
    prog_count = 0
    
    for prog in tree.xpath("//programme"):
        channel_ref = prog.get("channel") # Questo era l'errore precedente
        
        if channel_ref in real_channel_ids:
            # Traduci Titolo
            title = prog.find("title")
            if title is not None and title.text:
                title.text = translate_text(translator, title.text)
            
            # Traduci Descrizione
            desc = prog.find("desc")
            if desc is not None and desc.text:
                desc.text = translate_text(translator, desc.text)
            
            new_root.append(prog)
            prog_count += 1
            
            if prog_count % 50 == 0:
                print(f"Processati {prog_count} programmi...")
            
            # Limite per non eccedere i tempi di GitHub Actions
            if prog_count >= 1000:
                break

    # 5. Salvataggio
    if prog_count > 0:
        with open(OUTPUT_FILE, "wb") as f:
            f.write(etree.tostring(new_root, encoding="utf-8", xml_declaration=True, pretty_print=True))
        print(f"SUCCESSO: Generato {OUTPUT_FILE} con {prog_count} programmi.")
    else:
        print("ERRORE: Non ho trovato programmi. Verifica che gli ID corrispondano.")

if __name__ == "__main__":
    main()
