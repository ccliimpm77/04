import requests
import gzip
import xml.etree.ElementTree as ET

# Definizione URL e nomi file
url = "https://raw.githubusercontent.com/ccliimpm77/04/main/04.xml.gz"
gz_file = "04.xml.gz"
xml_file = "04.xml"
output_file = "04.epg"

# 1. Scarica il file .gz
response = requests.get(url)
with open(gz_file, "wb") as f:
    f.write(response.content)

# 2. Decompressione del file .gz in un file .xml
with gzip.open(gz_file, "rb") as f_in:
    with open(xml_file, "wb") as f_out:
        f_out.write(f_in.read())

# 3. Lettura dell'XML e scrittura del file finale .epg
tree = ET.parse(xml_file)
root = tree.getroot()

# Scrittura finale
tree.write(output_file, encoding="utf-8", xml_declaration=True)

print("Operazione completata con il metodo originale.")
