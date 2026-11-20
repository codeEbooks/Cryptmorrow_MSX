; cryptmorrow.asm - Cryptmorrow for the MSX1: the whole
; cartridge, 32 KB from #4000 to #BFFF.
; Step 5 of the book: the explorer, in two colours,
; starts in the Moss Gate, walks through the 16 rooms,
; picks up keys, treasures, potions and seals, opens the
; locked doors with their keys and, with the three
; seals, the portal: out through it, VICTORY. Skeletons
; patrol and bats chase; the sword (SPACE) defeats them
; a touch costs energy: with none left, GAME OVER.
;
; sjasmplus -DSTART_ROOM=1 -igenerated/B
;           --raw=cryptmorrow.rom cryptmorrow.asm
; pasmo --equ START_ROOM=1 -I generated/B
;           cryptmorrow.asm cryptmorrow.rom
; generated/B: the graphics (game/assets/build_msx.py).

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
code_end:

; ---- data ---------------------------------------------
        include "gfx_zones.asm"
        include "gfx_explorer.asm"
        include "gfx_combat.asm"
        include "gfx_rooms.asm"
        include "gfx_doors.asm"
data_end:

        ds #C000-$,#FF          ; 32 768 bytes in all
