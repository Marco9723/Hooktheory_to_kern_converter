import json
import sys
import os
from utils import load_dataset, display_song_list, extract_metadata, sanitize_filename
from build_kern_file import build_kern_file


def main() :
    
    # python hooktheory_to_kern.py dataset.json ./output
    if len(sys.argv) < 2:
        print("Missing arguments. Example: python main.py hooktheory.json ./output")
        sys.exit(1)


    dataset_path = sys.argv[1]
    # Se output_dir non è fornito, usiamo '.' (cartella corrente)
    output_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
    os.makedirs(output_dir, exist_ok=True)  # os.makedirs() crea la cartella

    # intro
    print("HookTheory to Kern converter")

    # loading
    try:
        songs = load_dataset(dataset_path)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"\nError: {e}")
        sys.exit(1)

    # song list
    songs_list = list(songs.items())
    print(f"There are {len(songs_list)} songs in the dataset.")

    # display
    display_song_list(songs)

    while True:  # valid song number
        try:
            song_number = input(f"\n Insert the number of the song to convert (0–{len(songs_list)-1}): ")
            idx = int(song_number.strip())
            
            if 0 <= idx < len(songs_list):
                break   
            print(f"Not valid index. Choose a number between 0 and {len(songs_list)-1}.")

        except:

            print("\nInput error!")
            sys.exit(0)   

    song_id, song = songs_list[idx]
    # Unpacking: la tupla (song_id, song_dict) viene assegnata a due variabili
    # meta = extract_metadata(song_id, song)
    hk, yt, ann, urls, song_name = extract_metadata(song_id, song)

    # print song info   <<<<<<
 

    # building kern file
    print("\n Starting building Kern file")
    try:
        kern_content = build_kern_file(song_id, song)
    except Exception as e:
        print(f"\nError during conversion!")
        sys.exit(1)

    # scrittura file
    file_name = sanitize_filename(song_name)
    kern_path = os.path.join(output_dir, file_name + '.krn')


    # write kern
    with open(kern_path, 'w', encoding='utf-8') as f:
        f.write(kern_content)
    print(f"\nFile **kern completed: {kern_path}")


    # print (for now)
    kern_lines = kern_content.splitlines()
    print(f"\n{'─'*50}")
    print(f"Final Kern conversion: ")
    print(f"\n{'─'*50}")
    for line in kern_lines:
        # kern_lines[:n_preview]: slice dei primi n_preview elementi
        print(f"  {line}")
    print(f"{'─'*50}\n")



if __name__ == '__main__':
    main()


