import json
import os
from typing import Dict
from data_structures import KERN_NOTE_NAME


def load_dataset(filepath: str):   # -> Dict[str, Dict]
     
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File non trovato: '{filepath}'")

    with open(filepath, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    
    if isinstance(dataset, dict):
        songs = {k: v for k, v in dataset.items() if isinstance(v, dict) and 'annotations' in v}
        if songs:
            return songs
        if dataset:
            return dataset   

    raise ValueError("Formato JSON non riconosciuto.\n")


def extract_metadata(song_id: str, song: Dict):  # Dict[str, Any]
    hk   = song.get('hooktheory', {})
    yt   = song.get('youtube', {})
    ann  = song.get('annotations', {})
    urls = hk.get('urls', {})
    song_name   = song.get('hooktheory', {}).get('song', 'Unknown')

    return hk, yt, ann, urls, song_name


def display_song_list(songs: Dict[str, Dict]):

    # .items() restituisce coppie (chiave, valore) in ordine di inserimento
    for i, (sid, song) in enumerate(songs.items()):
        hk  = song.get('hooktheory', {})

        def slug_to_name(s):
            return ' '.join(w.capitalize() for w in s.split('-'))

        artist = slug_to_name(hk.get('artist', 'Unknown'))
        title  = slug_to_name(hk.get('song',   'Unknown'))

        print(f"  [{i:4d}]  {artist:<28}  {title:<32}  ")

       
def sanitize_filename(name: str) -> str:
    
    # problematic chars in OS
    for ch in r'\/:*?"<>|':
        name = name.replace(ch, '_')

    name = name.strip()           # rimuovi spazi iniziali e finali
    name = name.replace(' ', '_') # spazi --> underscore

    return  name

