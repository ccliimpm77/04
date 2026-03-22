import requests
import xml.etree.ElementTree as ET

# URL
EPG_URL = "https://iptvx.one/EPG"
CANALI_URL = "https://raw.githubusercontent.com/ccliimpm77/04/refs/heads/main/canali.txt"

OUTPUT_FILE = "04.epg"


def scarica_file(url):
    print(f"Scarico: {url}")
    r = requests.get(url)
    r.raise_for_status()
    return r.text


def carica_canali():
    testo = scarica_file(CANALI_URL)
    canali = set()

    for riga in testo.splitlines():
        riga = riga.strip()
        if riga:
            canali.add(riga.lower())

    print(f"Canali caricati: {len(canali)}")
    return canali


def filtra_epg(xml_data, canali):
    root = ET.fromstring(xml_data)

    nuovo_root = ET.Element("tv")

    # copia canali
    for channel in root.findall("channel"):
        display_name = channel.find("display-name")
        if display_name is not None:
            nome = display_name.text.lower()
            if nome in canali:
                nuovo_root.append(channel)

    # copia programmi
    for programme in root.findall("programme"):
        channel_id = programme.get("channel", "").lower()

        if channel_id in canali:
            nuovo_root.append(programme)

    return nuovo_root


def salva_epg(root):
    tree = ET.ElementTree(root)
    tree.write(OUTPUT_FILE, encoding="utf-8", xml_declaration=True)
    print(f"File salvato: {OUTPUT_FILE}")


def main():
    epg_xml = scarica_file(EPG_URL)
    canali = carica_canali()

    nuovo_epg = filtra_epg(epg_xml, canali)
    salva_epg(nuovo_epg)


if __name__ == "__main__":
    main()
