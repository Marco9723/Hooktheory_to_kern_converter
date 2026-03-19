# Hooktheory_to_kern_converter

## Project logic 

main()
  │
  ├─ load_dataset() in utils.py            
  ├─ display_song_list() in utils.py       
  └─ build_kern_file() in build_kern_file.py    
       │
       ├─ compute_barline_positions() in temporal_structures.py 
       ├─ get_active_meter/key() in temporal_structures.py      
       ├─ build_kern_key_sig() in key_signature.py        
       ├─ build_tonal_token() in key_signature.py         
       ├─ split_into_voices() in manage_poliphony.py     
       │     └─ voice_to_events() in manage_poliphony.py       
       │           ├─ pitch_to_midi() in data_conversions.py         
       │           ├─ midi_to_kern_pitch() in data_conversions.py        
       │           ├─ duration_to_kern() in data_conversions.py        
       │           └─ split_at_barlines() in temporal_structures.py        
       │
       └─ harmony_to_events()          
             ├─ build_scale() in data_conversions.py           
             ├─ intervals_to_quality() in data_conversions.py  
             └─ pc_to_roman_numeral() in data_conversions.py  