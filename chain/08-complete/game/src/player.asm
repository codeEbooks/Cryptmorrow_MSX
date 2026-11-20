; player.asm - the music and the effects on the PSG, once
; a frame from the interrupt. The notes are those of the
; C64 game (game/assets/c64/score.py and sfx.py), made
; into data by game/assets/psg_music.py (music.asm), and
; the player is Cryptmorrow ZX's, brought to the MSX: the
; PSG is the AY of the 128K at another clock.
;
; pattern bytes  $00-$5f note, $60 rest,
;                $80-$bf length (value - $7f steps),
;                $c0-$df instrument, $ff end
; order bytes    $00-$7f pattern, $80-$bf transpose
;                (value - $a0), $ff n: go to entry n
; wave tables    control (1 tone, 2 noise) and argument
;                per frame: for a tone, $00-$7f semitones
;                above the note or $80 + n the fixed note
;                n; for noise, the noise period; $ff n
;                jump, $fe hold
; envelopes      a volume (0-15) per frame, $ff hold
; effects        control (bits 0-3 volume, bit 4 noise,
;                bit 5 the release goes on without the
;                priority; $ff end) and argument (a note,
;                or a noise period) per frame
;
; Voice 1 (bass) plays on channel A, voice 2 (lead and
; arpeggios) on B, voice 3 (drums) on C. Three modes, as
; on the C64: MUSIC (the theme, and the piece of the
; end), SOUND FX (the effects, on channel A) or SILENT.
; Music and effects never sound together.
;
; Register 7 of the PSG also sets its two ports: bit 6
; at 0 keeps port A (the joysticks) an input, bit 7 at 1
; port B an output. Every value written to it here is
; 10xxxxxx.

MODE_MUSIC      equ 0           ; audio_mode
MODE_FX         equ 1
MODE_SILENT     equ 2
PSG_REGS        equ 11          ; 0-10 change every frame
R_NOISE         equ 6
R_MIXER         equ 7
R_VOLUME        equ 8           ; 8, 9, 10: channels A-C
MIXER_OFF       equ %10111111   ; tone and noise off
MIXER_TONE_A    equ %10111110   ; tone on channel A
MIXER_NOISE_A   equ %10110111   ; noise on channel A

; A voice: IX points to VOICE_SIZE bytes.
V_ORDER         equ 0           ; entry of the order list
V_ORDLO         equ 1           ; the order list
V_ORDHI         equ 2
V_PATLO         equ 3           ; next byte of the pattern
V_PATHI         equ 4
V_STEPS         equ 5           ; steps left of this event
V_LEN           equ 6           ; length of notes, in steps
V_NOTE          equ 7           ; note played, transposed
V_TRANS         equ 8           ; transposition, signed
V_INSTR         equ 9           ; instrument
V_WAVE          equ 10          ; entry of the wave table
V_CTRL          equ 11          ; this frame: tone or noise
V_ARG           equ 12          ; this frame: note or period
V_GATE          equ 13          ; 1 while the note sounds
V_ENV           equ 14          ; entry of env_data
V_VOL           equ 15          ; volume of this frame
V_AGE           equ 16          ; frames since the note
V_VIBPH         equ 17          ; vibrato phase
V_VIB           equ 18          ; vibrato after n frames
VOICE_SIZE      equ 19

; ---- set_audio ----------------------------------------
; A = MODE_MUSIC, MODE_FX or MODE_SILENT: the theme from
; its beginning, or every channel silent; no effect left
; playing or waiting, no frame of the music owed (the
; menu of the title changes the mode while the music
; plays). The interrupt is held off meanwhile.
set_audio:
        di
        ld (audio_mode),a
        xor a
        ld (sfx_next),a
        ld (sfx_pos),a
        ld (sfx_prio),a
        ld (music_owed),a
        ld a,(audio_mode)
        or a
        jr nz,sa_quiet          ; MODE_MUSIC is 0
        ld a,SONG_THEME
        call music_init
        ei
        ret
sa_quiet:
        call psg_silence
        ei
        ret

; ---- end_sound ----------------------------------------
; A = ENDED_LOST or ENDED_WON: in MUSIC mode the piece of
; the end, in SOUND FX mode its effect.
end_sound:
        ld c,a
        ld a,(audio_mode)
        or a
        jr nz,es_effect
        ld a,c
        cp ENDED_WON
        ld a,SONG_WON
        jr z,es_song
        ld a,SONG_LOST
es_song:
        di                      ; the interrupt plays it
        call music_init
        ei
        ret
es_effect:
        ld a,c
        cp ENDED_WON
        ld a,SFX_WON
        jr z,sound_effect
        ld a,SFX_LOST
                                ; on into sound_effect

; ---- sound_effect -------------------------------------
; A = SFX_ number. In SOUND FX mode it starts at the next
; frame, one at a time, unless a more important effect
; (sfx_priority, as on the C64) plays or was asked for.
; In MUSIC and SILENT it is not heard.
sound_effect:
        ld c,a
        ld a,(audio_mode)
        cp MODE_FX
        ret nz
        ld e,c
        ld d,0
        ld hl,sfx_priority-1
        add hl,de
        ld a,(hl)               ; its priority
        di                      ; sfx_prio is shared with
        ld hl,sfx_prio          ; the interrupt
        cp (hl)
        jr c,se_refused         ; less important: not heard
        ld (hl),a
        ld a,c
        ld (sfx_next),a
se_refused:
        ei
        ret

; ---- music_init ---------------------------------------
; A = song (SONG_THEME, SONG_WON, SONG_LOST), from its
; start: every register silent at once, then the song's
; first frame worked out, so that the next interrupt
; sends it. Call it with the interrupt held off.
music_init:
        ld (music_song),a
        call psg_silence
        xor a
        ld (music_tick),a
        ld (music_owed),a       ; nothing owed yet
        ld hl,0
        ld (music_frames),hl
        ld hl,voices            ; every voice byte to 0
        ld b,3*VOICE_SIZE
mi_clear:
        ld (hl),a
        inc hl
        djnz mi_clear
        ld a,(music_song)       ; 3 order lists a song,
        ld l,a                  ; 2 bytes each: song x 6
        add a,a
        add a,l
        add a,a
        ld l,a
        ld h,0
        ld de,song_orders
        add hl,de
        ex de,hl                ; DE = the first list
        ld ix,voices
        ld b,3
mi_voice:
        push bc
        ld a,(de)
        ld (ix+V_ORDLO),a
        inc de
        ld a,(de)
        ld (ix+V_ORDHI),a
        inc de
        ld (ix+V_LEN),1
        push de
        call next_pattern       ; its first pattern
        pop de
        ld bc,VOICE_SIZE
        add ix,bc
        pop bc
        djnz mi_voice
        jp music_step           ; its first frame, ready for
                                ; the next interrupt

; ---- psg_silence --------------------------------------
; The shadow registers to 0, the mixer off; then the 14
; registers of the sound written (11-13, the PSG's own
; envelope, stay at 0: the volumes never use it). Call it
; with the interrupt held off.
psg_silence:
        ld hl,psg_shadow
        ld b,PSG_REGS
ps_clear:
        ld (hl),0
        inc hl
        djnz ps_clear
        ld a,MIXER_OFF
        ld (psg_shadow+R_MIXER),a
        call psg_flush
        ld a,PSG_REGS           ; 11, 12, 13 to 0
ps_env:
        out (PSG_ADDR),a
        ld c,a
        xor a
        out (PSG_WRITE),a
        ld a,c
        inc a
        cp 14
        jr nz,ps_env
        ret

; ---- psg_flush ----------------------------------------
; Registers 0-10 from the shadow, in this order: the
; number to PSG_ADDR, the value to PSG_WRITE. OUTI sends
; (HL) to port (C) and moves HL on (it counts B down too:
; here B means nothing). 56 T-states a register.
psg_flush:
        ld hl,psg_shadow
        ld c,PSG_WRITE
        xor a                   ; register 0
pf_next:
        out (PSG_ADDR),a        ; 12
        outi                    ; 18
        inc a                   ; 5
        cp PSG_REGS             ; 8
        jr nz,pf_next           ; 13
        ret

; ---- audio_frame --------------------------------------
; From the interrupt. In MUSIC: send the registers worked
; out for this frame, so that the PSG changes at the same
; moment every frame. The next frame of the voices
; (music_step) is then worked out by the main loop, after
; the VRAM (music_due), or here while the main loop is
; building a room (music_by_isr). If the main loop did
; not work it out in time, it is worked out here before
; the registers are sent. In SOUND FX and SILENT:
; fx_frame.
audio_frame:
        ld a,(audio_mode)
        or a
        jr nz,fx_frame          ; not MODE_MUSIC
        ld a,(music_owed)
        or a
        call nz,music_step      ; late: work it out now
        call psg_flush
        ld a,(music_by_isr)
        or a
        jp nz,music_step        ; the main loop is busy
        inc a
        ld (music_owed),a       ; the main loop works it out
        ret

; ---- fx_frame -----------------------------------------
; SOUND FX or SILENT. In SOUND FX first this frame of the
; effect, if one plays: an entry of fx_data a frame (an
; effect asked for by sound_effect starts here, sfx_next);
; then the registers go to the PSG. So an effect sounds
; from the frame whose picture shows what asked for it.
; In SILENT only the silence goes.
fx_frame:
        ld a,(audio_mode)
        cp MODE_FX
        call z,fx_step          ; SOUND FX: this frame
        jp psg_flush

fx_step:
        ld a,(sfx_next)
        or a
        jr z,fx_entry           ; nothing new
        ld e,a
        ld d,0
        ld hl,fx_first-1
        add hl,de
        ld a,(hl)
        ld (sfx_pos),a          ; its first entry
        xor a
        ld (sfx_next),a
fx_entry:
        ld a,(sfx_pos)
        or a
        ret z                   ; no effect plays
        ld l,a                  ; entry: fx_data + 2 n
        ld h,0
        add hl,hl
        ld de,fx_data
        add hl,de
        ld a,(hl)               ; the control byte
        cp FX_STOP
        jr z,fx_over
        inc hl
        ld c,(hl)               ; C = the argument
        ld hl,sfx_pos
        inc (hl)                ; the next entry, next frame
        ld b,a
        and FX_TAIL
        jr z,fx_held
        xor a                   ; the release goes on: any
        ld (sfx_prio),a         ; effect may come now
fx_held:
        ld a,b
        and 15
        ld (psg_shadow+R_VOLUME),a ; channel A
        bit 4,b                 ; FX_NOISE
        jr nz,fx_noisy
        ld l,c                  ; a tone: note C, its period
        ld h,0
        add hl,hl
        ld de,note_period
        add hl,de
        ld a,(hl)
        ld (psg_shadow),a       ; registers 0 and 1
        inc hl
        ld a,(hl)
        ld (psg_shadow+1),a
        ld a,MIXER_TONE_A
        jr fx_mixer
fx_noisy:
        ld a,c
        ld (psg_shadow+R_NOISE),a
        ld a,MIXER_NOISE_A
fx_mixer:
        ld (psg_shadow+R_MIXER),a
        ret
fx_over:
        xor a                   ; the effect is over: silent
        ld (sfx_pos),a
        ld (sfx_prio),a
        ld (psg_shadow+R_VOLUME),a
        ld a,MIXER_OFF
        ld (psg_shadow+R_MIXER),a
        ret

; ---- music_due ----------------------------------------
; From the main loop, after the VRAM: the next frame of
; the voices, if it is owed.
music_due:
        ld a,(music_owed)
        or a
        ret z
                                ; on into music_step

; ---- music_step ---------------------------------------
; The next frame of the three voices, into psg_shadow.
music_step:
        xor a
        ld (music_owed),a
        ld a,MIXER_OFF          ; each voice opens its own
        ld (psg_shadow+R_MIXER),a
        ld ix,voices
        xor a
ms_voice:
        ld (voice_n),a
        call voice_frame
        ld bc,VOICE_SIZE
        add ix,bc
        ld a,(voice_n)
        inc a
        cp 3
        jr nz,ms_voice
        ld a,(music_tick)       ; the frame inside the step
        inc a
        ld hl,music_speed
        cp (hl)
        jr nz,ms_tick
        xor a
ms_tick:
        ld (music_tick),a
        ld hl,(music_frames)
        inc hl
        ld (music_frames),hl
        ret

; ---- voice_frame (IX = voice, voice_n = 0-2) ----------
; At the first frame of a step the next event of the
; pattern, when the last one is over; GATE_BEFORE frames
; before the end of an event's last step its release.
voice_frame:
        ld a,(music_tick)
        or a
        jr nz,vf_mid
        ld a,(ix+V_STEPS)       ; first frame of a step
        or a
        call z,next_event       ; event over: read more
        dec (ix+V_STEPS)
        jr vf_sound
vf_mid:
        add a,GATE_BEFORE
        ld hl,music_speed
        cp (hl)
        jr nz,vf_sound
        ld a,(ix+V_STEPS)
        or a
        call z,gate_off         ; last step: release it

; Wave table: tone or noise, and the note or period.
vf_sound:
        ld e,(ix+V_WAVE)
        ld d,0
vf_wave:
        ld hl,wave_ctrl
        add hl,de
        ld a,(hl)
        cp WAVE_HOLD
        jr z,vf_kept            ; keep the last entry
        cp WAVE_LOOP
        jr nz,vf_step
        ld hl,wave_arg          ; jump inside the table
        add hl,de
        ld e,(hl)
        jr vf_wave
vf_step:
        ld (ix+V_CTRL),a
        ld c,a
        ld hl,wave_arg
        add hl,de
        ld a,(hl)
        inc e                   ; next entry next frame
        bit 1,c                 ; noise: the period as is
        jr nz,vf_arg
        bit 7,a
        jr nz,vf_fixed
        add a,(ix+V_NOTE)       ; semitones above the note
        jr vf_arg
vf_fixed:
        and $7F                 ; a fixed note (drums)
vf_arg:
        ld (ix+V_ARG),a
vf_kept:
        ld (ix+V_WAVE),e

; Envelope: this frame's volume; then on, unless the
; next entry says hold.
        ld e,(ix+V_ENV)
        ld hl,env_data
        add hl,de
        ld a,(hl)
        ld (ix+V_VOL),a
        inc hl
        ld a,(hl)
        cp ENV_HOLD
        jr z,vf_held
        inc (ix+V_ENV)
vf_held:

; Tone or noise into the shadow registers.
        ld a,(voice_n)
        ld c,a                  ; C = voice
        ld a,(ix+V_CTRL)
        cp WAVE_NOISE
        jr z,vf_noise
        ld l,(ix+V_ARG)         ; the note's period
        ld h,0
        add hl,hl
        ld de,note_period
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        call vibrato            ; DE = period
        ld a,c                  ; registers 2v and 2v + 1
        add a,a
        ld l,a
        ld h,0
        push bc
        ld bc,psg_shadow
        add hl,bc
        pop bc
        ld (hl),e
        inc hl
        ld (hl),d
        ld hl,mix_tone          ; open the tone of channel v
        jr vf_open
vf_noise:
        ld a,(ix+V_ARG)         ; the noise period
        ld (psg_shadow+R_NOISE),a
        ld hl,mix_noise         ; open the noise of v
vf_open:
        ld b,0
        add hl,bc
        ld a,(psg_shadow+R_MIXER)
        and (hl)
        ld (psg_shadow+R_MIXER),a
        ld hl,psg_shadow+R_VOLUME
        add hl,bc
        ld a,(ix+V_VOL)
        ld (hl),a
        ld a,(ix+V_AGE)         ; age, up to 255
        inc a
        ret z
        ld (ix+V_AGE),a
        ret

mix_tone:   db $FE,$FD,$FB      ; mixer: tone on, A-C
mix_noise:  db $F7,$EF,$DF      ; mixer: noise on, A-C

; vibrato: DE = period; V_VIB frames after the start
; of the note (NO_VIBRATO: never), one of eight offsets
; a frame. C is kept.
vibrato:
        ld a,(ix+V_VIB)
        cp NO_VIBRATO
        ret z                   ; an instrument without
        ld b,a                  ; B = the delay
        ld a,(ix+V_AGE)
        cp b
        ret c                   ; not yet
        ld a,(ix+V_VIBPH)
        inc (ix+V_VIBPH)
        and 7
        ld l,a
        ld h,0
        push bc
        ld bc,vib_offset
        add hl,bc
        pop bc
        ld a,(hl)               ; signed offset
        ld l,a
        add a,a
        sbc a,a                 ; its sign in every bit
        ld h,a
        add hl,de
        ex de,hl
        ret

; ---- next_event (IX = voice) --------------------------
; Reads commands until a note or a rest.
next_event:
        ld l,(ix+V_PATLO)
        ld h,(ix+V_PATHI)
ne_read:
        ld a,(hl)
        inc hl
        cp PAT_END
        jr z,ne_end
        cp CMD_INSTR
        jr nc,ne_instr
        cp CMD_LENGTH
        jr nc,ne_length
        cp NOTE_REST
        jr z,ne_rest
        add a,(ix+V_TRANS)      ; a note: transpose it
        call start_note
        jr ne_done
ne_rest:
        call gate_off
ne_done:
        ld a,(ix+V_LEN)
        ld (ix+V_STEPS),a
        ld (ix+V_PATLO),l
        ld (ix+V_PATHI),h
        ret
ne_length:
        sub CMD_LENGTH-1
        ld (ix+V_LEN),a
        jr ne_read
ne_instr:
        and $1F
        ld (ix+V_INSTR),a
        jr ne_read
ne_end:
        call next_pattern
        jr next_event

; ---- next_pattern (IX = voice) ------------------------
; Follows the order list: transpositions, the loop, then
; the address of the next pattern.
next_pattern:
        ld l,(ix+V_ORDLO)
        ld h,(ix+V_ORDHI)
np_read:
        ld e,(ix+V_ORDER)
        ld d,0
        push hl
        add hl,de
        ld a,(hl)
        cp ORDER_LOOP
        jr nz,np_entry
        inc hl
        ld a,(hl)               ; the entry to go on from
        ld (ix+V_ORDER),a
        pop hl
        jr np_read
np_entry:
        pop hl
        inc (ix+V_ORDER)
        cp CMD_LENGTH
        jr c,np_pattern
        sub TRANS_ZERO
        ld (ix+V_TRANS),a
        jr np_read
np_pattern:
        add a,a
        ld e,a
        ld hl,pat_addr
        add hl,de
        ld a,(hl)
        ld (ix+V_PATLO),a
        inc hl
        ld a,(hl)
        ld (ix+V_PATHI),a
        ret

; ---- start_note (A = note, IX = voice) ----------------
; The instrument's wave table and volumes from their
; start; the gate on. HL is kept.
start_note:
        ld (ix+V_NOTE),a
        push hl
        ld e,(ix+V_INSTR)
        ld d,0
        ld hl,ins_wave
        add hl,de
        ld a,(hl)
        ld (ix+V_WAVE),a
        ld hl,ins_env
        add hl,de
        ld a,(hl)
        ld (ix+V_ENV),a
        ld hl,ins_vib
        add hl,de
        ld a,(hl)
        ld (ix+V_VIB),a
        xor a
        ld (ix+V_AGE),a
        ld (ix+V_VIBPH),a
        inc a
        ld (ix+V_GATE),a
        pop hl
        ret

; ---- gate_off (IX = voice) ----------------------------
; If the note sounds: the release, from the entry that
; is not louder than the volume of the last frame.
; HL is kept.
gate_off:
        ld a,(ix+V_GATE)
        or a
        ret z                   ; already released
        ld (ix+V_GATE),0
        push hl
        ld e,(ix+V_INSTR)
        ld d,0
        ld hl,ins_rel
        add hl,de
        ld c,(hl)               ; C = its release
        ex de,hl                ; rel_start + 16 x instr
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld de,rel_start
        add hl,de
        ld e,(ix+V_VOL)
        ld d,0
        add hl,de
        ld a,(hl)
        add a,c
        ld (ix+V_ENV),a
        pop hl
        ret
