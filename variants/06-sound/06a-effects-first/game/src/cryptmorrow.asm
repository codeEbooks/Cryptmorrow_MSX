; cryptmorrow.asm - Cryptmorrow for the MSX1: the whole
; cartridge, 32 KB from #4000 to #BFFF.
; Step 6 of the book: the game of step 5 with its
; sound: the PSG plays the music and the effects, in the
; mode given to the assembler (SOUND_MODE).
;
; sjasmplus -DSTART_ROOM=1 -DSOUND_MODE=0 -igenerated/B
;           --raw=cryptmorrow.rom cryptmorrow.asm
; pasmo --equ START_ROOM=1 --equ SOUND_MODE=0
;           -I generated/B cryptmorrow.asm cryptmorrow.rom
; SOUND_MODE: 0 MUSIC, 1 SOUND FX, 2 SILENT.
; generated/B: the graphics (game/assets/build_msx.py)
; and the music (game/assets/psg_music.py).

        include "msx.asm"
        include "vars.asm"

        org #4000

; ---- the cartridge header (16 bytes) ------------------
        db "AB"                 ; a ROM with code
        dw init                 ; INIT: called by the BIOS
        dw 0                    ; STATEMENT: none
        dw 0                    ; DEVICE: none
        dw 0                    ; TEXT: none
        db 0,0,0,0,0,0          ; reserved

        include "start.asm"
        include "main.asm"
        include "interrupt.asm"
        include "vdp.asm"
        include "zone.asm"
        include "room.asm"
        include "hud.asm"
        include "torches.asm"
        include "input.asm"
        include "hero.asm"
        include "world.asm"
        include "objects.asm"
        include "combat.asm"
        include "player.asm"
code_end:

; ---- data ---------------------------------------------
        include "gfx_zones.asm"
        include "gfx_explorer.asm"
        include "gfx_combat.asm"
        include "gfx_rooms.asm"
        include "gfx_doors.asm"
        include "music.asm"
data_end:

        ds #C000-$,#FF          ; 32 768 bytes in all
