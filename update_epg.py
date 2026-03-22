import requests
import gzip
import xml.etree.ElementTree as ET

# Configurazione
url = "https://iptvx.one/EPG"
gz_file = "04.xml.gz"
xml_file = "04.xml"
output_file = "04.epg"

# 1. Scarica il file compresso
print("Scaricamento in corso...")
response = requests.get(url)
with open(gz_file, "wb") as f:
    f.write(response.content)

# 2. Decompressione del file .gz
print("Decompressione...")
with gzip.open(gz_file, "rb") as f_in:
    with open(xml_file, "wb") as f_out:
        f_out.write(f_in.read())

# 3. Parsing dell'XML e creazione del file finale .epg
print("Creazione file 04.epg...")
tree = ET.parse(xml_file)
root = tree.getroot()

# Scrittura del file finale
tree.write(output_file, encoding="utf-8", xml_declaration=True)

print("Operazione completata con successo.")
