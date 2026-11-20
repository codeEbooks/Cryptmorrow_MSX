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

; ---- work ---------------------------------------------
cells_left      equ #C042       ; load_third: cells to go
cells_skip      equ #C716       ; load_third: the bands'
row_third       equ #C043       ; build_room: third x 4

; ---- buffers ------------------------------------------
room_names      equ #C100       ; 640: rows 2-21 of names
name_row        equ #C380       ; 32: row 23, the name
solid_map       equ #C400       ; 640: 1 = solid, 32 x 20

; ---- the interrupt and the stack ----------------------
IM2_TAB         equ #F000       ; 257 bytes of IM2_HI
IM2_HI          equ #F1         ; the table points at #F1F1
IM2_JP          equ #F1F1       ; JP isr
STACK           equ #F380       ; BIOS work area above
