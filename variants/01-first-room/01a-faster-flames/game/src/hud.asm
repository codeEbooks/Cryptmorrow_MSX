; hud.asm - the two rules (rows 1 and 22) and the room's
; name (row 23).

; HL: the room's name, ending with 0
hud_draw:
        push hl
        ld de,NAMES             ; row 0: blank
        ld a,HUD_BLANK
        ld b,32
        call vram_fill
        ld de,NAMES+32          ; row 1: the rule
        ld a,RULE_TOP
        ld b,32
        call vram_fill
        ld de,NAMES+22*32       ; row 22: the rule
        ld a,RULE_BOTTOM
        ld b,32
        call vram_fill
        pop hl
        jp hud_name

; row 23: the name at HL, centred as on the Spectrum
hud_name:
        push hl
        ld hl,name_row
        ld b,32
hn_blank:
        ld (hl),NAME_BLANK
        inc hl
        djnz hn_blank
        pop hl
        push hl
        ld b,0                  ; its length
hn_length:
        ld a,(hl)
        or a
        jr z,hn_place
        inc hl
        inc b
        jr hn_length
hn_place:
        ld a,b
        inc a
        srl a                   ; (length + 1) / 2
        neg
        add a,16                ; the first column
        ld e,a
        ld d,0
        ld hl,name_row
        add hl,de
        ex de,hl                ; DE: in the row
        pop hl                  ; the name
hn_char:
        ld a,(hl)
        or a
        jr z,hn_put
        inc hl
        cp ' '
        jr nz,hn_letter
        ld a,NAME_BLANK
        jr hn_store
hn_letter:
        add a,LETTER_A-'A'
hn_store:
        ld (de),a
        inc de
        jr hn_char
hn_put:
        ld hl,name_row
        ld de,NAMES+23*32
        ld b,32
        jp vram_copy

; the fixed slots: the HUD's in third 0, the name's in
; third 2 (records: slot, 8 pattern bytes, colour; 0 ends)
load_glyphs:
        ld hl,glyphs_top
        ld b,PATTERNS / 256     ; third 0
        call lg_glyph
        ld hl,glyphs_bottom
        ld b,PATTERNS / 256 + 16
lg_glyph:                       ; third 2
        ld a,(hl)               ; the slot, 0 = the end
        or a
        ret z
        inc hl
        push bc
        ld e,a
        ld d,0
        ex de,hl
        add hl,hl
        add hl,hl
        add hl,hl               ; slot x 8
        ex de,hl
        ld a,d
        add a,b
        ld d,a                  ; in this third
        push de
        ld b,8
        call vram_copy          ; the pattern
        pop de
        ld a,d
        add a,COLOURS / 256
        ld d,a
        call vram_write_at
        ld a,(hl)
        inc hl
        call put_colour         ; and the colour
        pop bc
        jr lg_glyph
