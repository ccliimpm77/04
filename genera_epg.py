import requests
import xml.etree.ElementTree as ET
import gzip
import io

# URL sorgenti
EPG_URL = "https://iptvx.one/epg/epg.xml.gz"
CANALI_URL = "https://raw.githubusercontent.com/ccliimpm77/04/refs/heads/main/canali.txt"

OUTPUT_FILE = "04.epg"


# -----------------------------
# DOWNLOAD EPG (gzip)
# -----------------------------
def scarica_epg():
    print(f"Scarico EPG: {EPG_URL}")

    r = requests.get(EPG_URL, timeout=60)
    r.raise_for_status()

    with gzip.open(io.BytesIO(r.content), 'rt', encoding='utf-8') as f:
        return f.read()


# -----------------------------
# DOWNLOAD LISTA CANALI
# -----------------------------
def scarica_file(url):
    print(f"Scarico: {url}")
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.text


def normalizza(s):
    return s.lower().strip()


def carica_canali():
    testo = scarica_file(CANALI_URL)

    canali = set()
    for riga in testo.splitlines():
        riga = normalizza(riga)
        if riga:
            canali.add(riga)

    print(f"Canali caricati: {len(canali)}")
    return canali


# -----------------------------
# FILTRO EPG
# -----------------------------
def filtra_epg(xml_data, canali):
    print("Parsing XML...")
    root = ET.fromstring(xml_data)

    nuovo_root = ET.Element("tv")

    canali_validi = set()

    # --- FILTRA CANALI ---
    for channel in root.findall("channel"):
        cid = normalizza(channel.get("id", ""))

        display = channel.find("display-name")
        nome = normalizza(display.text) if display is not None else ""

        if cid in canali or nome in canali:
            nuovo_root.append(channel)
            canali_validi.add(cid)

    print(f"Canali trovati: {len(canali_validi)}")

    # --- FILTRA PROGRAMMI ---
    count_prog = 0

    for programme in root.findall("programme"):
        cid = normalizza(programme.get("channel", ""))

        if cid in canali_validi or cid in canali:
            nuovo_root.append(programme)
            count_prog += 1

    print(f"Programmi filtrati: {count_prog}")

    return nuovo_root


# -----------------------------
# SALVATAGGIO FILE
# -----------------------------
def salva_epg(root):
    print("Salvataggio file...")

    tree = ET.ElementTree(root)
    tree.write(OUTPUT_FILE, encoding="utf-8", xml_declaration=True)

    print(f"File salvato: {OUTPUT_FILE}")


# -----------------------------
# MAIN
# -----------------------------
def main():
    try:
        epg_xml = scarica_epg()
        canali = carica_canali()

        nuovo_epg = filtra_epg(epg_xml, canali)
        salva_epg(nuovo_epg)

        print("✅ Completato con successo")

    except Exception as e:
        print("❌ Errore:", str(e))
        raise


if __name__ == "__main__":
    main()
