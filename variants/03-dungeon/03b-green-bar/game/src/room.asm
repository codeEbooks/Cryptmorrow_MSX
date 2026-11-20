; room.asm - a room: its zone if new, its 16 x 10
; metatiles as 32 x 20 slots and the map of its solid
; cells (in RAM), the HUD and the name. The slots go to
; the screen with put_names: at start-up, or when a
; change of room is revealed (world.asm).

; A room's record (game/assets/build_msx.py): zone,
; door, two object slots, three enemy slots, map, name
ROOM_MAP        equ 22          ; 160 metatile numbers
; The solid kind of a metatile (the zone's data): 0 free,
; 1 solid, SOLID_DOOR a locked door or the portal's gate,
; solid while it is shut
SOLID_DOOR      equ 2           ; a door's cells, solid_map

; A: the room (0-15, row x 4 + column of the dungeon)
enter_room:
        ld (room),a
        add a,a
        ld l,a
        ld h,0
        ld de,room_table
        add hl,de
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a                  ; HL: the room's record
        ld (room_rec),hl
        ld b,(hl)               ; its zone
        ld a,(zone)
        cp b
        ld a,b
        call nz,load_zone       ; a new zone: its cells
        ld hl,(room_rec)
        ld de,ROOM_MAP
        add hl,de               ; the map
        call build_room         ; HL: then the name
        jp hud_draw

; The map at HL (160 metatiles) into room_names and, #300
; bytes on, solid_map (put_metatile). HL ends after the
; map.
build_room:
        ld de,room_names
        ld c,0                  ; metatile row 0-9
br_row:
        ld a,c
        inc a
        rrca
        rrca
        and %00111111           ; third = (row + 1) / 4
        add a,a
        add a,a
        ld (row_third),a        ; x 4: in the record
        ld b,16                 ; metatiles in a row
br_metatile:
        push bc
        ld c,(hl)               ; the metatile
        inc hl
        call put_metatile
        inc de
        inc de                  ; the next metatile
        pop bc
        djnz br_metatile
        ld a,e
        add a,32                ; past the row below
        ld e,a
        ld a,d
        adc a,0
        ld d,a
        inc c
        ld a,c
        cp 10
        jr nz,br_row
        ret

; C = a metatile, DE = its place in room_names,
; (row_third) = its third x 4. Its four slots (those of
; its third: the record has 4 for each) into room_names;
; its solid kind (0 free, 1 solid, SOLID_DOOR) into its
; four cells of solid_map, #300 bytes on. DE, HL stay.
put_metatile:
        push hl
        ld b,0
        ld hl,(zone_so)
        add hl,bc
        ld a,(hl)               ; its solid kind
        ld hl,solid_map-room_names
        add hl,de               ; its cells in solid_map
        ld (hl),a               ; top left
        inc hl
        ld (hl),a               ; top right
        push de
        ld de,31
        add hl,de               ; the row below
        ld (hl),a               ; bottom left
        inc hl
        ld (hl),a               ; bottom right
        ld l,c
        ld h,b                  ; HL: the metatile (B = 0)
        add hl,hl
        add hl,hl               ; x 4
        ld e,l
        ld d,h
        add hl,hl               ; x 8
        add hl,de               ; x 12: the record
        ld de,(zone_mt)
        add hl,de
        ld a,(row_third)
        ld e,a
        ld d,b
        add hl,de               ; its four slots here
        pop de                  ; in room_names
        push de
        ldi                     ; top left
        ldi                     ; top right
        ld a,e
        add a,30                ; the row below
        ld e,a
        ld a,d
        adc a,0
        ld d,a
        ldi                     ; bottom left
        ldi                     ; bottom right
        pop de
        pop hl
        ret

; room_names to rows 2-21 of the name table
put_names:
        ld de,NAMES+2*32
        call vram_write_at
        ld hl,room_names
        ld c,VDP_DATA
        ld d,20                 ; rows
pn_row:
        ld b,32
pn_byte:
        outi                    ; 18 T
        jp nz,pn_byte           ; 11 T
        dec d
        jr nz,pn_row
        ret
