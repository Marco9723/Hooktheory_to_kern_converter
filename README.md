# Hooktheory_to_kern_converter
The goal of this script is to convert songs from the HookTheory dataset (LINK TO HOOKTHEORY) into the corrisponding **kern file.
For melodies this is done by using MIDI notation as reference.
The code permits to select a song from the dataset and convert it.
You can find the complete list of songs in "list.txt", created with the function create_list() (utils.py).

(KERN NOTATION INFOS)

The main function is build_kern_file(): it reads the dictonary of one single song and its ID. Returns a string file of the whole kern content.

## Files content
- main.py
- build_kern_file.py
- data_structures.py
- data_conversions.py
- temporal_structures.py
- key_signatures.py
- manage_poliphony.py
- harmony.py
- utils.py
- songs_list.txt


## Project logic 

```
main()
│
├─ load_dataset()                  (utils.py)
├─ display_song_list()             (utils.py)
└─ build_kern_file()               (build_kern_file.py)
    │
    ├─ compute_barline_positions() (temporal_structures.py)
    ├─ get_active_meter & get_active_key()      (temporal_structures.py)
    ├─ build_kern_key_sig()        (key_signature.py)
    ├─ build_tonal_token()         (key_signature.py)
    │
    ├─ split_into_voices()         (manage_poliphony.py)
    │   └─ voice_to_events()       (manage_poliphony.py)
    │       ├─ pitch_to_midi()         (data_conversions.py)
    │       ├─ midi_to_kern_pitch()    (data_conversions.py)
    │       ├─ duration_to_kern()      (data_conversions.py)
    │       └─ split_at_barlines()     (temporal_structures.py)
    │
    └─ harmony_to_events()
        ├─ build_scale()               (data_conversions.py)
        ├─ intervals_to_quality()      (data_conversions.py)
        └─ pc_to_roman_numeral()       (data_conversions.py) 
```

## Main functions' descriptions
get_active_meter(): used to get the meter of the song at a given time. Also used in build_kern_file() to get the initial meter. (INPUTS AND OUTPUTS IN TUTTE LE FUNZIONI!)

get_active_key(): used to get the key of the song at a given time. Also used in build_kern_file() to get the initial key.

compute_barline_positions()

split_into_voices()

## Run the code