; hud.asm - row 0 (ENERGY, the key, the seals, SCORE), the {3}
; two rules (rows 1 and 22) and the room's name (row 23). {3}
;|; hud.asm - the two rules (rows 1 and 22) and the room's {-2}
;|; name (row 23). {-2}

; HL: the room's name, ending with 0
hud_draw:
        push hl
        call hud_row0           ; {3}
;|        ld de,NAMES             ; row 0: blank {-2}
;|        ld a,HUD_BLANK {-2}
;|        ld b,32 {-2}
;|        call vram_fill {-2}
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

;{3}
; Row 0 again if a value changed (hud_dirty)
hud_update:
        ld a,(hud_dirty)
        or a
        ret z
        xor a
        ld (hud_dirty),a
                                ; on into hud_row0

; Row 0: ENERGY and its bar, the keys, the seals, SCORE
hud_row0:
        ld hl,hud_template
        ld de,hud_row
        ld bc,32
        ldir
        call hud_bar
        call hud_counts
        call hud_score
        ld hl,hud_row
        ld de,NAMES             ; row 0
        ld b,32
        jp vram_copy

hud_template:                   ; row 0, before the numbers
        db HUD_E,HUD_N,HUD_E,HUD_R,HUD_G,HUD_Y,HUD_BLANK
        db BAR_EMPTY,BAR_EMPTY,BAR_EMPTY,BAR_EMPTY
        db HUD_BLANK,KEY_ICON,DIGIT_0,HUD_BLANK
        db SEAL_ICON,DIGIT_0,SLASH,DIGIT_0+3,HUD_BLANK
        db HUD_S,HUD_C,HUD_O,HUD_R,HUD_E,HUD_BLANK
        db DIGIT_0,DIGIT_0,DIGIT_0,DIGIT_0,DIGIT_0,DIGIT_0

; columns 7-10: two segments a cell, energy 0-8
hud_bar:
        ld a,(energy)
        ld hl,hud_row+7
        ld b,4
hb_cell:
        cp 2
        jr c,hb_part
        ld (hl),BAR_FULL
        sub 2
        jr hb_next
hb_part:
        ld (hl),BAR_EMPTY
        or a
        jr z,hb_next
        ld (hl),BAR_HALF
        xor a
hb_next:
        inc hl
        djnz hb_cell
        ret

; column 13: the keys (the bits of key_set counted);
; column 16: the seals (of 3)
hud_counts:
        ld a,(key_set)
        ld c,DIGIT_0
hc_key:
        or a
        jr z,hc_keys            ; no more bits
        srl a
        jr nc,hc_key
        inc c                   ; a key
        jr hc_key
hc_keys:
        ld a,c
        ld (hud_row+13),a
        ld a,(seals)
        add a,DIGIT_0
        ld (hud_row+16),a
        ret

; columns 26-31: the six digits of the score
hud_score:
        ld hl,score
        ld de,hud_row+26
        ld b,3
hs_byte:
        ld a,(hl)
        rrca
        rrca
        rrca
        rrca
        and #0F                 ; the high digit
        add a,DIGIT_0
        ld (de),a
        inc de
        ld a,(hl)
        and #0F                 ; the low digit
        add a,DIGIT_0
        ld (de),a
        inc de
        inc hl
        djnz hs_byte
        ret
;{}

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
