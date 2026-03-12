import os
import requests
import gzip
from lxml import etree
from deep_translator import GoogleTranslator
from concurrent.futures import ThreadPoolExecutor
import time

# --- CONFIGURAZIONE ---
EPG_URL = "https://iptvx.one/EPG.xml.gz"
CHANNELS_FILE = "canali.txt"
OUTPUT_FILE = "04.epg"
MAX_WORKERS = 10  # Numero di traduzioni simultanee
BATCH_SIZE = 30   # Quanti testi inviare in una singola richiesta

def translate_batch(texts):
    """Traduce una lista di testi in un colpo solo"""
    if not texts:
        return {}
    try:
        translator = GoogleTranslator(source='auto', target='it')
        # La libreria supporta la traduzione di liste
        translated_list = translator.translate_batch(texts)
        return dict(zip(texts, translated_list))
    except Exception as e:
        print(f"Errore nel blocco di traduzione: {e}")
        return {text: text for text in texts}

def main():
    start_time = time.time()
    print("--- INIZIO PROCESSO VELOCE ---")

    # 1. Caricamento Canali
    if not os.path.exists(CHANNELS_FILE):
        print("Errore: canali.txt mancante")
        return
    with open(CHANNELS_FILE, 'r', encoding='utf-8') as f:
        wanted_list = {line.strip() for line in f if line.strip()}

    # 2. Download e Parsing
    try:
        r = requests.get(EPG_URL, headers={'User-Agent': 'Mozilla/5.0'}, timeout=60)
        xml_content = gzip.decompress(r.content) if r.content.startswith(b'\x1f\x8b') else r.content
        tree = etree.fromstring(xml_content)
    except Exception as e:
        print(f"Errore download: {e}")
        return

    # 3. Filtraggio Canali e Programmi
    real_ids = {c.get("id") for c in tree.xpath("//channel") if c.get("id") in wanted_list or c.findtext("display-name") in wanted_list}
    relevant_programmes = [p for p in tree.xpath("//programme") if p.get("channel") in real_ids]
    
    # 4. Raccolta testi UNICI da tradurre (Deduplicazione)
    unique_texts = set()
    for p in relevant_programmes:
        t = p.findtext("title")
        d = p.findtext("desc")
        if t and len(t) > 2: unique_texts.add(t)
        if d and len(d) > 2: unique_texts.add(d)

    print(f"Testi unici da tradurre: {len(unique_texts)} (su {len(relevant_programmes)} programmi)")

    # 5. Traduzione in parallelo e a blocchi
    text_list = list(unique_texts)
    batches = [text_list[i:i + BATCH_SIZE] for i in range(0, len(text_list), BATCH_SIZE)]
    
    translation_map = {}
    print(f"Avvio traduzione con {MAX_WORKERS} thread in parallelo...")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(executor.map(translate_batch, batches))
        for res in results:
            translation_map.update(res)

    # 6. Applicazione traduzioni all'XML
    new_root = etree.Element("tv", tree.attrib)
    
    # Aggiungi i canali
    for c in tree.xpath("//channel"):
        if c.get("id") in real_ids:
            new_root.append(c)

    # Aggiungi i programmi tradotti
    for p in relevant_programmes:
        t_node = p.find("title")
        if t_node is not None and t_node.text in translation_map:
            t_node.text = translation_map[t_node.text]
        
        d_node = p.find("desc")
        if d_node is not None and d_node.text in translation_map:
            d_node.text = translation_map[d_node.text]
            
        new_root.append(p)

    # 7. Salvataggio
    with open(OUTPUT_FILE, "wb") as f:
        f.write(etree.tostring(new_root, encoding="utf-8", xml_declaration=True, pretty_print=True))

    end_time = time.time()
    print(f"--- FINE ---")
    print(f"Tempo impiegato: {int(end_time - start_time)} secondi")
    print(f"File generato: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
