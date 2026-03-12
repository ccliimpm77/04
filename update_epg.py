import os
import requests
import gzip
from lxml import etree
from deep_translator import GoogleTranslator
import time

# --- CONFIGURAZIONE ---
# L'URL corretto deve avere EPG in maiuscolo
EPG_URL = "https://iptvx.one/EPG.xml.gz" 
CHANNELS_FILE = "canali.txt"
OUTPUT_FILE = "04.epg"

def translate_text(translator, text):
    if not text or len(str(text)) < 3:
        return text
    try:
        # Delay per evitare il blocco da parte di Google Translate
        time.sleep(0.2)
        return translator.translate(text)
    except Exception:
        return text

def main():
    print("--- INIZIO PROCESSO EPG ---")
    translator = GoogleTranslator(source='auto', target='it')

    # 1. Lettura canali da filtrare
    if not os.path.exists(CHANNELS_FILE):
        print(f"ERRORE: {CHANNELS_FILE} non trovato!")
        return
    
    with open(CHANNELS_FILE, 'r', encoding='utf-8') as f:
        wanted_channels = [line.strip() for line in f if line.strip()]
    print(f"Canali richiesti: {len(wanted_channels)}")

    # 2. Download con User-Agent reale
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/110.0.0.0 Safari/537.36'}
    print(f"Scaricamento da: {EPG_URL}...")
    try:
        r = requests.get(EPG_URL, headers=headers, timeout=60)
        if r.status_code == 404:
            print("ERRORE 404: L'URL non è corretto. Provo con l'estensione .xml...")
            r = requests.get("https://iptvx.one/EPG.xml", headers=headers, timeout=60)
        
        r.raise_for_status()
        print("Download completato.")
    except Exception as e:
        print(f"ERRORE DOWNLOAD: {e}")
        return

    # 3. Decompressione e Parsing
    try:
        # Se i primi byte sono quelli di un GZIP, decomprimi
        if r.content.startswith(b'\x1f\x8b'):
            xml_content = gzip.decompress(r.content)
        else:
            xml_content = r.content
        
        parser = etree.XMLParser(recover=True, encoding='utf-8')
        tree = etree.fromstring(xml_content, parser=parser)
        print("XML analizzato correttamente.")
    except Exception as e:
        print(f"ERRORE PARSING: {e}")
        return

    # 4. Creazione nuovo file XML
    new_root = etree.Element("tv")
    new_root.set("generator-info-name", "Custom-IT-EPG")

    # Filtra Canali
    canali_trovati = 0
    for channel in tree.xpath("//channel"):
        # Controlliamo se l'ID o il nome del canale è nella nostra lista
        channel_id = channel.get("id")
        display_name = channel.findtext("display-name")
        
        if channel_id in wanted_channels or display_name in wanted_channels:
            new_root.append(channel)
            canali_trovati += 1
    
    print(f"Canali trovati nel file sorgente: {canali_trovati}")

    # Filtra e Traduce Programmi
    print("Traduzione programmi in corso (potrebbe richiedere tempo)...")
    prog_count = 0
    for prog in tree.xpath("//programme"):
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
            prog_count += 1
            
            # Debug ogni 20 programmi
            if prog_count % 20 == 0:
                print(f"Tradotti {prog_count} programmi...")
            
            # Limite massimo per evitare che GitHub blocchi lo script per troppa durata
            if prog_count >= 300:
                print("Raggiunto limite di 300 programmi per sicurezza.")
                break

    # 5. Salvataggio
    if prog_count > 0:
        with open(OUTPUT_FILE, "wb") as f:
            f.write(etree.tostring(new_root, encoding="utf-8", xml_declaration=True, pretty_print=True))
        print(f"SUCCESSO: Creato file {OUTPUT_FILE} con {prog_count} programmi.")
    else:
        print("ERRORE: Nessun programma trovato per i canali specificati. Verifica i nomi in canali.txt")

if __name__ == "__main__":
    main()
