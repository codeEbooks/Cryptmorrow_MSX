; input.asm - the keyboard and joystick 1, as one byte:
; the bits of the MSX joystick, 1 = held. The arrows and
; SPACE (row 8 of the keyboard) and the stick of port 1
; with its button A count the same, at the same time.

JOY_UP          equ %00000001
JOY_DOWN        equ %00000010
JOY_LEFT        equ %00000100
JOY_RIGHT       equ %00001000
JOY_FIRE        equ %00010000
KEY_ROW         equ 8           ; SPACE, arrows
JOY_PORT1       equ %10001111   ; R15: port 1, pin 8 low

read_input:
        in a,(PPI_ROW)          ; keep bits 4-7
        and %11110000
        or KEY_ROW
        out (PPI_ROW),a
        in a,(PPI_KEYS)         ; 0 = pressed
        cpl
        ld c,a                  ; 1 = pressed
        ld b,0
        bit 5,c                 ; up arrow
        jr z,ri_down
        set 0,b
ri_down:
        bit 6,c                 ; down arrow
        jr z,ri_left
        set 1,b
ri_left:
        bit 4,c                 ; left arrow
        jr z,ri_right
        set 2,b
ri_right:
        bit 7,c                 ; right arrow
        jr z,ri_space
        set 3,b
ri_space:
        bit 0,c                 ; space
        jr z,in_joy
        set 4,b
in_joy:
        ld a,15
        out (PSG_ADDR),a        ; joystick port 1
        ld a,JOY_PORT1
        out (PSG_WRITE),a
        ld a,14
        out (PSG_ADDR),a
        in a,(PSG_READ)         ; 0 = pressed
        cpl
        and %00011111           ; up down left right A
        or b
        ld (input),a
        ret
