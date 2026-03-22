import urllib.request
import gzip
import xml.etree.ElementTree as ET
from deep_translator import GoogleTranslator
import os
import sys

# CONFIGURAZIONE
SOURCE_URL = "https://iptvx.one/EPG"
CHANNELS_LIST_FILE = "canali.txt"
OUTPUT_FILE = "04.epg"

def load_target_channels():
    """Carica la lista dei canali da filtrare dal file canali.txt"""
    if not os.path.exists(CHANNELS_LIST_FILE):
        print(f"!!! ERRORE: File {CHANNELS_LIST_FILE} non trovato.")
        return set()
    with open(CHANNELS_LIST_FILE, 'r', encoding='utf-8') as f:
        # Crea un set di ID canali puliti da spazi e righe vuote
        return set(line.strip() for line in f if line.strip())

def main():
    target_channels = load_target_channels()
    if not target_channels:
        print("Nessun canale trovato in canali.txt. Esco.")
        return

    print(f"Canali da filtrare: {len(target_channels)}")
    
    # Inizializza il traduttore e la cache per la velocità
    translator = GoogleTranslator(source='auto', target='it')
    translation_cache = {}

    def translate_it(text):
        """Traduce il testo in italiano usando una cache per non ripetere traduzioni uguali"""
        if not text or text.isdigit(): return text
        if text in translation_cache:
            return translation_cache[text]
        try:
            translated = translator.translate(text)
            translation_cache[text] = translated
            return translated
        except:
            return text

    try:
        # Apertura connessione
        req = urllib.request.Request(SOURCE_URL, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, timeout=120)
        
        # Decompressione al volo
        with gzip.GzipFile(fileobj=response) as gzipped:
            # Parsing iterativo per risparmiare RAM
            context = ET.iterparse(gzipped, events=('start', 'end'))
            
            with open(OUTPUT_FILE, 'wb') as f_out:
                f_out.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
                f_out.write(b'<tv generator-info-name="Filtered-Translated-EPG">\n')

                current_channel_id = None
                
                for event, elem in context:
                    tag = elem.tag.split('}')[-1] # Gestione namespace

                    if event == 'end':
                        if tag == 'channel':
                            channel_id = elem.get('id')
                            if channel_id in target_channels:
                                f_out.write(ET.tostring(elem, encoding='utf-8'))
                                f_out.write(b'\n')
                            elem.clear()

                        elif tag == 'programme':
                            channel_id = elem.get('channel')
                            if channel_id in target_channels:
                                # TRADUZIONE TITOLO E DESCRIZIONE
                                title_node = elem.find('title')
                                if title_node is not None:
                                    title_node.text = translate_it(title_node.text)
                                
                                desc_node = elem.find('desc')
                                if desc_node is not None:
                                    desc_node.text = translate_it(desc_node.text)

                                f_out.write(ET.tostring(elem, encoding='utf-8'))
                                f_out.write(b'\n')
                            elem.clear()

                f_out.write(b'</tv>')
        
        print(f"Fatto! File {OUTPUT_FILE} creato e tradotto.")

    except Exception as e:
        print(f"Errore durante il processo: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
