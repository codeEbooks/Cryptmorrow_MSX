; torches.asm - the flames: every eight frames, the next of
; four phases into the pattern of every flame slot. The
; phase is (frames / 8) mod 4; flame_phase is the one drawn
; (a new zone has its flames in phase 0, and a change of
; room takes several frames).

animate_torches:
        ld a,(frames)
        add a,a                 ; frames x 2: every 4
        and %00011000           ; the phase due, x 8
        ld hl,flame_phase
        cp (hl)
        ret z                   ; drawn already
        ld (hl),a
        ld c,a
        ld a,(flame_count)
        or a
        ret z
        ld b,a
        ld hl,flame_list
at_flame:
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        call vram_write_at      ; the slot's pattern
        ld a,(hl)               ; type: 0 left, 1 right
        inc hl
        push hl
        rrca
        rrca
        rrca                    ; x 32: four phases of 8
        add a,c
        ld e,a
        ld d,0
        ld hl,flame_phases
        add hl,de
        push bc
        ld bc,8*256+VDP_DATA
at_row:
        outi                    ; 18 T
        jp nz,at_row            ; 11 T
        pop bc
        pop hl
        djnz at_flame
        ret
