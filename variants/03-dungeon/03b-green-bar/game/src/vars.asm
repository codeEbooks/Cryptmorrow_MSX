; vars.asm - the RAM of page 3 (#C000-#F37F): every byte
; has one owner, named here.

; ---- the frame ----------------------------------------
frames          equ #C000       ; 2: interrupts counted

; ---- start-up -----------------------------------------
cart_slot       equ #C003       ; our slot, E000SSPP

; ---- the room -----------------------------------------
room            equ #C005       ; number of the room shown
zone            equ #C006       ; its zone, #FF = none yet
zone_mt         equ #C007       ; 2: the zone's metatiles
room_rec        equ #C05B       ; 2: this room's record
zone_so         equ #C054       ; 2: the zone's solid kinds
flame_count     equ #C009       ; flame slots of the zone
flame_list      equ #C00A       ; 6 x 3: VRAM address, type
FLAME_MAX       equ 6           ; build_msx.py: no more
flame_phase     equ #C056       ; phase drawn, x 8
reveal_due      equ #C057       ; 1: a room to reveal

; ---- the HUD ------------------------------------------
energy          equ #C01C       ; 0-8
key_set         equ #C01D       ; keys carried: bits 0-2 A-C
seals           equ #C01E       ; seals carried, 0-3
score           equ #C01F       ; 3: BCD, high byte first
hud_row         equ #C022       ; 32: row 0 of the screen
hud_dirty       equ #C05D       ; 1: row 0 to draw again

; ---- work ---------------------------------------------
cells_left      equ #C042       ; load_third: cells to go
cells_skip      equ #C716       ; load_third: the bands'
row_third       equ #C043       ; build_room: third x 4

; ---- the explorer -------------------------------------
input           equ #C044       ; 1 = held: bits of JOY_*
hero_x          equ #C045       ; screen pixels, top left
hero_y          equ #C046
hero_dir        equ #C047       ; DIR_DOWN, UP, LEFT, RIGHT
hero_frame      equ #C048       ; 0 standing, 1 the step
hero_timer      equ #C049       ; frames since the last step
hero_moving     equ #C04A       ; 1 if it moved this frame
hero_sat        equ #C04C       ; 8: 2 x Y, X, shape, ink

; ---- buffers ------------------------------------------
room_names      equ #C100       ; 640: rows 2-21 of names
name_row        equ #C380       ; 32: row 23, the name
solid_map       equ #C400       ; 640: 1 = solid, 32 x 20

; ---- the interrupt and the stack ----------------------
IM2_TAB         equ #F000       ; 257 bytes of IM2_HI
IM2_HI          equ #F1         ; the table points at #F1F1
IM2_JP          equ #F1F1       ; JP isr
STACK           equ #F380       ; BIOS work area above
