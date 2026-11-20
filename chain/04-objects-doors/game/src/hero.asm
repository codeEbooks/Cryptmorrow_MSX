; hero.asm - the explorer: two hardware sprites of 16 x 16,
; one over the other, a colour each: the skin (sprite 0,
; in front) and the clothes (sprite 1).
; The rules of the C64 and ZX game: the horizontal wins
; over the vertical, left over right, up over down; one
; pixel a frame; a step is refused when the pixel beyond
; the hitbox (the feet) is in a solid cell or outside the
; room; a new walk image every 8 frames while moving, the
; first image standing.

DIR_DOWN        equ 0           ; the order of the images
DIR_UP          equ 1
DIR_LEFT        equ 2
DIR_RIGHT       equ 3
HERO_X0         equ 120         ; under the gate
HERO_Y0         equ 104
HERO_SKIN       equ 9           ; light red: face, hands
HERO_CLOTHES    equ 10          ; dark yellow: hat, coat
CLOTHES_SHAPES  equ 8 * 4       ; after the 8 skins
WALK_RATE       equ 8           ; frames a walk image
BOX_LEFT        equ 3           ; the hitbox in the sprite:
BOX_MID         equ 7           ; columns 3-12, rows 10-15
BOX_RIGHT       equ 12
BOX_TOP         equ 10
BOX_BOTTOM      equ 15
ROOM_TOP        equ 16          ; screen lines of the room
ROOM_LINES      equ 160

; the explorer at the start, facing down, standing
hero_init:
        ld a,HERO_X0
        ld (hero_x),a
        ld a,HERO_Y0
        ld (hero_y),a
        xor a
        ld (hero_dir),a
        ld (hero_frame),a
        ld (hero_timer),a
        ld (hero_moving),a
        ld (hero_block),a
        ld (input),a
        ret

; the sprite shapes: the explorer's 8 images in two
; layers (512 bytes)
load_shapes:
        ld hl,hero_shapes
        ld de,SHAPES
        ld b,0                  ; 256 bytes: the skins
        call vram_copy
        ld de,SHAPES+256
        ld b,0                  ; 256 bytes: the clothes
        jp vram_copy

; one frame of the explorer, from input
update_hero:
        xor a
        ld (hero_moving),a
        ld (hero_block),a
        ld a,(input)
        ld c,a
        and JOY_LEFT | JOY_RIGHT
        jr z,uh_vertical
        ld b,DIR_RIGHT
        bit 2,c                 ; left wins over right
        jr z,uh_turn
        ld b,DIR_LEFT
        jr uh_turn
uh_vertical:
        ld a,c
        and JOY_UP | JOY_DOWN
        jr z,animate_hero       ; nothing: it stands
        ld b,DIR_DOWN
        bit 0,c                 ; up wins over down
        jr z,uh_turn
        ld b,DIR_UP
uh_turn:
        ld a,b
        ld (hero_dir),a
        call hero_blocked       ; A = 1: a solid cell
        ld (hero_block),a
        or a
        jr nz,animate_hero
        ld a,(hero_dir)
        ld hl,hero_x
        cp DIR_LEFT
        jr nz,uh_right
        dec (hl)
        jr uh_moved
uh_right:
        cp DIR_RIGHT
        jr nz,uh_up
        inc (hl)
        jr uh_moved
uh_up:
        ld hl,hero_y
        cp DIR_UP
        jr nz,uh_down
        dec (hl)
        jr uh_moved
uh_down:
        inc (hl)
uh_moved:
        ld a,1
        ld (hero_moving),a
animate_hero:                   ; the walk
        ld a,(hero_moving)
        or a
        jr z,ah_stand
        ld hl,hero_timer
        inc (hl)
        ld a,(hl)
        cp WALK_RATE
        ret nz
        ld (hl),0
        ld a,(hero_frame)
        xor 1                   ; the other foot
        ld (hero_frame),a
        ret
ah_stand:
        xor a
        ld (hero_frame),a
        ld (hero_timer),a
        ret

; A = 1 (NZ) if the pixel one step ahead of the hitbox, in
; hero_dir, is solid or out of the room; 0 (Z) if free
hero_blocked:
        ld a,(hero_x)
        ld d,a
        ld a,(hero_y)
        ld e,a
        ld a,(hero_dir)
        cp DIR_LEFT
        jr z,hb_left
        cp DIR_RIGHT
        jr z,hb_right
        cp DIR_UP
        jr z,hb_up
        ld a,e                  ; down: under the feet
        add a,BOX_BOTTOM+1
        jr hb_across
hb_up:
        ld a,e                  ; up: over the feet
        add a,BOX_TOP-1
hb_across:
        ld e,a                  ; three points on that line
        ld a,d
        add a,BOX_LEFT
        ld d,a
        call is_solid
        ret nz
        ld a,d
        add a,BOX_MID-BOX_LEFT
        ld d,a
        call is_solid
        ret nz
        ld a,d
        add a,BOX_RIGHT-BOX_MID
        ld d,a
        jr is_solid
hb_left:
        ld a,d
        add a,BOX_LEFT-1
        jr hb_along
hb_right:
        ld a,d
        add a,BOX_RIGHT+1
        jr c,is_out             ; past column 255
hb_along:
        ld d,a                  ; two points in that column
        ld a,e
        add a,BOX_TOP
        ld e,a
        call is_solid
        ret nz
        ld a,e
        add a,BOX_BOTTOM-BOX_TOP
        ld e,a
                                ; and on into is_solid

; D = x, E = y (screen pixels): A = 1 (NZ) if that pixel is
; in a solid cell or out of the room, 0 (Z) if free. DE
; stays.
is_solid:
        ld a,e
        sub ROOM_TOP
        jr c,is_out             ; above the room
        cp ROOM_LINES
        jr nc,is_out            ; below it
        and %11111000           ; the cell row x 8
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl               ; x 32: the row's first cell
        ld a,d
        rrca
        rrca
        rrca
        and %00011111           ; the cell column
        or l
        ld l,a
        ld a,h
        add a,solid_map / 256
        ld h,a
        ld a,(hl)
        or a
        ret
is_out:
        ld a,1
        or a
        ret

; the explorer's two sprites in hero_sat, for the next
; frame (put_sprites): Y (a line higher: the VDP shows it
; one lower), X, the image of each layer, its colour
hero_sprites:
        ld a,(hero_y)
        dec a
        ld (hero_sat),a
        ld (hero_sat+4),a
        ld a,(hero_x)
        ld (hero_sat+1),a
        ld (hero_sat+5),a
        ld a,(hero_dir)
        add a,a
        ld b,a
        ld a,(hero_frame)
        add a,b                 ; direction x 2 + step
        add a,a
        add a,a                 ; x 4: the shape number
        ld (hero_sat+2),a       ; the skin
        add a,CLOTHES_SHAPES
        ld (hero_sat+6),a       ; the clothes
        ld a,HERO_SKIN
        ld (hero_sat+3),a
        ld a,HERO_CLOTHES
        ld (hero_sat+7),a
        ret
