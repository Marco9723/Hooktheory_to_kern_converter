# Hooktheory_to_kern_converter

## Project logic 

main()
│
├─ load_dataset()                  (utils.py)
├─ display_song_list()             (utils.py)
└─ build_kern_file()               (build_kern_file.py)
    │
    ├─ compute_barline_positions() (temporal_structures.py)
    ├─ get_active_meter/key()      (temporal_structures.py)
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