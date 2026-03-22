import xml.etree.ElementTree as ET

# Carica mapping
with open('id.ori.txt', encoding='utf-8') as f:
    ori_ids = [line.strip() for line in f if line.strip()]

with open('id.m3u.txt', encoding='utf-8') as f:
    m3u_ids = [line.strip() for line in f if line.strip()]

if len(ori_ids) != len(m3u_ids):
    raise ValueError("id.ori.txt e id.m3u.txt devono avere lo stesso numero di righe!")

mapping = dict(zip(ori_ids, m3u_ids))
channels_to_keep = set(ori_ids)

# Parse EPG
tree = ET.parse('epg.xml')
root = tree.getroot()

# Filtra e rinomina <channel>
new_channels = []
for channel in root.findall('channel'):
    ch_id = channel.get('id')
    if ch_id in channels_to_keep:
        channel.set('id', mapping[ch_id])
        new_channels.append(channel)

# Filtra e rinomina <programme>
new_programmes = []
for programme in root.findall('programme'):
    ch_id = programme.get('channel')
    if ch_id in channels_to_keep:
        programme.set('channel', mapping[ch_id])
        new_programmes.append(programme)

# Ricostruisci XMLTV pulito
new_root = ET.Element('tv')
for attr, value in root.attrib.items():
    new_root.set(attr, value)

for ch in new_channels:
    new_root.append(ch)
for prog in new_programmes:
    new_root.append(prog)

# Salva
new_tree = ET.ElementTree(new_root)
new_tree.write('04.xml', encoding='utf-8', xml_declaration=True)

print(f"✅ 04.xml creato con {len(new_channels)} canali e {len(new_programmes)} programmi")
