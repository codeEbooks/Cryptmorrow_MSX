; cryptmorrow.asm - Cryptmorrow for the MSX1: the whole
; cartridge, 32 KB from #4000 to #BFFF.
; Version 1.0, the complete game. At power on the
; opening screen, three seconds or until FIRE; then the
; title, whose menu chooses the sound (MUSIC, SOUND FX,
; SILENT); FIRE starts the game: the explorer, in two
; colours, starts in the Moss Gate, walks through the 16
; rooms, picks up keys, treasures, potions and seals,
; opens the locked doors with their keys and, with the
; three seals, the portal: out through it, VICTORY.
; Skeletons patrol and bats chase; the sword defeats
; them; a touch costs energy: with none left, GAME OVER.
; Then the end screen, and the title again.
;
; sjasmplus -DSTART_ROOM=1 -DSOUND_MODE=0 -DSTART_PLAY=0
;           -igenerated/B --raw=cryptmorrow.rom
;           cryptmorrow.asm
; pasmo --equ START_ROOM=1 --equ SOUND_MODE=0
;           --equ START_PLAY=0 -I generated/B
;           cryptmorrow.asm cryptmorrow.rom
; START_PLAY=1: the game at once in room START_ROOM, in
; mode SOUND_MODE, without the title (for the tests).
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
        include "screens.asm"
code_end:

; ---- data ---------------------------------------------
        include "gfx_zones.asm"
        include "gfx_explorer.asm"
        include "gfx_combat.asm"
        include "gfx_rooms.asm"
        include "gfx_screens.asm"
        include "gfx_opening.asm"
        include "gfx_doors.asm"
        include "music.asm"
data_end:

        ds #C000-$,#FF          ; 32 768 bytes in all
