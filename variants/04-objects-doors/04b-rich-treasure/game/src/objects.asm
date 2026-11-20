; objects.asm - the objects, the locked doors and the
; portal. Up to two objects lie in a room, drawn as
; metatiles with the room (they never move); a door
; opens with its key and stays open; the portal of the
; start room opens with the three seals. What was taken
; or opened is kept in the variables (taken, doors_open):
; the rooms' data in the cartridge never change. As in
; the C64 and ZX games.

PORTAL          equ 4           ; door 4: the gate
MAX_OBJECTS     equ 2           ; slots of a room
KIND_SEAL       equ 4           ; keys are 1-3
KIND_TREASURE   equ 5
ENERGY_MAX      equ 8           ; segments of the bar
POTION_ENERGY   equ 2
MAX_SEALS       equ 3
HIT_X           equ (BOX_LEFT+BOX_RIGHT)/2  ; the middle
HIT_Y           equ (BOX_TOP+BOX_BOTTOM)/2  ; of the hitbox

; ---- check_door ---------------------------------------
; After the explorer has moved: if a door stopped it and
; it carries the door's key, the key is used up and the
; door opens for the rest of the game. The portal needs
; no key but all the seals (and keeps them).
check_door:
        ld a,(hero_block)
        cp SOLID_DOOR
        ret nz                  ; no door stopped it
        ld a,(door_here)
        or a
        ret z
        ld c,a                  ; C = door 1-4
        call door_bit
        ld b,a                  ; B = its bit
        ld hl,doors_open
        and (hl)
        ret nz                  ; open already
        ld a,c
        cp PORTAL
        jr z,portal_door
        ld a,(key_set)
        and b
        ret z                   ; no key: it stays shut
        ld a,(key_set)
        xor b                   ; the key is used up
        ld (key_set),a
        ld a,1
        ld (hud_dirty),a
        jr door_opens
portal_door:
        ld a,(seals)
        cp MAX_SEALS
        ret nz                  ; not all the seals yet
door_opens:
        ld a,(doors_open)
        or b
        ld (doors_open),a
        jr draw_door            ; on the screen at once

; A = door 1-4 (or key 1-3): A = its bit, 1 2 4 8; B lost
door_bit:
        ld b,a
        ld a,1
db_next:
        dec b
        ret z
        add a,a
        jr db_next

; ---- show_door ----------------------------------------
; If the door of this room is open, its open tiles over
; the closed ones (draw_door).
show_door:
        ld a,(door_here)
        or a
        ret z                   ; no door
        call door_bit
        ld hl,doors_open
        and (hl)
        ret z                   ; still shut
                                ; on into draw_door

; The list of the room's door in door_table: column, row,
; metatile and solid cells of each open tile, then #FF.
draw_door:
        ld a,(door_here)
        dec a
        add a,a                 ; 2 bytes a door
        ld e,a
        ld d,0
        ld hl,door_table
        add hl,de
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
dd_tile:
        ld a,(hl)               ; column, or #FF: the end
        cp #FF
        ret z
        ld c,a
        inc hl
        ld b,(hl)               ; row
        inc hl
        ld a,(hl)               ; metatile
        inc hl
        push hl
        call place_tile         ; DE: in room_names
        pop hl
        ld c,(hl)               ; its solid cells
        inc hl
        push hl
        ld hl,solid_map-room_names
        add hl,de
        call mask_cells
        pop hl
        jr dd_tile

; C: bits 0-3 (top left, top right, bottom left, bottom
; right); HL: the top left cell in solid_map. A cell whose
; bit is 1 becomes solid (1), the posts of the portal.
mask_cells:
        call mask_cell
        inc hl
        call mask_cell
        ld de,31
        add hl,de
        call mask_cell
        inc hl
mask_cell:
        srl c
        ret nc
        ld (hl),1
        ret

; ---- show_objects -------------------------------------
; The objects of the room that are still there, each its
; own metatile: the floor of its place with the object
; drawn over it.
show_objects:
        xor a
        ld (obj_slot),a
so_slot:
        call slot_info
        jr z,so_next            ; nothing there
        inc hl
        ld c,(hl)               ; column
        inc hl
        ld b,(hl)               ; row
        inc hl
        ld a,(hl)               ; metatile
        call place_tile
so_next:
        ld hl,obj_slot
        inc (hl)
        ld a,(hl)
        cp MAX_OBJECTS
        jr nz,so_slot
        ret

; Slot obj_slot of the room: HL = its 4 bytes in the
; room's record (kind, column, row, metatile), DE = its
; byte in taken (room x 2 + slot), A = kind; Z if there
; is nothing there (an empty slot, or an object taken).
slot_info:
        ld a,(room)
        add a,a
        ld hl,obj_slot
        add a,(hl)
        ld e,a
        ld d,0
        ld hl,taken
        add hl,de
        ex de,hl                ; DE: the byte in taken
        ld a,(obj_slot)
        add a,a
        add a,a                 ; 4 bytes a slot
        add a,ROOM_OBJS
        ld l,a
        ld h,0
        ld bc,(room_rec)
        add hl,bc
        ld a,(de)
        or a
        jr nz,si_empty          ; taken
        ld a,(hl)
        or a                    ; kind 0: an empty slot
        ret
si_empty:
        xor a
        ret

; ---- check_objects ------------------------------------
; The explorer picks up an object when the middle of its
; hitbox is in the object's metatile:
; column = (x + HIT_X) / 16,
; row = (y + HIT_Y - ROOM_TOP) / 16.
; The floor takes its place at once.
check_objects:
        ld a,(hero_x)
        add a,HIT_X
        rrca                    ; / 16
        rrca
        rrca
        rrca
        and 15
        ld (hit_col),a
        ld a,(hero_y)
        add a,HIT_Y-ROOM_TOP
        rrca
        rrca
        rrca
        rrca
        and 15
        ld (hit_row),a
        xor a
        ld (obj_slot),a
co_slot:
        call slot_info
        jr z,co_next
        inc hl
        ld a,(hit_col)
        cp (hl)
        jr nz,co_next
        inc hl
        ld a,(hit_row)
        cp (hl)
        jr nz,co_next
        dec hl
        dec hl
        ld a,(hl)               ; the kind
        push de
        call use_object         ; carry: taken
        pop de
        jr nc,co_next
        ld a,1
        ld (de),a               ; taken for the whole game
        ld (hud_dirty),a
        call erase_object
co_next:
        ld hl,obj_slot
        inc (hl)
        ld a,(hl)
        cp MAX_OBJECTS
        jr nz,co_slot
        ret

; A = kind: what the object does. Carry set if it is
; taken, clear if it stays (a potion, the energy full).
use_object:
        cp KIND_SEAL
        jr c,take_key           ; 1-3
        jr z,take_seal
        cp KIND_TREASURE
        jr z,take_treasure
        ld a,(energy)           ; a potion
        cp ENERGY_MAX
        ret nc                  ; full: it stays
        add a,POTION_ENERGY
        cp ENERGY_MAX+1
        jr c,uo_energy
        ld a,ENERGY_MAX
uo_energy:
        ld (energy),a
        scf
        ret
take_key:
        call door_bit           ; keys 1-3: bits 1, 2, 4
        ld hl,key_set
        or (hl)
        ld (hl),a
        scf
        ret
take_seal:
        ld hl,seals
        inc (hl)
        ld de,#1000             ; 1000 points (BCD)
        jr add_score
take_treasure:
        ld de,#0500             ; 500 points (BCD)
                                ; on into add_score

; score += DE, four BCD digits. The score is three bytes
; of two digits, the highest first; DAA turns each sum
; back into two decimal digits. Carry set at the end.
add_score:
        ld hl,score+2
        ld a,(hl)
        add a,e
        daa
        ld (hl),a
        dec hl
        ld a,(hl)
        adc a,d
        daa
        ld (hl),a
        dec hl
        ld a,(hl)
        adc a,0
        daa
        ld (hl),a
        scf
        ret

; The floor of the map where the object of obj_slot lay
erase_object:
        ld a,(obj_slot)
        add a,a
        add a,a                 ; 4 bytes a slot
        add a,ROOM_OBJS+1
        ld l,a
        ld h,0
        ld de,(room_rec)
        add hl,de
        ld c,(hl)               ; column
        inc hl
        ld b,(hl)               ; row
        ld a,b                  ; the map: 16 row + column
        add a,a
        add a,a
        add a,a
        add a,a
        add a,c
        add a,ROOM_MAP
        ld l,a
        ld h,0
        add hl,de
        ld a,(hl)               ; the metatile of the map
                                ; on into place_tile

; ---- the tiles ----------------------------------------
; A = metatile, B = row (0-9), C = column (0-15) of the
; room: put_tile, and on the screen too if the room is
; shown (room_shown). DE ends at its place in room_names.
place_tile:
        call put_tile
        ld a,(room_shown)
        or a
        ret z                   ; built behind the black
        push de
        ld hl,NAMES+2*32-room_names
        add hl,de
        ex de,hl                ; DE: its slots in VRAM
        pop hl                  ; HL: in room_names
        push hl
        push de
        ld b,2
        call vram_copy          ; the top two
        pop hl
        ld de,32
        add hl,de
        ex de,hl                ; DE: VRAM, the row below
        pop hl
        push hl
        ld bc,32
        add hl,bc               ; HL: room_names, below
        ld b,2
        call vram_copy
        pop de
        ret

; A = metatile, B = row, C = column: its four slots into
; room_names and its solid kind into solid_map
; (put_metatile). DE ends at its place in room_names.
put_tile:
        push af
        ld a,b
        inc a
        rrca
        rrca
        and %00111111           ; third = (row + 1) / 4
        add a,a
        add a,a
        ld (row_third),a        ; x 4: in the record
        ld l,b
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl               ; 64 row
        ld a,c
        add a,a
        ld e,a
        ld d,0
        add hl,de               ; + 2 column
        ld de,room_names
        add hl,de
        ex de,hl                ; DE: its place
        pop af
        ld c,a
        jp put_metatile
