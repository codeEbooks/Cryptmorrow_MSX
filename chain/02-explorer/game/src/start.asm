; start.asm - from the BIOS's call to INIT to the first
; frame: the slots, the VDP, the variables, the sprite
; shapes, the interrupt; then the game at once, in the
; room START_ROOM (the Moss Gate).

init:
        di
        ld sp,STACK
        call slot_page2         ; #8000-#BFFF: ours too
        call vdp_init           ; Screen 2, screen off, no
                                ; interrupt from the VDP
        call vars_init          ; every variable at its
        xor a                   ; first value
        ld (input),a
        call load_shapes        ; the sprites' images
        call irq_init
        call game_init          ; the game at once
        call put_sprites
        in a,(VDP_STAT)         ; clear an old request
        ld a,R1_ON              ; screen on, interrupt on
        call vdp_r1             ; and EI
        jp main_loop

; ---- game_init ----------------------------------------
; The first room: every variable from its first value,
; the fixed slots of the HUD and of the name, the start
; room, the explorer, its sprites.
game_init:
        call vars_init
        call load_glyphs        ; HUD and name slots
        ld a,START_ROOM
        call enter_room         ; zone, room, name
        call put_names          ; the room's slots
        call hero_init
        jp show_combat          ; the first frame's sprites

; ---- slots: page 2 to the cartridge -------------------
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

; ---- the variables ------------------------------------
vars_init:
        ld hl,0
        ld (frames),hl
        xor a
        ld (flame_count),a
        dec a                   ; #FF: no zone loaded
        ld (zone),a
        ret

; ---- the frame interrupt: IM 2 and the table ----------
irq_init:
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
        ret
