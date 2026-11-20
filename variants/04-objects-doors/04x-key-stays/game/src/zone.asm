; zone.asm - a zone's cells into the pattern and colour
; tables of the three thirds, and the list of the slots
; that hold a flame.

; A: the zone (0 atrium, 1-3 the wings A, B, C)
load_zone:
        ld (zone),a
        add a,a
        ld l,a
        ld h,0
        ld de,zone_table
        add hl,de
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a                  ; HL: the zone's record
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld (zone_mt),de         ; its metatiles
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld (zone_so),de         ; their solid cells
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        push de                 ; its flame slots, for later
        ld d,PATTERNS / 256     ; third 0
        call load_third
        ld d,PATTERNS / 256 + 8 ; third 1
        call load_third
        ld d,PATTERNS / 256 + 16
        call load_third         ; third 2
        pop hl
        ld de,flame_list
        ld b,0                  ; flames found
lz_flame:
        ld a,(hl)               ; third, or the end: #FF,
        cp #FE                  ; or #FE and the bands' own
        jr nc,lz_flame_end
        inc hl
        add a,a
        add a,a
        add a,a
        ld c,a                  ; third x 8: #800 a third
        ld a,(hl)               ; the slot
        inc hl
        push hl
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl               ; slot x 8
        ld a,h
        add a,c
        ld h,a                  ; + third x #800
        ex de,hl                ; DE: address, HL: list
        ld (hl),e
        inc hl
        ld (hl),d
        inc hl
        ex de,hl                ; DE: list, HL: address
        pop hl
        ld a,(hl)               ; type: 0 left, 1 right
        inc hl
        ld (de),a
        inc de
        inc b
        jr lz_flame
lz_flame_end:
        ld a,b
        ld (flame_count),a
        xor a
        ld (flame_phase),a      ; the cells hold phase 0
        ret

; HL: a third's cells (the game's count, the count of
; all, patterns, colours: the cells of the bands of the
; title and of the end come last, and only the screens
; use them); D: the high byte of its pattern table. The
; game's cells go to the VRAM; HL ends after them all.
load_third:
        ld a,(hl)               ; the game's cells
        inc hl
        ld e,a
        ld a,(hl)               ; all of them
        inc hl
        sub e
        ld (cells_skip),a       ; the bands' after them
        ld a,e
        or a
        ret z                   ; (never with bands' only)
        ld (cells_left),a
        ld e,0
        push de
        call vram_write_at
        ld c,VDP_DATA
        ld a,(cells_left)
        ld e,a
lt_pattern:
        ld b,8
lt_pattern_row:
        outi                    ; 18 T
        jp nz,lt_pattern_row    ; 11 T
        dec e
        jr nz,lt_pattern
        ld a,(cells_skip)       ; past the bands' patterns
        ld e,a
        ld d,0
        ex de,hl
        add hl,hl
        add hl,hl
        add hl,hl               ; x 8
        add hl,de
        pop de
        ld a,d
        add a,COLOURS / 256     ; the colour table
        ld d,a
        call vram_write_at
        ld a,(cells_left)
        ld e,a
lt_colour:
        ld a,(hl)
        inc hl
        call put_colour
        dec e
        jr nz,lt_colour
        ld a,(cells_skip)       ; past the bands' colours
        add a,l
        ld l,a
        ret nc
        inc h
        ret
