#!/usr/bin/env python3
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import gzip
import shutil
import urllib.request
from urllib.error import HTTPError, URLError

EPG_URL = "https://iptvx.one/epg/epg.xml.gz"
EPG_LOCAL_GZ = "epg.xml.gz"
EPG_LOCAL = "epg.xml"
OUTPUT = "04.xml"

def download_epg():
    print(f"Scaricamento EPG da: {EPG_URL}")
    try:
        with urllib.request.urlopen(EPG_URL) as response:
            with open(EPG_LOCAL_GZ, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
        print(f"Download completato ({Path(EPG_LOCAL_GZ).stat().st_size:,} bytes)")
        
        # Decomprimi
        with gzip.open(EPG_LOCAL_GZ, 'rb') as f_in:
            with open(EPG_LOCAL, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        print(f"Decompresso in {EPG_LOCAL} ({Path(EPG_LOCAL).stat().st_size:,} bytes)")
        
    except (HTTPError, URLError) as e:
        print(f"ERRORE DOWNLOAD: {e}")
        sys.exit(1)
    except gzip.BadGzipFile:
        print("ERRORE: Il file scaricato non è un valido archivio gzip")
        sys.exit(1)

def main():
    # 1. Download se non esiste già (utile per debug locale)
    if not Path(EPG_LOCAL).is_file():
        download_epg()

    # 2. Carica mapping
    ori_path = Path("id.ori.txt")
    m3u_path = Path("id.m3u.txt")

    if not ori_path.is_file() or not m3u_path.is_file():
        print("ERRORE: id.ori.txt o id.m3u.txt non trovati")
        sys.exit(1)

    with ori_path.open(encoding="utf-8") as f:
        ori_ids = [line.strip() for line in f if line.strip()]

    with m3u_path.open(encoding="utf-8") as f:
        m3u_ids = [line.strip() for line in f if line.strip()]

    if len(ori_ids) != len(m3u_ids):
        print(f"ERRORE: id.ori.txt ({len(ori_ids)}) e id.m3u.txt ({len(m3u_ids)}) hanno lunghezze diverse")
        sys.exit(1)

    mapping = dict(zip(ori_ids, m3u_ids))
    channels_to_keep = set(ori_ids)

    print(f"Canali da mantenere e mappare: {list(mapping.items())}")

    # 3. Parsa EPG
    try:
        tree = ET.parse(EPG_LOCAL)
        root = tree.getroot()
        print(f"EPG parsato correttamente – {len(root.findall('channel'))} canali totali")
    except Exception as e:
        print(f"ERRORE PARSING XML: {e}")
        # Mostra prime righe per debug
        if Path(EPG_LOCAL).is_file():
            with open(EPG_LOCAL, encoding="utf-8", errors="replace") as f:
                head = f.read(800)
                print("Prime righe di epg.xml (per debug):\n", head)
        sys.exit(1)

    # 4. Filtra e rinomina canali
    kept_channels = 0
    new_channels = []
    for channel in root.findall("channel"):
        ch_id = channel.get("id")
        if ch_id in channels_to_keep:
            channel.set("id", mapping[ch_id])
            # Opzionale: aggiorna display-name se vuoi
            # for dn in channel.findall("display-name"):
            #     if dn.text == ch_id:
            #         dn.text = mapping[ch_id]
            new_channels.append(channel)
            kept_channels += 1

    # 5. Filtra programmi
    kept_programmes = 0
    new_programmes = []
    for programme in root.findall("programme"):
        ch_id = programme.get("channel")
        if ch_id in channels_to_keep:
            programme.set("channel", mapping[ch_id])
            new_programmes.append(programme)
            kept_programmes += 1

    print(f"Trovati e mantenuti: {kept_channels} canali / {kept_programmes} programmi")

    if kept_channels == 0:
        print("ATTENZIONE: Nessun canale corrispondente trovato nell'EPG → controlla id.ori.txt")

    # 6. Crea nuovo XMLTV
    new_root = ET.Element("tv")
    for k, v in root.attrib.items():
        new_root.set(k, v)

    for ch in new_channels:
        new_root.append(ch)
    for prog in new_programmes:
        new_root.append(prog)

    # 7. Salva con indentazione leggibile
    ET.indent(new_root, space="  ", level=0)
    new_tree = ET.ElementTree(new_root)
    new_tree.write(OUTPUT, encoding="utf-8", xml_declaration=True)

    print(f"File salvato: {OUTPUT} ({Path(OUTPUT).stat().st_size:,} bytes)")

if __name__ == "__main__":
    main()
