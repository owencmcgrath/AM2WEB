import xml.etree.ElementTree as ET
from datetime import datetime
import re

def parse_itunes_library(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    tracks_dict = root.find('./dict/dict')
    
    songs = []
    current_song = {}
    
    for elem in tracks_dict:
        if elem.tag == 'key':
            track_id = elem.text
        elif elem.tag == 'dict':
            for i in range(0, len(elem)):
                if elem[i].tag == 'key':
                    key = elem[i].text
                    value = elem[i+1]
                    
                    if value.tag == 'integer':
                        current_song[key] = int(value.text)
                    elif value.tag == 'string':
                        current_song[key] = value.text
                    elif value.tag == 'date':
                        current_song[key] = datetime.strptime(value.text, '%Y-%m-%dT%H:%M:%SZ')
                    elif value.tag == 'true':
                        current_song[key] = True
                    elif value.tag == 'false':
                        current_song[key] = False
            
            songs.append(current_song)
            current_song = {}
    
    return songs

songs = parse_itunes_library('/Users/owenmcgrath/Downloads/library.xml')

for song in songs:
  print(f"Track: {song.get('Name')} by {song.get('Artist')}")