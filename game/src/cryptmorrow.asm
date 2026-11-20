; cryptmorrow.asm - Cryptmorrow for the MSX1: the whole
; cartridge, 32 KB from #4000 to #BFFF.
; Version 1.0, the complete game. At power on the        {8}
; opening screen, three seconds or until FIRE; then the  {8}
; title, whose menu chooses the sound (MUSIC, SOUND FX,  {8}
; SILENT); FIRE starts the game: the explorer, in two    {8}
; colours, starts in the Moss Gate, walks through the 16 {8}
; rooms, picks up keys, treasures, potions and seals,    {8}
; opens the locked doors with their keys and, with the   {8}
; three seals, the portal: out through it, VICTORY.      {8}
; Skeletons patrol and bats chase; the sword defeats     {8}
; them; a touch costs energy: with none left, GAME OVER. {8}
; Then the end screen, and the title again.              {8}
;|; Step 1 of the book: the Moss Gate on the screen, its   {1-1}
;|; name between two rules, its torches burning.           {1-1}
;|; Step 2 of the book: the explorer, in two colours,      {2-2}
;|; walks in the Moss Gate (the arrows, or joystick 1).    {2-2}
;|; Step 3 of the book: the explorer, in two colours,      {3-3}
;|; starts in the Moss Gate and walks through the 16       {3-3}
;|; rooms; the HUD.                                        {3-3}
;|; Step 4 of the book: the explorer, in two colours,      {4-4}
;|; starts in the Moss Gate, walks through the 16 rooms,   {4-4}
;|; picks up keys, treasures, potions and seals, opens the {4-4}
;|; locked doors with their keys and, with the three       {4-4}
;|; seals, the portal: out through it, VICTORY.            {4-4}
;|; Step 5 of the book: the explorer, in two colours,      {5-5}
;|; starts in the Moss Gate, walks through the 16 rooms,   {5-5}
;|; picks up keys, treasures, potions and seals, opens the {5-5}
;|; locked doors with their keys and, with the three       {5-5}
;|; seals, the portal: out through it, VICTORY. Skeletons  {5-5}
;|; patrol and bats chase; the sword (SPACE) defeats them; {5-5}
;|; a touch costs energy: with none left, GAME OVER.       {5-5}
;|; Step 6 of the book: the game of step 5 with its        {6-6}
;|; sound: the PSG plays the music and the effects, in the {6-6}
;|; mode given to the assembler (SOUND_MODE).              {6-6}
;|; Step 7 of the book: at power on the title, whose       {7-7}
;|; menu chooses the sound (MUSIC, SOUND FX, SILENT); FIRE {7-7}
;|; starts the game: the explorer, in two colours, starts  {7-7}
;|; in the Moss Gate, walks through the 16 rooms, picks up {7-7}
;|; keys, treasures, potions and seals, opens the locked   {7-7}
;|; doors with their keys and, with the three seals, the   {7-7}
;|; portal: out through it, VICTORY. Skeletons patrol and  {7-7}
;|; bats chase; the sword defeats them; a touch costs      {7-7}
;|; energy: with none left, GAME OVER. Then the end        {7-7}
;|; screen, and the title again.                           {7-7}
;
; sjasmplus -DSTART_ROOM=1 -DSOUND_MODE=0 -DSTART_PLAY=0 {7}
;           -igenerated/B --raw=cryptmorrow.rom {7}
;           cryptmorrow.asm {7}
; pasmo --equ START_ROOM=1 --equ SOUND_MODE=0 {7}
;           --equ START_PLAY=0 -I generated/B {7}
;           cryptmorrow.asm cryptmorrow.rom {7}
; START_PLAY=1: the game at once in room START_ROOM, in {7}
; mode SOUND_MODE, without the title (for the tests). {7}
;|; sjasmplus -DSTART_ROOM=1 -DSOUND_MODE=0 -igenerated/B {6-6}
;|;           --raw=cryptmorrow.rom cryptmorrow.asm {6-6}
;|; pasmo --equ START_ROOM=1 --equ SOUND_MODE=0 {6-6}
;|;           -I generated/B cryptmorrow.asm cryptmorrow.rom {6-6}
;|; SOUND_MODE: 0 MUSIC, 1 SOUND FX, 2 SILENT. {6-6}
;|; sjasmplus -DSTART_ROOM=1 -igenerated/B {-5}
;|;           --raw=cryptmorrow.rom cryptmorrow.asm {-5}
;|; pasmo --equ START_ROOM=1 -I generated/B {-5}
;|;           cryptmorrow.asm cryptmorrow.rom {-5}
; generated/B: the graphics (game/assets/build_msx.py) {6}
; and the music (game/assets/psg_music.py). {6}
;|; generated/B: the graphics (game/assets/build_msx.py). {-5}

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
        include "input.asm"     ; {2}
        include "hero.asm"      ; {2}
        include "world.asm"     ; {3}
        include "objects.asm"   ; {4}
        include "combat.asm"    ; {2}
        include "player.asm"    ; {6}
        include "screens.asm"   ; {7}
code_end:

; ---- data ---------------------------------------------
        include "gfx_zones.asm"
        include "gfx_explorer.asm" ; {2}
        include "gfx_combat.asm" ; {5}
        include "gfx_rooms.asm"
        include "gfx_screens.asm" ; {7}
        include "gfx_opening.asm" ; {8}
        include "gfx_doors.asm" ; {4}
        include "music.asm"     ; {6}
data_end:

        ds #C000-$,#FF          ; 32 768 bytes in all
