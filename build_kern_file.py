from fractions import Fraction 
from temporal_structures import get_active_meter, compute_barline_positions
from key_signatures import get_active_key, build_kern_key_sig, build_tonal_token
from manage_poliphony import split_into_voices, voice_to_events
from harmony import harmony_to_events
from typing import List, Dict




def build_kern_file(song_id: str, song: Dict) -> str:
    """
    1) Estrai i dati dalle annotations
    2) Calcola le stanghette
    3) Dividi la melodia in voci e converti in eventi
    4) Converti gli accordi in eventi
    5) Raccogli tutti i timestamp, scorri e scrivi riga per riga

    song_id: chiave del dataset (ID HookTheory, es. 'qveoYyGGodn')
    song   : dizionario con tutti i dati della canzone
       >>>> Stringa con il contenuto del file **kern pronto per la scrittura
    """

    # 1) data extraction from annotations
    annotations = song.get('annotations', {})  # se 'annotations' manca, usiamo dict vuoto. Questo evita KeyError e rende il codice robusto a dati mancanti
    num_beats    = int(annotations.get('num_beats', 0)) # converti a intero!
    meters       = annotations.get('meters',  [{'beat':0,'beats_per_bar':4,'beat_unit':4}])
    keys         = annotations.get('keys',    [{'beat':0,'tonic_pitch_class':0, 'scale_degree_intervals':[2,2,1,2,2,2]}])
    melody_notes = annotations.get('melody')  or []  # or [] perchè dataset può avere "melody" null  # .get('melody', []) restituisce None se la chiave esiste ma vale null.
    harmony_list = annotations.get('harmony') or []

    # Stima num_beats se mancante 
    # Alcuni brani nel dataset potrebbero avere num_beats=0 o assente. Lo stimiamo dall'offset massimo delle note o degli accordi.
    if num_beats == 0 and melody_notes:
        # max() con key: restituisce la nota con l'offset più grande
        # poi prendiamo il suo offset e arrotondiamo per eccesso
        num_beats = int(max(melody_notes, key=lambda n: n['offset'])['offset'] + 0.99)
    if num_beats == 0 and harmony_list:
        num_beats = int(max(harmony_list, key=lambda c: c['offset'])['offset'] + 0.99)
    if num_beats == 0:
        num_beats = 4   # fallback minimo: almeno una misura di 4/4

    # 2) metrica e tonalità iniziali
    # Ci servono per scrivere l'header del file.
    # Usiamo Fraction(0) per essere coerenti con il resto del codice.
    init_beats_per_bar, init_beat_unit = get_active_meter(Fraction(0), meters)
    init_tonic, init_intervals = get_active_key(Fraction(0), keys)

    # 3) calcolo stanghette 
    barline_positions = compute_barline_positions(meters, num_beats)

    # 4) divisione melodia in voci e conversione eventi
    voices = split_into_voices(melody_notes)
    if not voices or voices == [[]]:
        voices = [[]]
        print("No melodic lines: spine **kern empty.")

    n_voices = len(voices)
    total_spines = n_voices + 1

    # Costruiamo la lista degli eventi per ogni voce
    # È una "lista di liste di tuple": per ogni voce, una sequenza di eventi
    voice_events_list = []  # List[List[Tuple[Fraction, Fraction, str]]]
    for v_notes in voices:
        v_events = voice_to_events(v_notes, barline_positions, num_beats, init_beat_unit)
        voice_events_list.append(v_events)

    # 5) conversione accordi in eventi 
    harm_events = harmony_to_events(harmony_list, keys)

    # 6) raccogliamo tutti i timestamp di attacco 
    # Usiamo un set per eliminare automaticamente i duplicati.
    # (es. voce1 e accordo potrebbero avere un attacco allo stesso beat)
    all_onsets = set()  # Set[Fraction] =

    for v_ev in voice_events_list:
        for (t, _, _) in v_ev:
            # _ è una convenzione: "questa variabile esiste ma non la uso". La tupla ha 3 elementi, ci interessa solo il primo (onset)
            all_onsets.add(t)

    for (t, _, _) in harm_events:
        all_onsets.add(t)

    # Aggiungiamo le stanghette come timestamp: dobbiamo emetterle anche se non coincidono con nessun attacco melodico/armonico
    for bl in barline_positions:
        all_onsets.add(bl)

    sorted_onsets = sorted(all_onsets)
    # sorted() su un set: converte in lista ordinata (il set non è ordinato)

    # 7) indici di scorrimento lineari
    # Per ogni timeline (voce o armonia), teniamo un indice che punta all'evento corrente. Lo avanziamo solo quando emettiamo quell'evento.
    v_idx = [0] * n_voices    # lista di n_voices zeri: un indice per ogni voce
    h_idx = 0                  # indice per gli accordi

    # 8) costruiamo le righe del file
    lines: List[str] = []     # ogni elemento sarà una riga del file **kern

    # 9) metadata
    hk   = song.get('hooktheory', {})
    yt   = song.get('youtube', {})
    urls = hk.get('urls', {})

    def rename(slug: str) -> str:   # local function  adam-lambert--> Adam Lambert
        return ' '.join(w.capitalize() for w in slug.split('-'))

    artist_name = rename(hk.get('artist', 'Unknown Artist'))
    song_name   = rename(hk.get('song',   'Unknown Song'))

    def all_spines(token: str) -> str:
        # Replica un token su tutte le spine, separate da TAB
        return '\t'.join([token] * total_spines)

    # 10) File intro
    lines.append(f"!!!title: {song_name}")
    lines.append(f"!!!OTL: {song_name}")
    lines.append(f"!!!COM: {artist_name}")
    lines.append(f"!!!OPR: {artist_name}")
    lines.append(f"!!!hooktheory-id: {song_id}")

    # 11) Intestazione delle spine: ['**kern'] * n_voices  && ['**mxhm'] 
    lines.append('\t'.join(['**kern'] * n_voices + ['**mxhm']))

    # 12) Token di configurazione iniziali 
    # chiave di violino standard, la spina **mxhm riceve '*' = "token nullo" (non ha una chiave)
    clef_row = '\t'.join(['*clefG2'] * n_voices + ['*'])
    lines.append(clef_row)

    # variabili di stato per tenere traccia della configurazione corrente
    # le uso per evitare di riscrivere token uguali inutilmente e per rilevare i cambi di tonalità/metrica
    key_sig_token  = build_kern_key_sig(init_tonic, init_intervals)
    tonal_token    = build_tonal_token(init_tonic, init_intervals)
    time_sig_token = f"*M{init_beats_per_bar}/{init_beat_unit}"

    # queste vanno ripetute su tutte le spines
    lines.append(all_spines(key_sig_token))    # *k[f#c#]\t*k[f#c#]
    lines.append(all_spines(tonal_token))      # *D:\t*D:
    lines.append(all_spines(time_sig_token))   # *M4/4\t*M4/4

    # =1- = stanghetta di apertura
    lines.append(all_spines('=1-'))

    # variabili di stato per il loop principale 
    bar_number        = 1     # numero della misura corrente (partendo da 1)
    next_barline_idx  = 0     # puntatore nella lista barline_positions

    # Loop principale: scorriamo tutti i timestamp 
    for t in sorted_onsets:

        # set bar
        # se questo timestamp è una stanghetta, la emettiamo PRIMA degli eventi.
        # poi continua a processare gli eventi che hanno onset coincidente con la stanghetta stessa
        if (next_barline_idx < len(barline_positions) and t == barline_positions[next_barline_idx]):
            bar_number += 1
            lines.append(all_spines(f"={bar_number}"))
            next_barline_idx += 1
            

        
        # Verifica se la metrica è cambiata rispetto all'ultima emessa. I cambi di metrica coincidono sempre con una stanghetta
        bpb_t, bu_t = get_active_meter(t, meters)
        new_time_sig = f"*M{bpb_t}/{bu_t}"
        if new_time_sig != time_sig_tok and t in set(barline_positions):
            lines.append(all_spines(new_time_sig))
            time_sig_tok = new_time_sig    

        # tonality change
        tonic_t, intervals_t = get_active_key(t, keys)
        new_key_sig = build_kern_key_sig(tonic_t, intervals_t)
        new_tonal   = build_tonal_token(tonic_t, intervals_t)
        if new_key_sig != key_sig_tok:
            # scriviamo firma in chiave che il token di tonalità
            lines.append(all_spines(new_key_sig))
            lines.append(all_spines(new_tonal))
            key_sig_tok = new_key_sig    # aggiorniamo lo stato

        # melodic voices token
        row_tokens = []  # : List[str]

        for v in range(n_voices):
            v_events = voice_events_list[v]   # eventi di questa voce
            i = v_idx[v]                       # indice corrente di questa voce

            if i < len(v_events) and v_events[i][0] == t:
                # questo evento della voce inizia esattamente a questo timestamp
                row_tokens.append(v_events[i][2])   # [2] è il token **kern
                v_idx[v] += 1                      
            else:
                # nessun attacco a questo timestamp per questa voce: l'evento precedente continua --> token '.'
                row_tokens.append('.')

        # chord token
        if h_idx < len(harm_events) and harm_events[h_idx][0] == t:
            harm_tok = harm_events[h_idx][2]
            h_idx += 1
        else:
            harm_tok = '.'   # accordo precedente ancora in corso

        # write the row
        # Aggiungiamo la riga SOLO se almeno una spina ha un evento reale --> evita righe inutili di soli '.'
        if any(tok != '.' for tok in row_tokens) or harm_tok != '.':
            lines.append('\t'.join(row_tokens + [harm_tok]))


    # spine ending
    lines.append('\t'.join(['*-'] * total_spines))

    return '\n'.join(lines)