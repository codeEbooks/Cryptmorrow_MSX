; probe.asm - the Phase 0 probe: a 32 KB MSX1 cartridge
; that does what the game will do, and nothing else:
; - the AB header and ENASLT for #8000-#BFFF;
; - Screen 2: one drawing per third, a colour per row;
; - four 16 x 16 sprites, one moved by keys and joystick;
; - IM 2 with the 257-byte table and a frame counter;
; - a note on the PSG, joystick read with the sound on;
; - a stop at frame_ready once a frame, for the tests.
;
; The same source makes the broken versions and the lab
; versions, chosen on the command line:
;   BROKEN = 0  the probe
;            1  the status register is not read
;            2  PSG register 7 with bit 6 at 1
;            3  ENASLT forgotten
;            4  sprite 1 at Y = 208
;            5  five sprites on one line
;            6  VRAM written too fast in the picture
;   IRQMODE = 0 IM 2, our table (the game's way)
;             1 IM 1 and the BIOS hook H.TIMI
; sjasmplus -DBROKEN=0 -DIRQMODE=0 --raw=probe.rom probe.asm
; pasmo --equ BROKEN=0 --equ IRQMODE=0 probe.asm probe.rom

        include "msx.asm"

; ---- RAM in page 3 -------------------------------------
IM2_TAB         equ #F000       ; 257 bytes, all IM2_HI
IM2_HI          equ #F1         ; the table points at #F1F1
IM2_JP          equ #F1F1       ; JP isr
STACK           equ #F380       ; BIOS work area above

; ---- what the probe shows ------------------------------
HERO_X0         equ 120         ; start of sprite 0
HERO_Y0         equ 60
ROW_Y           equ 100         ; sprites 1-3, one line
NOTE_ON         equ 25          ; frame of the note on
NOTE_OFF        equ 75          ; and off (one second)
NOTE_PERIOD     equ 254         ; 1789772.5/16/254 = 440.4
TORCH_ROW       equ 12          ; the animated row

        org #4000

; ---- the cartridge header (16 bytes) -------------------
        db "AB"                 ; a ROM with code
        dw init                 ; INIT: called by the BIOS
        dw 0                    ; STATEMENT: none
        dw 0                    ; DEVICE: none
        dw 0                    ; TEXT: none
        db 0,0,0,0,0,0          ; reserved

; ---- start ---------------------------------------------
init:
        di
        ld sp,STACK
 IF BROKEN = 3
        nop                     ; ENASLT forgotten
 ELSE
        call slot_page2         ; #8000-#BFFF: ours too
 ENDIF
        ld a,(page2_mark)       ; read from page 2
        ld (page2_read),a
        ld a,(MSXID1)           ; 50 or 60 Hz?
        ld (msx_id1),a
        call timing_t1
        call vdp_setup
        call timing_t2
        call timing_t3
        call vars_setup
        call psg_setup
        call irq_setup
        in a,(VDP_STAT)         ; clear an old request
        ld a,#E2                ; R1: 16K, screen on,
        call vdp_r1             ; interrupt on, 16 x 16
        ei
main_loop:
        halt                    ; wait for the frame
        call read_input
        call move_hero
        call put_sprites
        call animate_torch
        call play_note
frame_ready:                    ; the tests stop here
        jr main_loop

; ---- slots: page 2 to the cartridge --------------------
; At INIT only page 1 (#4000-#7FFF) is ours. Our slot is the
; one of page 1; ENASLT puts it in page 2 as well.
slot_page2:
        call RSLREG             ; A = slots of pages 0-3
        rrca
        rrca
        and %00000011           ; slot of page 1
        ld c,a
        ld b,0
        ld hl,EXPTBL            ; is that slot expanded?
        add hl,bc
        ld a,(hl)
        and %10000000
        or c
        ld c,a                  ; C = E000 00PP
        ld hl,SLTTBL            ; its secondary register
        ld a,c
        and %00000011
        ld e,a
        ld d,0
        add hl,de
        ld a,(hl)
        and %00001100           ; secondary slot, page 1
        or c                    ; A = E000 SSPP
        ld (cart_slot),a
        ld h,#80                ; any address in page 2
        jp ENASLT               ; returns to our caller

; ---- timing labs: three pieces of code to count --------
timing_t1:                      ; DJNZ: M1 cycles only
        ld b,0
t1_loop:
        djnz t1_loop
t1_end:
        ret

timing_t2:                      ; 256 bytes to VRAM #3C00
        ld a,#00                ; (sprite shapes 32-39,
        out (VDP_CTRL),a        ; unused); screen off
        ld a,#3C+#40
        out (VDP_CTRL),a
        ld hl,#4000             ; the bytes: our header...
        ld bc,VDP_DATA          ; B = 0: 256 bytes
t2_loop:
        outi                    ; 18 T on the MSX
        jp nz,t2_loop           ; 11 T: 29 T a byte
t2_end:
        ret

timing_t3:                      ; LDIR, 256 bytes of RAM
        ld hl,#4000
        ld de,copy_buf
        ld bc,256
t3_ldir:
        ldir
t3_end:
        ret

; ---- the VDP -------------------------------------------
; Registers first (screen off), then all 16 KB of VRAM to 0,
; then the tables. Interrupts are off: nothing can read the
; status register between two bytes sent to VDP_CTRL.
vdp_setup:
        ld hl,vdp_regs
        ld c,#80                ; register 0, write flag
vdp_reg_loop:
        ld a,(hl)
        out (VDP_CTRL),a        ; the value first
        ld a,c
        out (VDP_CTRL),a        ; then #80 + register
        inc hl
        inc c
        ld a,c
        cp #88
        jr nz,vdp_reg_loop
        ld de,#0000             ; clear the 16 KB
        call vram_write_at
        ld bc,#4000
vdp_clear_loop:
        xor a
        out (VDP_DATA),a
        dec bc
        ld a,b
        or c
        jr nz,vdp_clear_loop
        call put_thirds         ; one drawing per third
        call put_torch_names
        call put_sprite_shape
        ret

; R1 in A, one register write
vdp_r1:
        out (VDP_CTRL),a
        ld a,#81
        out (VDP_CTRL),a
        ret

; VRAM write address in DE (bits 0-13)
vram_write_at:
        ld a,e
        out (VDP_CTRL),a
        ld a,d
        and %00111111
        or %01000000            ; bit 6: write
        out (VDP_CTRL),a
        ret

; pattern 0 and colour 0 of each third, from page 2
put_thirds:
        ld hl,thirds            ; 3 x (8 + 8) bytes
        ld de,#0000             ; pattern 0, third 0
        call put_third
        ld de,#0800
        call put_third
        ld de,#1000
        call put_third
        ret

; 8 pattern bytes at DE, 8 colour bytes at DE + #2000
put_third:
        push de
        call vram_write_at
        ld b,8
put_pat_loop:
        ld a,(hl)
        out (VDP_DATA),a
        inc hl
        djnz put_pat_loop
        pop de
        ld a,d
        add a,#20
        ld d,a
        call vram_write_at
        ld b,8
put_col_loop:
        ld a,(hl)
        out (VDP_DATA),a
        inc hl
        djnz put_col_loop
        ret

; name 1 on the torch row: the animated drawing
put_torch_names:
        ld de,#1800+TORCH_ROW*32+2
        call vram_write_at
        ld b,28
        ld a,1
put_torch_loop:
        out (VDP_DATA),a
        djnz put_torch_loop
        ld de,#2000+#0800+8     ; colours of pattern 1,
        call vram_write_at      ; middle third
        ld hl,torch_colours
        ld b,8
put_torch_col:
        ld a,(hl)
        out (VDP_DATA),a
        inc hl
        djnz put_torch_col
        ret

; sprite pattern 0 (16 x 16, 32 bytes) at #3800
put_sprite_shape:
        ld de,#3800
        call vram_write_at
        ld hl,sprite_ring
        ld b,32
put_shape_loop:
        ld a,(hl)
        out (VDP_DATA),a
        inc hl
        djnz put_shape_loop
        ret

; ---- variables -----------------------------------------
vars_setup:
        ld hl,0
        ld (frames),hl
        xor a
        ld (vdp_status),a
        ld (input),a
        ld (input_prev),a
        ld (torch_phase),a
        ld a,HERO_X0
        ld (hero_x),a
        ld a,HERO_Y0
        ld (hero_y),a
        ld a,15                 ; white
        ld (hero_colour),a
        ret

; ---- the PSG: register 7, joystick port 1 --------------
psg_setup:
        ld a,7
        out (PSG_ADDR),a
 IF BROKEN = 2
        ld a,%11111110          ; bit 6 at 1: port A out
 ELSE
        ld a,%10111110          ; bit 7 out, bit 6 in
 ENDIF
        out (PSG_WRITE),a       ; tone A on, the rest off
        ld a,8
        out (PSG_ADDR),a
        xor a
        out (PSG_WRITE),a       ; channel A silent
        ld a,0
        out (PSG_ADDR),a
        ld a,NOTE_PERIOD & 255
        out (PSG_WRITE),a
        ld a,1
        out (PSG_ADDR),a
        ld a,NOTE_PERIOD / 256
        out (PSG_WRITE),a
        ret

; ---- the frame interrupt -------------------------------
irq_setup:
 IF IRQMODE = 0
        ld hl,IM2_TAB           ; 257 bytes of IM2_HI
        ld de,IM2_TAB+1
        ld bc,256
        ld (hl),IM2_HI
        ldir
        ld a,#C3                ; JP isr at #F1F1
        ld (IM2_JP),a
        ld hl,isr
        ld (IM2_JP+1),hl
        ld a,IM2_TAB / 256
        ld i,a
        im 2
 ELSE
        ld a,#C3                ; JP timi_hook in H.TIMI
        ld (HTIMI),a
        ld hl,timi_hook
        ld (HTIMI+1),hl
        im 1
 ENDIF
        ret

 IF IRQMODE = 0
isr:
        push af
  IF BROKEN = 1
        nop                     ; status not read
  ELSE
        in a,(VDP_STAT)         ; clears the request
  ENDIF
        ld (vdp_status),a
        push hl
        ld hl,(frames)
        inc hl
        ld (frames),hl
        pop hl
        pop af
        ei
        reti
 ELSE
timi_hook:                      ; A = status, from the BIOS
        ld (vdp_status),a
        ld hl,(frames)
        inc hl
        ld (frames),hl
        ret
 ENDIF

; ---- once a frame --------------------------------------
; keyboard row 8 and joystick 1 into one byte, 1 = pressed:
; bit 0 up, 1 down, 2 left, 3 right, 4 fire
read_input:
        ld a,(input)
        ld (input_prev),a
        in a,(PPI_ROW)          ; keep bits 4-7
        and %11110000
        or 8                    ; row 8
        out (PPI_ROW),a
        in a,(PPI_KEYS)         ; 0 = pressed
        ld (keys_raw),a
        cpl
        ld c,a                  ; 1 = pressed
        ld b,0
        bit 5,c                 ; up arrow
        jr z,in_k1
        set 0,b
in_k1:  bit 6,c                 ; down arrow
        jr z,in_k2
        set 1,b
in_k2:  bit 4,c                 ; left arrow
        jr z,in_k3
        set 2,b
in_k3:  bit 7,c                 ; right arrow
        jr z,in_k4
        set 3,b
in_k4:  bit 0,c                 ; space
        jr z,in_joy
        set 4,b
in_joy:
        ld a,15                 ; port 1: bit 6 = 0,
        out (PSG_ADDR),a        ; pins 6-7 high, pin 8 low
        ld a,%10001111
        out (PSG_WRITE),a
        ld a,14
        out (PSG_ADDR),a
        in a,(PSG_READ)         ; 0 = pressed
        ld (joy_raw),a
        cpl
        and %00011111           ; up down left right A
        or b
        ld (input),a
        ret

; one pixel a frame; fire (a new press) changes the colour
move_hero:
        ld a,(input)
        ld c,a
        ld hl,hero_y
        bit 0,c
        jr z,mv_down
        dec (hl)
mv_down:
        bit 1,c
        jr z,mv_left
        inc (hl)
mv_left:
        ld hl,hero_x
        bit 2,c
        jr z,mv_right
        dec (hl)
mv_right:
        bit 3,c
        jr z,mv_fire
        inc (hl)
mv_fire:
        ld a,(input_prev)
        cpl
        and c
        bit 4,a                 ; pressed now, not before
        ret z
        ld a,(hero_colour)
        xor %00000101           ; white <-> light yellow
        ld (hero_colour),a
        ret

; the sprite attribute table: 4 sprites, then Y = 208
put_sprites:
        ld de,#1B00
        call vram_write_at      ; in the border: no rush
        ld a,(hero_y)
        out (VDP_DATA),a
        ld a,(hero_x)
        out (VDP_DATA),a
        xor a                   ; pattern 0
        out (VDP_DATA),a
        ld a,(hero_colour)
        out (VDP_DATA),a
        ld hl,row_sprites       ; sprites 1-3 (and 4)
        ld b,row_end-row_sprites
put_spr_loop:
        ld a,(hl)
        out (VDP_DATA),a
        inc hl
        djnz put_spr_loop
        ld a,208                ; end of the list
        out (VDP_DATA),a
        ret

; every 4 frames, the 8 bytes of pattern 1 (middle third)
; rotate one pixel: every torch on the row moves at once
animate_torch:
        ld a,(frames)
        and 3
        ret nz
        ld a,(torch_phase)
        inc a
        and 7
        ld (torch_phase),a
        ld e,a                  ; HL = torch_shapes
        ld d,0                  ; + 8 * phase
        ld hl,torch_shapes
        add hl,de               ; (16-bit, phase 0-7: *8)
        add hl,de
        add hl,de
        add hl,de
        add hl,de
        add hl,de
        add hl,de
        add hl,de
 IF BROKEN = 6
        ld bc,1200              ; 31 T x 1200: into
torch_wait:                     ; the picture
        dec bc
        ld a,b
        or c
        jr nz,torch_wait
        ld de,#0800+8
        call vram_write_at
        ld c,VDP_DATA
        outi                    ; 18 T apart: too fast
        outi
        outi
        outi
        outi
        outi
        outi
        outi
 ELSE
        ld de,#0800+8
        call vram_write_at
        ld bc,8*256+VDP_DATA
torch_loop:
        outi                    ; 29 T a byte, safe
        jp nz,torch_loop
 ENDIF
        ret

; the note: channel A on from NOTE_ON to NOTE_OFF.
; Register 7 is written every frame, as a player does.
play_note:
        ld a,7
        out (PSG_ADDR),a
 IF BROKEN = 2
        ld a,%11111110
 ELSE
        ld a,%10111110
 ENDIF
        out (PSG_WRITE),a
        ld a,8
        out (PSG_ADDR),a
        ld hl,(frames)
        ld a,h
        or a
        jr nz,note_quiet
        ld a,l
        cp NOTE_ON
        jr c,note_quiet
        cp NOTE_OFF
        jr nc,note_quiet
        ld a,15
        out (PSG_WRITE),a
        ret
note_quiet:
        xor a
        out (PSG_WRITE),a
        ret

; ---- data of page 1 ------------------------------------
vdp_regs:                       ; registers 0-7, Screen 2
        db %00000010            ; R0: Graphics II
        db %10100010            ; R1: 16K, off, 16 x 16
        db #06                  ; R2: names at #1800
        db #FF                  ; R3: colours at #2000
        db #03                  ; R4: patterns at #0000
        db #36                  ; R5: sprites at #1B00
        db #07                  ; R6: shapes at #3800
        db #04                  ; R7: border dark blue

row_sprites:                    ; Y, X, pattern, colour
 IF BROKEN = 4
        db 208,64,0,8           ; Y = 208: the list ends
 ELSE
        db ROW_Y,64,0,8         ; medium red
 ENDIF
        db ROW_Y,104,0,10       ; dark yellow
        db ROW_Y,144,0,12       ; dark green
 IF BROKEN = 5
        db ROW_Y,184,0,13       ; a fifth on the line
        db ROW_Y,224,0,6
 ENDIF
row_end:

torch_colours:                  ; a colour for every row
        db #B1,#B1,#A1,#A1,#81,#81,#61,#61

torch_shapes:                   ; 8 phases of 8 bytes
        db #18,#3C,#7E,#FF,#FF,#7E,#3C,#18
        db #0C,#1E,#3F,#7F,#7F,#3F,#1E,#0C
        db #06,#0F,#1F,#3F,#3F,#1F,#0F,#06
        db #0C,#1E,#3F,#7F,#7F,#3F,#1E,#0C
        db #18,#3C,#7E,#FF,#FF,#7E,#3C,#18
        db #30,#78,#FC,#FE,#FE,#FC,#78,#30
        db #60,#F0,#F8,#FC,#FC,#F8,#F0,#60
        db #30,#78,#FC,#FE,#FE,#FC,#78,#30

; ---- page 2: data the probe reads after ENASLT ---------
        ds #8000-$,#FF

page2_mark:
        db #A5                  ; read at start-up

thirds:                         ; pattern, then colours
        db #FF,#81,#81,#81,#FF,#18,#18,#18      ; bricks
        db #21,#31,#41,#51,#61,#71,#81,#91      ; a colour
        db #AA,#55,#AA,#55,#AA,#55,#AA,#55      ; checker
        db #F2,#F3,#F4,#F5,#F6,#F7,#F8,#F9      ; per row
        db #FF,#FE,#FC,#F8,#F0,#E0,#C0,#80      ; slope
        db #A1,#B1,#C1,#D1,#E1,#F1,#51,#71

sprite_ring:                    ; 16 x 16: left, then right
        db #07,#1F,#38,#60,#60,#C0,#C0,#C0
        db #C0,#C0,#C0,#60,#60,#38,#1F,#07
        db #E0,#F8,#1C,#06,#06,#03,#03,#03
        db #03,#03,#03,#06,#06,#1C,#F8,#E0

        ds #C000-$,#FF          ; 32 768 bytes in all

; ---- RAM variables (page 3) ----------------------------
frames          equ #C000       ; 2: interrupts counted
vdp_status      equ #C002       ; status read by the IRQ
input           equ #C003       ; bit 0-4, 1 = pressed
input_prev      equ #C004
keys_raw        equ #C005       ; row 8 as read
joy_raw         equ #C006       ; PSG register 14 as read
hero_x          equ #C007
hero_y          equ #C008
hero_colour     equ #C009
torch_phase     equ #C00A
cart_slot       equ #C00B       ; our slot, E000SSPP
page2_read      equ #C00C       ; #A5 if ENASLT worked
msx_id1         equ #C00D       ; byte #002B of the BIOS
copy_buf        equ #C100       ; 256: LDIR (timing_t3)
