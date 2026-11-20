; world.asm - the dungeon: a grid of 4 x 4 rooms (room =
; 4 x row + column). The explorer leaves a room through an
; opening and enters the next one from the opposite side,
; at the same place along the wall: the asset builder has
; checked that every opening has one in front of it.
; While the room changes the screen stays on: the room
; goes black, is built, and comes back all at once.

GRID_W          equ 4           ; rooms in a row
ENTRY_MARGIN    equ 8           ; pixels inside the new room
ROOM_BLANK      equ #E0         ; a black slot in each third

; A room is left when the hitbox (the feet) enters the
; outer ring of cells of the room: walls fill that ring
; but in the openings. With the sprite at (x, y):
; north: hitbox top in cell row 2 (lines 16-23),
; south: hitbox bottom in cell row 21 (lines 168-175),
; west:  hitbox left in cell column 0,
; east:  hitbox right in cell column 31.
NORTH_EDGE      equ ROOM_TOP+7-BOX_TOP
SOUTH_EDGE      equ ROOM_TOP+ROOM_LINES-8-BOX_BOTTOM
WEST_EDGE       equ 7-BOX_LEFT
EAST_EDGE       equ 31*8-BOX_RIGHT

; check_exits: after the explorer has moved. At an edge,
; the next room: the explorer goes to the opposite edge,
; ENTRY_MARGIN pixels inside.
check_exits:
        ld a,(hero_y)
        cp NORTH_EDGE+1
        jr c,exit_north         ; y <= NORTH_EDGE
        cp SOUTH_EDGE
        jr nc,exit_south        ; y >= SOUTH_EDGE
        ld a,(hero_x)
        cp WEST_EDGE+1
        jr c,exit_west          ; x <= WEST_EDGE
        cp EAST_EDGE
        ret c                   ; x < EAST_EDGE: still in
        ld a,WEST_EDGE+ENTRY_MARGIN
        ld (hero_x),a           ; east: a room right
        ld a,1
        jr change_room
exit_north:
        ld a,SOUTH_EDGE-ENTRY_MARGIN
        ld (hero_y),a
        ld a,256-GRID_W         ; a row up: -4
        jr change_room
exit_south:
        ld a,NORTH_EDGE+ENTRY_MARGIN
        ld (hero_y),a
        ld a,GRID_W             ; a row down: +4
        jr change_room
exit_west:
        ld a,EAST_EDGE-ENTRY_MARGIN
        ld (hero_x),a
        ld a,255                ; a room left: -1
                                ; on into change_room

; A = step in the grid. Early in the frame: the room
; goes black and the sprites go away, the next room is
; built (its zone, names, solid map, HUD and name:
; several frames, the interrupt keeps coming); the
; pass goes on there. At the top of the next frame the
; main loop shows the sprites, and reveal_room the room.
change_room:
        ld hl,room
        add a,(hl)              ; the next room
        push af
        call hide_room
        pop af
        call enter_room
        ld a,1
        ld (reveal_due),a
room_built:                     ; (the tests time it)
        ret

; No sprites (the list ends at sprite 0), and the 640
; slots of rows 2-21 ROOM_BLANK: 31 T a slot from the top,
; faster than the picture.
hide_room:
        ld de,SPRITES
        ld a,208
        ld b,1
        call vram_fill
        ld de,NAMES+2*32
        call vram_write_at
        ld a,ROOM_BLANK
        ld d,20                 ; rows
hr_row:
        ld b,32
hr_slot:
        out (VDP_DATA),a        ; 12 T
        nop                     ; 5 T
        djnz hr_slot            ; 14 T
        dec d
        jr nz,hr_row
        ret

; At the top of the frame after a change: the new
; room's slots, from the top, faster than the picture.
reveal_room:
        ld a,(reveal_due)
        or a
        ret z
        xor a
        ld (reveal_due),a
        jp put_names
