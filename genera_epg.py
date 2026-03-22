import requests
import xml.etree.ElementTree as ET
import gzip
import io
import json
import os
import time

# -----------------------------
# CONFIG
# -----------------------------
EPG_URL = "https://iptvx.one/epg/epg.xml.gz"
CANALI_URL = "https://raw.githubusercontent.com/ccliimpm77/04/refs/heads/main/canali.txt"

OUTPUT_FILE = "04.epg"
CACHE_FILE = "traduzioni.json"

MAX_TRADUZIONI = 500   # limite sicurezza (GitHub Actions)
DELAY = 0.3            # evita rate limit


# -----------------------------
# DOWNLOAD EPG
# -----------------------------
def scarica_epg():
    print(f"Scarico EPG: {EPG_URL}")
    r = requests.get(EPG_URL, timeout=60)
    r.raise_for_status()

    with gzip.open(io.BytesIO(r.content), 'rt', encoding='utf-8') as f:
        return f.read()


# -----------------------------
# DOWNLOAD CANALI
# -----------------------------
def scarica_file(url):
    print(f"Scarico: {url}")
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.text


def normalizza(s):
    return s.lower().strip() if s else ""


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

    # CANALI
    for channel in root.findall("channel"):
        cid = normalizza(channel.get("id", ""))

        display = channel.find("display-name")
        nome = normalizza(display.text) if display is not None else ""

        if cid in canali or nome in canali:
            nuovo_root.append(channel)
            canali_validi.add(cid)

    print(f"Canali trovati: {len(canali_validi)}")

    # PROGRAMMI
    count = 0
    for programme in root.findall("programme"):
        cid = normalizza(programme.get("channel", ""))

        if cid in canali_validi or cid in canali:
            nuovo_root.append(programme)
            count += 1

    print(f"Programmi filtrati: {count}")
    return nuovo_root


# -----------------------------
# CACHE TRADUZIONI
# -----------------------------
def carica_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def salva_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


# -----------------------------
# TRADUZIONE (LibreTranslate)
# -----------------------------
def traduci_testo(testo, cache):
    testo = testo.strip()

    if not testo:
        return testo

    # già tradotto
    if testo in cache:
        return cache[testo]

    try:
        response = requests.post(
            "https://libretranslate.de/translate",
            data={
                "q": testo,
                "source": "auto",
                "target": "it",
                "format": "text"
            },
            timeout=10
        )

        result = response.json()
        tradotto = result.get("translatedText", testo)

        cache[testo] = tradotto
        time.sleep(DELAY)

        return tradotto

    except Exception as e:
        print("Errore traduzione:", e)
        return testo


# -----------------------------
# TRADUZIONE EPG (SMART)
# -----------------------------
def traduci_epg(root):
    print("Traduzione intelligente attiva...")

    cache = carica_cache()
    tradotti = 0

    for programme in root.findall("programme"):
        if tradotti >= MAX_TRADUZIONI:
            print("Limite traduzioni raggiunto")
            break

        title = programme.find("title")
        desc = programme.find("desc")

        # traduci titolo
        if title is not None and title.text:
            nuovo = traduci_testo(title.text, cache)
            if nuovo != title.text:
                title.text = nuovo
                tradotti += 1

        # traduci descrizione (opzionale ma pesante)
        if desc is not None and desc.text and tradotti < MAX_TRADUZIONI:
            nuovo = traduci_testo(desc.text, cache)
            if nuovo != desc.text:
                desc.text = nuovo
                tradotti += 1

        if tradotti % 50 == 0 and tradotti > 0:
            print(f"Tradotti: {tradotti}")

    salva_cache(cache)
    print(f"Traduzione completata: {tradotti}")


# -----------------------------
# SALVA FILE
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

        epg_filtrato = filtra_epg(epg_xml, canali)

        traduci_epg(epg_filtrato)

        salva_epg(epg_filtrato)

        print("✅ COMPLETATO")

    except Exception as e:
        print("❌ ERRORE:", str(e))
        raise


if __name__ == "__main__":
    main()
