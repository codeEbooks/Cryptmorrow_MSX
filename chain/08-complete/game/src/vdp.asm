; vdp.asm - the VDP: Screen 2, and the three ways the game
; writes VRAM. Every loop leaves at least 29 T between two
; bytes, the TMS9918A's pace in the picture. An address or
; a register takes two bytes on VDP_CTRL; reading the
; status (the interrupt does) between them would undo the
; first: DI and EI keep them together.

; ---- the tables in VRAM -------------------------------
PATTERNS        equ #0000       ; 3 x 2 KB, one per third
NAMES           equ #1800       ; 768: 32 x 24 slots
SPRITES         equ #1B00       ; 32 x 4: Y, X, shape, ink
COLOURS         equ #2000       ; 3 x 2 KB, one per third
SHAPES          equ #3800       ; sprite shapes

R1_OFF          equ %10000010   ; 16K, screen off, 16 x 16
R1_ON           equ %11100010   ; 16K, on, interrupt, 16x16
R1_BLANK        equ %10100010   ; the picture off

; ---- start-up: registers, 16 KB of zeros, no sprites --
; The registers with interrupts off (INIT begins with DI).
; From the first address on the Z80 takes interrupts, but
; the VDP sends none until R1_ON.
vdp_init:
        ld hl,vdp_regs
        ld c,#80                ; register 0, write flag
vi_reg:
        ld a,(hl)
        out (VDP_CTRL),a        ; the value first
        ld a,c
        out (VDP_CTRL),a        ; then #80 + register
        inc hl
        inc c
        ld a,c
        cp #88
        jr nz,vi_reg
        ld de,#0000             ; clear the 16 KB
        call vram_write_at
        ld bc,#4000
vi_clear:
        xor a
        out (VDP_DATA),a
        dec bc
        ld a,b
        or c
        jr nz,vi_clear
        ld de,SPRITES           ; sprite 0 at Y = 208:
        ld a,208                ; the list ends there
        ld b,1
        jp vram_fill

vdp_regs:                       ; registers 0-7, Screen 2
        db %00000010            ; R0: Graphics II
        db R1_OFF               ; R1: screen off
        db NAMES / #400         ; R2: #06
        db #FF                  ; R3: colours at #2000
        db #03                  ; R4: patterns at #0000
        db SPRITES / #80        ; R5: #36
        db SHAPES / #800        ; R6: #07
        db #01                  ; R7: border black

; R1 in A, one register write; then interrupts on
vdp_r1:
        di
        out (VDP_CTRL),a
        ld a,#81
        out (VDP_CTRL),a
        ei
        ret

; VRAM write address in DE (bits 0-13); A is lost; then
; interrupts on
vram_write_at:
        di
        ld a,e
        out (VDP_CTRL),a
        ld a,d
        and %00111111
        or %01000000            ; bit 6: write
        out (VDP_CTRL),a
        ei
        ret

; B bytes (0 = 256) from HL to VRAM at DE: 29 T a byte
vram_copy:
        call vram_write_at
        ld c,VDP_DATA
vc_byte:
        outi                    ; 18 T
        jp nz,vc_byte           ; 11 T
        ret

; B bytes (0 = 256) of A to VRAM at DE: 31 T a byte
vram_fill:
        push af
        call vram_write_at
        pop af
vf_byte:
        out (VDP_DATA),a        ; 12 T
        nop                     ; 5 T
        djnz vf_byte            ; 14 T
        ret

; The 8 colour bytes of a cell, at the address already set.
; A: the colour (ink x 16 + paper) of all eight rows or,
; below #10, the number of a gradient: 8 bytes, one a row.
; BC and A are lost.
put_colour:
        cp #10
        jr c,pc_gradient
        ld b,8
pc_row:
        out (VDP_DATA),a        ; 12 T
        nop                     ; 5 T
        djnz pc_row             ; 14 T
        ret
pc_gradient:
        push hl
        add a,a
        add a,a
        add a,a                 ; 8 bytes a gradient
        ld l,a
        ld h,0
        ld bc,gradients
        add hl,bc
        ld bc,8*256+VDP_DATA
pc_gradient_row:
        outi                    ; 18 T
        jp nz,pc_gradient_row   ; 11 T
        pop hl
        ret
