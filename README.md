# Hooktheory_to_kern_converter
The goal of this script is to convert songs from the [HookTheory dataset](https://github.com/chrisdonahue/sheetsage-data/blob/main/hooktheory/Hooktheory.json.gz) into the corrisponding **kern file. For melodies this is done by using MIDI notation as reference. The code permits to select a song from the dataset and convert it in the corresponding **kern format.

For more information about the [dataset](https://github.com/chrisdonahue/sheetsage?tab=readme-ov-file).

You can find the complete list of songs in "list.txt", created with the function create_list() (utils.py).

The **kern format has a precise syntax and rules that can be found at the following [link](https://www.humdrum.org/guide/ch02/).

The main function is build_kern_file(): it reads the dictonary of one single song and its ID. Returns a string file of the whole kern content.

In the output folder you can find the first 100 files converted to kerning notation as an example.

All the converted can be found at the following [link](https://drive.google.com/drive/folders/1RaWtBcHzsbkbpXALwvnlJ54Hvmt7GwOe?usp=sharing).

You can upload a **kern file via [Verovio Humdrum viewer](https://verovio.humdrum.org/) to listen to the final result.

# Files Organization and Content

- **main.py**
- **build_kern_file.py**
- **data_conversions.py**: pitch_to_midi(), midi_to_kern_pitch(), duration_to_kern(), build_scale(), intervals_to_chord_quality(),      pitch_class_to_roman_numbers(), pitch_class_to_chord_notation()
- **temporal_structures.py**: compute_barline_positions(), get_active_meter(), split_at_barlines()
- **key_signatures.py**: get_active_key(), build_kern_key_sig(), build_tonal_token()
- **manage_poliphony.py**: split_into_voices(), voice_to_events()
- **harmony.py**: harmony_to_events()
- **beams.py**: is_rest(), beamable(), add_beams()
- **utils.py**: load_dataset(), extract_metadata(), display_song_list(), sanitize_filename(), create_list()
- **data_structures.py**: dictionaries for data structures
- **songs_list.txt**: complete list of songs in the dataset


# Project Logic 

```
main()
│
├─ load_dataset()                  (utils.py)
├─ display_song_list()/create_list()            (utils.py)
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
    |
    ├─ add_beams()
    │
    └─ harmony_to_events()
        ├─ build_scale()               (data_conversions.py)
        ├─ intervals_to_quality()      (data_conversions.py)
        └─ pc_to_roman_numeral()       (data_conversions.py) 
```

# Logic and Functions Description
- Load dataset (utils.py)
- Display song list (or create list) (utils.py)
- Select one song (main.py)
- Extract and print metadata with function extract_metadata() (utils.py)
- Call **build_kern_file()**: it reads song hooktheory ID and whole song dictionary. It will return a string with kern file content
    - Extract song data from annotation
    - Initial meter and key signature: **get_active_meter()** and **get_active_key()** (temporal_structures.py, key_signatures.py)
    - **compute_barline_positions()** (temporal_structures.py) 
    - **split_into_voices()**  (manage_poliphony.py)
    - For each voice: **voice_to_events()** (manage_poliphony.py)
        - **split_at_barlines()**: to manage legatos and rests (manage_poliphony.py)
    - **harmony_to_events()** (harmony.py)
        - **intervals_to_chord_quality()**
        - **pitch_class_to_roman_numbers()**
    - **add_beams()**
    - Collect and sort all attack timestamps (with set to automatically eliminate duplicates)
    - Build rows of kern file
        - Starting rows of the file with lines.append() 
        - **build_kern_key_sig()** for key token
        - **build_tonal_token()** 
        - **MAIN LOOP: loop through all the timestamps** 
            - For bars: lines.append(all_spines(f"={bar_number}"))  
            - **get_active_meter()** and eventually new_time_sig
            - Check tonality change with **get_active_key()** and eventually build_kern_key_sig() + build_tonal_token()
            - Melodic voices token
            - Chord token
            - Write row

# Run the code

## Clone the repository
```
git clone https://github.com/Marco9723/Hooktheory_to_kern_converter 
```
## Move into the project folder
```
cd .\Hooktheory_to_kern_converter  (or your repository)
```

## Run the project
```
python main.py [your dataset path] [your output path]
```
