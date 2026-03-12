import os
import requests
import gzip
from lxml import etree
from deep_translator import GoogleTranslator
import time
import sys

# --- CONFIGURAZIONE ---
EPG_URL = "https://iptvx.one/epg.xml.gz" # Prova questo che è il link diretto comune
CHANNELS_FILE = "canali.txt"
OUTPUT_FILE = "04.epg"

def main():
    print("--- INIZIO DIAGNOSTICA ---")
    
    # 1. Controllo file canali
    if not os.path.exists(CHANNELS_FILE):
        print(f"! ERRORE: Il file {CHANNELS_FILE} non esiste nel repo.")
        with open(CHANNELS_FILE, "w") as f: f.write("Rai1.it")
        print("  Creato file canali.txt di prova con 'Rai1.it'")

    with open(CHANNELS_FILE, 'r') as f:
        wanted_channels = [line.strip() for line in f if line.strip()]
    print(f"Canali da filtrare: {wanted_channels}")

    # 2. Tentativo di Download
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
    }
    
    print(f"Scarico da: {EPG_URL}")
    try:
        r = requests.get(EPG_URL, headers=headers, timeout=30)
        print(f"Stato HTTP: {r.status_code}")
        print(f"Tipo Contenuto (Header): {r.headers.get('Content-Type')}")
        
        if r.status_code != 200:
            print(f"! ERRORE: Il sito ha risposto con errore {r.status_code}")
            return

        data = r.content
        print(f"Byte scaricati: {len(data)}")

        # Verifichiamo se è HTML (sbagliato) o XML/GZIP (giusto)
        if data.strip().startswith(b"<!DOCTYPE html") or data.strip().startswith(b"<html"):
            print("! ERRORE CRITICO: L'URL fornito è una PAGINA WEB, non un file EPG XML.")
            print("  Devi trovare il link diretto che finisce in .xml o .xml.gz")
            return

    except Exception as e:
        print(f"! ERRORE DURANTE IL DOWNLOAD: {e}")
        return

    # 3. Parsing XML
    try:
        if data.startswith(b'\x1f\x8b'): # Se è GZIP
            data = gzip.decompress(data)
        
        parser = etree.XMLParser(recover=True, encoding='utf-8')
        tree = etree.fromstring(data, parser=parser)
        print("XML caricato correttamente in memoria.")
    except Exception as e:
        print(f"! ERRORE PARSING XML: {e}")
        return

    # 4. Creazione nuovo file
    new_root = etree.Element("tv")
    
    # Copia canali
    c_count = 0
    for channel in tree.xpath("//channel"):
        if channel.get("id") in wanted_channels:
            new_root.append(channel)
            c_count += 1
    
    # Copia programmi (senza traduzione per ora, per testare se funziona)
    p_count = 0
    for prog in tree.xpath("//programme"):
        if prog.get("id") in wanted_channels:
            new_root.append(prog)
            p_count += 1
            if p_count > 1000: break # Limite di sicurezza

    print(f"Canali trovati: {c_count}, Programmi trovati: {p_count}")

    if c_count == 0:
        print("! AVVISO: Nessun canale trovato. Controlla che gli ID in canali.txt siano uguali a quelli dell'XML.")

    # 5. Scrittura file finale
    try:
        with open(OUTPUT_FILE, "wb") as f:
            f.write(etree.tostring(new_root, encoding="utf-8", xml_declaration=True, pretty_print=True))
        print(f"--- FILE {OUTPUT_FILE} GENERATO CON SUCCESSO ---")
    except Exception as e:
        print(f"! ERRORE SCRITTURA: {e}")

if __name__ == "__main__":
    main()
