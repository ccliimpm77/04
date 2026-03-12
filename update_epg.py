import os
import requests
import gzip
from lxml import etree
from deep_translator import GoogleTranslator
import time

# --- CONFIGURAZIONE ---
# Se l'URL finisce per /EPG, spesso reindirizza a un .xml.gz
EPG_URL = "https://iptvx.one/epg.xml.gz" 
CHANNELS_FILE = "canali.txt"
OUTPUT_FILE = "04.epg"

def translate_text(translator, text):
    if not text or len(str(text)) < 2:
        return text
    try:
        # Piccolo delay per evitare ban da Google
        time.sleep(0.2)
        return translator.translate(text)
    except Exception as e:
        print(f"DEBUG: Salto traduzione per: {text} (Errore: {e})")
        return text

def main():
    translator = GoogleTranslator(source='auto', target='it')

    # 1. Verifica o crea file canali.txt
    if not os.path.exists(CHANNELS_FILE):
        print(f"ATTENZIONE: {CHANNELS_FILE} non trovato. Creo un file di esempio...")
        with open(CHANNELS_FILE, 'w') as f:
            f.write("Rai1.it\nCanale5.it") # Esempio
        print("Creato canali.txt con canali di esempio. Modificalo con i tuoi ID.")

    with open(CHANNELS_FILE, 'r') as f:
        wanted_channels = [line.strip() for line in f if line.strip()]
    
    if not wanted_channels:
        print("ERRORE: La lista canali in canali.txt è vuota!")
        return

    # 2. Download EPG
    print(f"Scaricamento EPG da: {EPG_URL}")
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(EPG_URL, headers=headers, timeout=60)
        response.raise_for_status()
    except Exception as e:
        print(f"ERRORE CRITICO Download: {e}")
        return

    # 3. Decompressione
    print("Analisi contenuto...")
    try:
        # Prova a decomprimere se è GZIP, altrimenti usa i dati grezzi
        if EPG_URL.endswith(".gz") or response.content[:2] == b'\x1f\x8b':
            content = gzip.decompress(response.content)
        else:
            content = response.content
        
        parser = etree.XMLParser(recover=True, encoding='utf-8')
        tree = etree.fromstring(content, parser=parser)
    except Exception as e:
        print(f"ERRORE CRITICO Parsing XML: {e}")
        print("Il link fornito potrebbe non essere un file XMLTV valido.")
        return

    # 4. Creazione nuovo XML
    new_root = etree.Element("tv")
    for key, value in tree.attrib.items():
        new_root.set(key, value)

    # 5. Filtraggio Canali
    found_channels = []
    for channel in tree.xpath("//channel"):
        channel_id = channel.get("id")
        if channel_id in wanted_channels:
            new_root.append(channel)
            found_channels.append(channel_id)
    
    print(f"Trovati {len(found_channels)} canali su {len(wanted_channels)} richiesti.")

    # 6. Filtraggio e Traduzione Programmi
    print("Inizio filtraggio e traduzione (operazione lenta)...")
    prog_count = 0
    for prog in tree.xpath("//programme"):
        channel_id = prog.get("id")
        if channel_id in wanted_channels:
            # Traduzione Titolo
            t_node = prog.find("title")
            if t_node is not None and t_node.text:
                t_node.text = translate_text(translator, t_node.text)
            
            # Traduzione Descrizione
            d_node = prog.find("desc")
            if d_node is not None and d_node.text:
                d_node.text = translate_text(translator, d_node.text)
                
            new_root.append(prog)
            prog_count += 1
            if prog_count % 10 == 0:
                print(f"Processati {prog_count} programmi...")
            
            # Limite per non far durare l'action ore (opzionale)
            if prog_count > 500: 
                print("Raggiunto limite 500 programmi per questa sessione.")
                break

    # 7. Salvataggio finale
    print(f"Salvataggio in {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "wb") as f:
        f.write(etree.tostring(new_root, encoding="utf-8", xml_declaration=True, pretty_print=True))
    
    print("FINITO! File generato con successo.")

if __name__ == "__main__":
    main()
