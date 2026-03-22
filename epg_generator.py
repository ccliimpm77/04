#!/usr/bin/env python3
"""
EPG Generator - Scarica, filtra e traduce la guida TV in italiano.
Legge canali.txt dal repo, scarica l'EPG da iptvx.one, traduce con Claude API.
"""

import os
import gzip
import xml.etree.ElementTree as ET
from xml.dom import minidom
import anthropic
import time
import sys

# ── Configurazione ────────────────────────────────────────────────────────────
EPG_URL       = "https://iptvx.one/EPG"
CANALI_FILE   = "canali.txt"
OUTPUT_FILE   = "04.epg"
CLAUDE_MODEL  = "claude-sonnet-4-20250514"
BATCH_SIZE    = 15        # titoli per chiamata API (bilancia velocità/costo)
MAX_RETRIES   = 3
RETRY_DELAY   = 5         # secondi tra i retry

# ── Utilità ───────────────────────────────────────────────────────────────────

def load_canali(path: str) -> list[str]:
    """Legge canali.txt e restituisce lista di nomi (una riga = un canale)."""
    with open(path, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def download_epg(url: str) -> bytes:
    """
    Scarica l'EPG usando curl (bypassa Cloudflare meglio di urllib/requests).
    Supporta gzip automaticamente tramite --compressed.
    """
    import subprocess
    import tempfile

    print(f"[*] Scarico EPG da {url} ...")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp:
        tmp_path = tmp.name

    cmd = [
        "curl",
        "--silent",
        "--fail",
        "--location",           # segui redirect
        "--compressed",         # decomprime gzip automaticamente
        "--max-time", "180",
        "--retry", "3",
        "--retry-delay", "5",
        "--user-agent", (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "--header", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "--header", "Accept-Language: it-IT,it;q=0.9,en;q=0.8",
        "--header", "Accept-Encoding: gzip, deflate, br",
        "--header", "Connection: keep-alive",
        "-o", tmp_path,
        url,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"curl fallito (exit {result.returncode}): {result.stderr.strip()}"
        )

    with open(tmp_path, "rb") as f:
        data = f.read()

    os.unlink(tmp_path)

    # Sicurezza: decomprime se ancora gzip (curl --compressed a volte non basta)
    if data[:2] == b'\x1f\x8b':
        data = gzip.decompress(data)

    if not data:
        raise RuntimeError("File EPG scaricato è vuoto.")

    print(f"[*] EPG scaricato ({len(data)//1024} KB)")
    return data


def parse_epg(data: bytes):
    """Parsa l'XML XMLTV e restituisce (channels_dict, programmes_list)."""
    print("[*] Parsing XML EPG ...")
    root = ET.fromstring(data)

    channels = {}   # id -> display-name
    for ch in root.findall("channel"):
        cid   = ch.get("id", "")
        names = [n.text for n in ch.findall("display-name") if n.text]
        if cid and names:
            channels[cid] = names  # lista di nomi alternativi

    programmes = root.findall("programme")
    print(f"[*] Trovati {len(channels)} canali, {len(programmes)} programmi")
    return channels, programmes


def match_channels(canali: list[str], channels: dict) -> set[str]:
    """
    Restituisce l'insieme degli ID canale che corrispondono ai nomi in canali.txt.
    Matching case-insensitive e parziale.
    """
    matched_ids = set()
    canali_lower = [c.lower() for c in canali]

    for cid, names in channels.items():
        for name in names:
            nl = name.lower()
            for cl in canali_lower:
                # Match esatto o sottostringa in entrambe le direzioni
                if cl == nl or cl in nl or nl in cl:
                    matched_ids.add(cid)
                    break

    print(f"[*] Canali abbinati: {len(matched_ids)} / {len(canali)}")
    return matched_ids


# ── Traduzione con Claude ─────────────────────────────────────────────────────

def translate_batch(client: anthropic.Anthropic, texts: list[str]) -> list[str]:
    """
    Invia un batch di testi a Claude e restituisce le traduzioni in italiano.
    Ogni testo è separato da '|||' nella richiesta per minimizzare le chiamate API.
    """
    if not texts:
        return []

    joined = "\n|||".join(texts)
    prompt = (
        "Traduci in italiano i seguenti testi della guida TV. "
        "Restituisci SOLO le traduzioni, una per riga, separate da '|||', "
        "nello stesso ordine. Non aggiungere spiegazioni, numerazione o altro testo.\n\n"
        f"{joined}"
    )

    for attempt in range(MAX_RETRIES):
        try:
            msg = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )
            result = msg.content[0].text.strip()
            parts = [p.strip() for p in result.split("|||")]
            # Se il numero di parti non corrisponde, restituiamo gli originali
            if len(parts) != len(texts):
                print(f"  [!] Batch disallineato ({len(parts)} vs {len(texts)}), uso originali")
                return texts
            return parts
        except Exception as e:
            print(f"  [!] Errore API (tentativo {attempt+1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
    return texts  # fallback: testo originale


def translate_programmes(client: anthropic.Anthropic, programmes: list) -> dict:
    """
    Raccoglie tutti i titoli/descrizioni unici, li traduce in batch,
    restituisce dizionario {testo_originale: testo_tradotto}.
    """
    # Raccogli testi unici da tradurre
    to_translate = set()
    for prog in programmes:
        title = prog.find("title")
        desc  = prog.find("desc")
        if title is not None and title.text:
            to_translate.add(title.text.strip())
        if desc is not None and desc.text:
            to_translate.add(desc.text.strip())

    unique_texts = list(to_translate)
    print(f"[*] Testi unici da tradurre: {len(unique_texts)}")

    translations = {}
    total_batches = (len(unique_texts) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(unique_texts), BATCH_SIZE):
        batch     = unique_texts[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f"  [*] Batch {batch_num}/{total_batches} ({len(batch)} testi) ...")
        translated = translate_batch(client, batch)
        for orig, tr in zip(batch, translated):
            translations[orig] = tr
        # Pausa cortesia tra batch per evitare rate-limit
        if i + BATCH_SIZE < len(unique_texts):
            time.sleep(1)

    return translations


# ── Costruzione XML output ────────────────────────────────────────────────────

def build_output_xml(channels: dict, matched_ids: set, programmes: list,
                     translations: dict, canali_names: list[str]) -> str:
    """Costruisce il file XMLTV finale con soli i canali/programmi selezionati."""

    root = ET.Element("tv", attrib={
        "generator-info-name": "epg-generator",
        "generator-info-url":  "https://github.com/ccliimpm77/04"
    })

    # Sezione <channel>
    for cid in sorted(matched_ids):
        ch_el = ET.SubElement(root, "channel", id=cid)
        for name in channels.get(cid, [cid]):
            dn = ET.SubElement(ch_el, "display-name")
            dn.text = name

    # Sezione <programme>
    count = 0
    for prog in programmes:
        if prog.get("channel") not in matched_ids:
            continue

        new_prog = ET.SubElement(root, "programme", attrib={
            "start":   prog.get("start", ""),
            "stop":    prog.get("stop",  ""),
            "channel": prog.get("channel", "")
        })

        # Titolo tradotto
        title_el = prog.find("title")
        new_title = ET.SubElement(new_prog, "title", lang="it")
        if title_el is not None and title_el.text:
            new_title.text = translations.get(title_el.text.strip(), title_el.text)
        else:
            new_title.text = ""

        # Descrizione tradotta
        desc_el = prog.find("desc")
        if desc_el is not None and desc_el.text:
            new_desc = ET.SubElement(new_prog, "desc", lang="it")
            new_desc.text = translations.get(desc_el.text.strip(), desc_el.text)

        # Categoria (se presente)
        for cat in prog.findall("category"):
            new_cat = ET.SubElement(new_prog, "category", lang="it")
            new_cat.text = translations.get(cat.text or "", cat.text or "")

        # Episodio (se presente)
        for ep in prog.findall("episode-num"):
            new_ep = ET.SubElement(new_prog, "episode-num", system=ep.get("system", ""))
            new_ep.text = ep.text

        count += 1

    print(f"[*] Programmi inclusi nel file di output: {count}")

    # Pretty-print XML
    raw = ET.tostring(root, encoding="unicode")
    dom = minidom.parseString(raw)
    return dom.toprettyxml(indent="  ", encoding=None)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Chiave API da variabile d'ambiente (impostata nei Secrets di GitHub Actions)
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[!] ERRORE: variabile d'ambiente ANTHROPIC_API_KEY non impostata.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # 1. Leggi canali.txt
    if not os.path.exists(CANALI_FILE):
        print(f"[!] File '{CANALI_FILE}' non trovato.")
        sys.exit(1)
    canali = load_canali(CANALI_FILE)
    print(f"[*] Canali richiesti ({len(canali)}): {', '.join(canali[:10])}{'...' if len(canali)>10 else ''}")

    # 2. Scarica e parsa EPG
    raw = download_epg(EPG_URL)
    channels, programmes = parse_epg(raw)

    # 3. Abbina i canali
    matched_ids = match_channels(canali, channels)
    if not matched_ids:
        print("[!] Nessun canale abbinato. Controlla canali.txt e i nomi nell'EPG.")
        sys.exit(1)

    # 4. Filtra i programmi dei canali abbinati
    filtered = [p for p in programmes if p.get("channel") in matched_ids]
    print(f"[*] Programmi filtrati: {len(filtered)}")

    # 5. Traduci
    print("[*] Avvio traduzione con Claude ...")
    translations = translate_programmes(client, filtered)

    # 6. Costruisci XML output
    xml_output = build_output_xml(channels, matched_ids, programmes, translations, canali)

    # 7. Scrivi file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(xml_output)
    print(f"[✓] File '{OUTPUT_FILE}' creato con successo.")


if __name__ == "__main__":
    main()
