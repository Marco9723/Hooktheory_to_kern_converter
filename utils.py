import json
import os
from typing import Dict


def load_dataset(filepath: str):   
     
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: '{filepath}'")

    with open(filepath, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    
    if isinstance(dataset, dict):
        songs = {k: v for k, v in dataset.items() if isinstance(v, dict) and 'annotations' in v}
        if songs:
            return songs
        if dataset:
            return dataset   


def extract_metadata(song: Dict):  
    hk   = song.get('hooktheory', {})
    yt   = song.get('youtube', {})
    ann  = song.get('annotations', {})
    urls = hk.get('urls', {})
    song_name   = song.get('hooktheory', {}).get('song', 'Unknown')

    return hk, yt, ann, urls, song_name


def display_song_list(songs: Dict[str, Dict]):

    # items() returns tuples (key, value) 
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

    name = name.strip()           # removes spaces at end and beginning
    name = name.replace(' ', '_') # space = underscore

    return  name
        

def get_name(s):
    return ' '.join(w.capitalize() for w in s.split('-'))


def create_list(songs: Dict[str, Dict], output_path: str = 'songs_list.txt'):

    def get_name(s):
        return ' '.join(w.capitalize() for w in s.split('-'))

    lines = []

    for i, (sid, song) in enumerate(songs.items()):
        hk  = song.get('hooktheory', {})
        artist = get_name(hk.get('artist', 'Unknown'))
        title  = get_name(hk.get('song',   'Unknown'))
        lines.append(f"{i:4d}:  {artist:<28}  {title:<32}  ")

    content = '\n'.join(lines)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"List created")