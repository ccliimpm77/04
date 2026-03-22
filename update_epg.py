import requests
import gzip
import xml.etree.ElementTree as ET
from io import BytesIO

# Configurazione URL
EPG_URL = "https://iptvx.one/epg/epg.xml.gz"
ORI_URL = "https://raw.githubusercontent.com/ccliimpm77/04/refs/heads/main/id.ori.txt"
M3U_URL = "https://raw.githubusercontent.com/ccliimpm77/04/refs/heads/main/id.m3u.txt"

def get_mapping():
    ori_ids = requests.get(ORI_URL).text.strip().splitlines()
    m3u_ids = requests.get(M3U_URL).text.strip().splitlines()
    # Crea un dizionario { 'ID_ORIGINALE': 'ID_NUOVO' }
    return dict(zip(ori_ids, m3u_ids))

def process_epg():
    mapping = get_mapping()
    allowed_ori_ids = set(mapping.keys())

    # Scarica e decomprime l'EPG
    print("Scaricamento EPG...")
    response = requests.get(EPG_URL)
    with gzip.open(BytesIO(response.content), 'rb') as f:
        tree = ET.parse(f)
    
    root = tree.getroot()
    new_root = ET.Element("tv", root.attrib)

    # Filtra e Rinomina i Canali
    for channel in root.findall('channel'):
        chan_id = channel.get('id')
        if chan_id in allowed_ori_ids:
            channel.set('id', mapping[chan_id])
            new_root.append(channel)

    # Filtra e Rinomina i Programmi
    for programme in root.findall('programme'):
        chan_id = programme.get('channel')
        if chan_id in allowed_ori_ids:
            programme.set('channel', mapping[chan_id])
            new_root.append(programme)

    # Salva il file
    new_tree = ET.ElementTree(new_root)
    ET.indent(new_tree, space="  ", level=0)
    new_tree.write("04.xml", encoding="utf-8", xml_declaration=True)
    print("File 04.xml creato con successo.")

if __name__ == "__main__":
    process_epg()
