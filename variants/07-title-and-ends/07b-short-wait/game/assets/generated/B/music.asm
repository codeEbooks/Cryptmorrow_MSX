; music.asm - made by game/assets/psg_music.py from
; c64/score.py and c64/sfx.py (the C64 game), for the
; PSG of the MSX (1 789 772.5 Hz). Do not edit: run
; tools/build_game.py --assets again.

SPEED_50    equ 6       ; frames a step, 50 Hz
SPEED_60    equ 7       ; frames a step, 60 Hz
GATE_BEFORE equ 2       ; release: frames before
                            ; the end of the last step
NOTE_REST   equ $60
CMD_LENGTH  equ $80
CMD_INSTR   equ $C0
PAT_END     equ $FF
ORDER_LOOP  equ $FF
TRANS_ZERO  equ $A0
WAVE_TONE   equ 1
WAVE_NOISE  equ 2
WAVE_HOLD   equ $FE
WAVE_LOOP   equ $FF
ENV_HOLD    equ $FF
NO_VIBRATO  equ $FF
FX_NOISE    equ $10         ; effects
FX_TAIL     equ $20
FX_STOP     equ $FF
SONG_THEME   equ 0
SONG_WON     equ 1
SONG_LOST    equ 2
SFX_SLASH   equ 1
SFX_HIT     equ 2
SFX_DUST    equ 3
SFX_PICKUP  equ 4
SFX_DOOR    equ 5
SFX_HURT    equ 6
SFX_LOST    equ 7
SFX_WON     equ 8

note_period:  ; PSG tone period of notes 0-95
        dw 0,0,0,0,0,0,0,0
        dw 0,4068,3839,3624,3420,3229,3047,2876
        dw 2715,2562,2419,2283,2155,2034,1920,1812
        dw 1710,1614,1524,1438,1357,1281,1209,1141
        dw 1077,1017,960,906,855,807,762,719
        dw 679,641,605,571,539,508,480,453
        dw 428,404,381,360,339,320,302,285
        dw 269,254,240,226,214,202,190,180
        dw 170,160,151,143,135,127,120,113
        dw 107,101,95,90,85,80,76,71
        dw 67,64,60,57,53,50,48,45
        dw 42,40,38,36,34,32,30,28
ins_wave:  ; instrument: wave table
        db $00,$00,$02,$07,$0C,$13,$19
ins_env:  ; volumes of a note
        db $00,$11,$3D,$69,$95,$A8,$BB
ins_rel:  ; volumes of the release
        db $06,$17,$43,$6F,$A6,$B9,$C0
ins_vib:  ; vibrato after n frames
        db $FF,$0C,$FF,$FF,$FF,$FF,$FF
rel_start:  ; release entry from volume 0-15
        db $09,$09,$08,$07,$07,$06,$05,$05
        db $04,$03,$03,$02,$01,$01,$00,$00
        db $24,$21,$1F,$1C,$1A,$17,$15,$12
        db $10,$0D,$0B,$08,$06,$03,$01,$00
        db $24,$21,$1F,$1C,$1A,$17,$15,$12
        db $10,$0D,$0B,$08,$06,$03,$01,$00
        db $24,$21,$1F,$1C,$1A,$17,$15,$12
        db $10,$0D,$0B,$08,$06,$03,$01,$00
        db $00,$00,$00,$00,$00,$00,$00,$00
        db $00,$00,$00,$00,$00,$00,$00,$00
        db $00,$00,$00,$00,$00,$00,$00,$00
        db $00,$00,$00,$00,$00,$00,$00,$00
        db $00,$00,$00,$00,$00,$00,$00,$00
        db $00,$00,$00,$00,$00,$00,$00,$00
env_data:
        db $0F,$0F,$0E,$0E,$0D,$FF,$0E,$0C,$0B,$09,$08,$06
        db $05,$03,$02,$00,$FF,$0F,$0F,$0E,$0E,$0D,$FF,$0F
        db $0E,$0E,$0D,$0D,$0D,$0C,$0C,$0B,$0B,$0B,$0A,$0A
        db $09,$09,$09,$08,$08,$07,$07,$07,$06,$06,$05,$05
        db $05,$04,$04,$03,$03,$03,$02,$02,$01,$01,$01,$00
        db $FF,$0B,$0D,$0F,$0E,$0D,$FF,$0F,$0E,$0E,$0D,$0D
        db $0D,$0C,$0C,$0B,$0B,$0B,$0A,$0A,$09,$09,$09,$08
        db $08,$07,$07,$07,$06,$06,$05,$05,$05,$04,$04,$03
        db $03,$03,$02,$02,$01,$01,$01,$00,$FF,$0B,$0D,$0F
        db $0E,$0D,$FF,$0F,$0E,$0E,$0D,$0D,$0D,$0C,$0C,$0B
        db $0B,$0B,$0A,$0A,$09,$09,$09,$08,$08,$07,$07,$07
        db $06,$06,$05,$05,$05,$04,$04,$03,$03,$03,$02,$02
        db $01,$01,$01,$00,$FF,$0F,$0E,$0D,$0C,$0B,$0A,$09
        db $08,$07,$06,$05,$04,$03,$02,$01,$00,$FF,$00,$FF
        db $0F,$0E,$0D,$0C,$0B,$0A,$09,$08,$07,$06,$05,$04
        db $03,$02,$01,$00,$FF,$00,$FF,$0F,$09,$02,$00,$FF
        db $00,$FF
vib_offset:  ; period, a cycle
        db $FF,$FF,$FF,$00,$01,$01,$01,$00
wave_ctrl:
        db $01,$FE,$01,$01,$01,$01,$FF,$01,$01,$01,$01,$FF
        db $02,$01,$01,$01,$01,$01,$FE,$02,$01,$02,$02,$02
        db $FE,$02,$FE
wave_arg:
        db $00,$00,$00,$03,$07,$0C,$02,$00,$04,$07,$0C,$07
        db $0D,$A8,$A4,$A1,$9D,$9A,$00,$08,$B2,$0A,$0B,$0C
        db $00,$04,$00
pat_addr:
        dw pat_bass_bar,pat_bass_half,pat_bass_fill
        dw pat_lead_a,pat_lead_b,pat_arp_intro
        dw pat_arp_break,pat_hats,pat_beat
        dw pat_fill,pat_half,pat_won_bass
        dw pat_won_lead,pat_won_arp,pat_lost_bass
        dw pat_lost_lead,pat_lost_arp,pat_silence
song_orders:  ; three order lists a song
        dw ord_theme_1,ord_theme_2,ord_theme_3
        dw ord_won_1,ord_won_2,ord_won_3
        dw ord_lost_1,ord_lost_2,ord_lost_3
ord_theme_1:
        db $A0,$00,$00,$9C,$00,$9B,$00,$A0,$00,$9C,$00,$A5
        db $00,$9B,$00,$A0,$00,$9C,$00,$A5,$01,$9B,$01,$A0
        db $02,$A3,$00,$9E,$00,$A0,$00,$9C,$00,$A3,$00,$9E
        db $00,$A5,$00,$9B,$02,$A0,$00,$9C,$00,$A5,$00,$9B
        db $00,$A0,$00,$9C,$00,$A5,$01,$9B,$01,$A0,$02,$A0
        db $00,$9C,$00,$A5,$00,$9B,$02,$FF,$00
ord_theme_2:
        db $05,$03,$04,$03,$06,$FF,$00
ord_theme_3:
        db $07,$07,$08,$09,$08,$08,$08,$08,$08,$08,$08,$09
        db $08,$08,$08,$08,$08,$08,$08,$09,$08,$08,$08,$08
        db $08,$08,$08,$09,$0A,$0A,$0A,$09,$FF,$00
ord_won_1:
        db $0B,$11,$FF,$01
ord_won_2:
        db $0C,$11,$FF,$01
ord_won_3:
        db $0D,$11,$FF,$01
ord_lost_1:
        db $0E,$11,$FF,$01
ord_lost_2:
        db $0F,$11,$FF,$01
ord_lost_3:
        db $10,$11,$FF,$01
pat_bass_bar:
        db $C0,$81,$19,$19,$25,$19,$19,$25,$19,$25,$FF
pat_bass_half:
        db $C0,$81,$19,$25,$19,$25,$FF
pat_bass_fill:
        db $C0,$81,$19,$19,$25,$19,$80,$25,$25,$81,$19,$20
        db $25,$FF
pat_lead_a:
        db $C1,$85,$38,$81,$36,$83,$34,$81,$38,$34,$87,$31
        db $83,$34,$39,$85,$39,$81,$38,$83,$36,$81,$39,$3D
        db $87,$3C,$83,$38,$3F,$85,$3D,$81,$3B,$83,$38,$81
        db $34,$38,$83,$39,$81,$38,$36,$83,$34,$31,$36,$39
        db $38,$3C,$8B,$3D,$83,$60,$FF
pat_lead_b:
        db $C1,$83,$3B,$81,$38,$3B,$87,$40,$85,$3F,$81,$3D
        db $83,$3B,$36,$85,$40,$81,$3F,$83,$3D,$38,$87,$39
        db $83,$3B,$3D,$81,$3B,$40,$83,$44,$42,$40,$87,$3F
        db $83,$42,$3F,$3D,$39,$36,$39,$87,$38,$83,$3C,$3F
        db $FF
pat_arp_intro:
        db $C2,$8F,$31,$31,$C3,$2D,$2C,$FF
pat_arp_break:
        db $C2,$8F,$31,$C3,$2D,$C2,$2A,$C3,$2C,$FF
pat_hats:
        db $C6,$81,$30,$30,$30,$30,$30,$30,$30,$30,$FF
pat_beat:
        db $C4,$81,$30,$C6,$30,$C5,$30,$C6,$30,$C4,$30,$C6
        db $30,$C4,$30,$C5,$30,$FF
pat_fill:
        db $C4,$81,$30,$C6,$30,$C5,$30,$C6,$30,$C5,$80,$30
        db $30,$81,$30,$80,$30,$30,$C4,$81,$30,$FF
pat_half:
        db $C4,$87,$30,$C5,$30,$FF
pat_won_bass:
        db $C0,$83,$1C,$28,$23,$28,$81,$1C,$20,$23,$28,$87
        db $1C,$FF
pat_won_lead:
        db $C1,$81,$3B,$40,$44,$47,$44,$47,$83,$4C,$81,$4B
        db $4C,$4E,$4B,$87,$4C,$FF
pat_won_arp:
        db $C3,$8B,$34,$83,$2F,$8F,$34,$FF
pat_lost_bass:
        db $C0,$87,$19,$15,$14,$83,$19,$60,$FF
pat_lost_lead:
        db $C1,$83,$38,$36,$34,$33,$8B,$31,$83,$60,$FF
pat_lost_arp:
        db $C2,$87,$31,$C3,$2D,$2C,$C2,$31,$FF
pat_silence:
        db $BF,$60,$FF
sfx_priority:  ; effects 1-8
        db $01,$02,$03,$03,$04,$05,$06,$06
fx_first:  ; effects 1-8
        db $01,$0B,$15,$2A,$42,$5B,$70,$B0
fx_data:  ; control, argument a frame
        db $FF,$00,$1F,$04,$1D,$05,$1D,$06,$1D,$08,$1D,$0A
        db $1D,$0C,$19,$0C,$32,$0C,$30,$0C,$FF,$00,$0F,$48
        db $0D,$43,$0D,$3C,$0C,$3C,$2A,$3C,$27,$3C,$24,$3C
        db $22,$3C,$20,$3C,$FF,$00,$1F,$0D,$1F,$10,$1F,$14
        db $1F,$18,$1F,$1B,$1F,$1F,$1F,$1F,$1F,$1F,$1F,$1F
        db $1F,$1F,$1E,$1F,$3C,$1F,$3B,$1F,$39,$1F,$38,$1F
        db $36,$1F,$35,$1F,$33,$1F,$32,$1F,$30,$1F,$FF,$00
        db $0F,$3C,$0D,$3C,$0D,$40,$0D,$40,$0D,$43,$0D,$43
        db $0D,$48,$0D,$48,$0D,$4C,$0D,$4C,$0D,$4F,$0D,$4F
        db $0D,$54,$0D,$54,$0D,$54,$2B,$54,$2A,$54,$28,$54
        db $26,$54,$24,$54,$22,$54,$21,$54,$20,$54,$FF,$00
        db $0F,$18,$0E,$18,$0E,$18,$0E,$19,$0E,$19,$0E,$19
        db $0E,$1A,$0E,$1A,$0E,$1A,$0E,$19,$0E,$19,$0E,$19
        db $1E,$1F,$1E,$1F,$1E,$1F,$3C,$1F,$3B,$1F,$39,$1F
        db $38,$1F,$36,$1F,$35,$1F,$33,$1F,$32,$1F,$30,$1F
        db $FF,$00,$0F,$39,$0E,$39,$0E,$37,$0E,$37,$0E,$34
        db $0E,$34,$0E,$30,$0E,$30,$0E,$2D,$0E,$2D,$0E,$2B
        db $0E,$2B,$0E,$28,$0E,$28,$0C,$28,$2A,$28,$27,$28
        db $24,$28,$22,$28,$20,$28,$FF,$00,$0F,$37,$0E,$37
        db $0E,$37,$0E,$37,$0E,$36,$0E,$36,$0E,$36,$0E,$36
        db $0E,$35,$0E,$35,$0E,$35,$0E,$35,$0E,$34,$0E,$34
        db $0E,$34,$0E,$34,$0E,$33,$0E,$33,$0E,$33,$0E,$33
        db $0E,$32,$0E,$32,$0E,$32,$0E,$32,$0E,$31,$0E,$31
        db $0E,$31,$0E,$31,$0E,$30,$0E,$30,$0E,$30,$0E,$30
        db $0E,$2F,$0E,$2F,$0E,$2F,$0E,$2F,$0E,$2E,$0E,$2E
        db $0E,$2E,$0E,$2E,$0E,$2D,$0E,$2D,$0E,$2D,$0E,$2D
        db $0E,$2C,$0E,$2C,$0E,$2C,$0E,$2C,$0E,$2C,$2D,$2C
        db $2C,$2C,$2B,$2C,$2A,$2C,$29,$2C,$28,$2C,$27,$2C
        db $26,$2C,$25,$2C,$24,$2C,$23,$2C,$22,$2C,$21,$2C
        db $20,$2C,$FF,$00,$0F,$40,$0E,$40,$0E,$40,$0E,$40
        db $0E,$44,$0E,$44,$0E,$44,$0E,$44,$0E,$47,$0E,$47
        db $0E,$47,$0E,$47,$0E,$4C,$0E,$4C,$0E,$4C,$0E,$4C
        db $0E,$4C,$0E,$4C,$0E,$4C,$0E,$4C,$0E,$4C,$0E,$4C
        db $0E,$4C,$0E,$4C,$0E,$4C,$0E,$4C,$0E,$4C,$0E,$4C
        db $0E,$4C,$2D,$4C,$2C,$4C,$2B,$4C,$2A,$4C,$29,$4C
        db $28,$4C,$27,$4C,$26,$4C,$25,$4C,$24,$4C,$23,$4C
        db $22,$4C,$21,$4C,$20,$4C,$FF,$00
music_end:
