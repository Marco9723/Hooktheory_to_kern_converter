import json
import sys
import os
from utils import load_dataset, display_song_list, extract_metadata, sanitize_filename, get_name, create_list
from build_kern_file import build_kern_file


def main() :
    
    # to start the script (example): python hooktheory_to_kern.py dataset.json ./output
    if len(sys.argv) < 2:
        print("Missing arguments. Example: python main.py hooktheory.json ./output")
        sys.exit(1)

    dataset_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
    os.makedirs(output_dir, exist_ok=True)  

    print("HookTheory to Kern converter")
    print("Loading dataset...")

    # load dataset
    try:
        songs = load_dataset(dataset_path)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"\nError: {e}")
        sys.exit(1)

    # song list 
    songs_list = list(songs.items())
    print(f"{len(songs_list)} songs found in the dataset")

    # display & create list, if needed (create only the first time you execute the code)
    # display_song_list(songs)
    create_list(songs)

    while True:  # valid song number
        try:
            song_number = input(f"Insert the number of the song to convert (0–{len(songs_list)-1}): ")
            idx = int(song_number.strip())
            
            if 0 <= idx < len(songs_list):
                break   
            print(f"Not valid index. Choose a number between 0 and {len(songs_list)-1}.")

        except:
            print("\nInput error!")
            sys.exit(0)   

    song_id, song = songs_list[idx]
    
    # metadata
    hk, yt, ann, urls, song_name = extract_metadata(song)
    id = hk.get('id', 'Unknown')
    artist_name = hk.get('artist', 'Unknown')

    # print song info   
    print(f"\nHookTheory ID: {hk.get('id', 'Unknown')} \n" +
          f"Artist: {hk.get('artist', 'Unknown')} \n" +
          f"Song: {hk.get('song', 'Unknown')} \n" +
          f"YouTube link: {yt.get('url', 'Unknown')} \n" +
          f"Artist URL: {urls.get('artist','Unknown')} \n" + 
          f"Song URL: {urls.get('song','Unknown')} \n" +
          f"Clip URL: {urls.get('clip','Unknown')}" )
 
    # build kern file
    print("\nStarting building Kern file")
    try:
        kern_content = build_kern_file(song_id, song)
    except Exception as e:
        print(f"\nError during conversion!")
        sys.exit(1)

    # sanitize file name before saving
    file_name = song_number + " - " + sanitize_filename(song_name) + " - " + sanitize_filename(artist_name) + " - " + id
    kern_path = os.path.join(output_dir, file_name + '.krn')

    # write final kern file
    with open(kern_path, 'w', encoding='utf-8') as f:
        f.write(kern_content)
    print(f"\nFile **kern completed: {kern_path}")


if __name__ == '__main__':
    main()


