; start.asm - from the BIOS's call to INIT to the first
; frame: the slots, the PSG, the VDP, the sound in its {6}
; first mode (SOUND_MODE, given to the assembler: the {7}
; first line of the menu), the sprite shapes, the {7}
; interrupt; then the opening screen and the title {8}
; (screens.asm). With START_PLAY (the tests' {8}
;|; interrupt; then the title (screens.asm). With {7-7}
;|; START_PLAY (the tests' {7-7}
; cartridges) the game at once, in the room START_ROOM. {7}
;|; frame: the slots, the VDP, the variables, the {-1}
;|; interrupt; then the room START_ROOM (the Moss Gate). {-1}
;|; frame: the slots, the VDP, the variables, the sprite {2-5}
;|; shapes, the interrupt; then the game at once, in the {2-5}
;|; room START_ROOM (the Moss Gate). {2-5}
;|; first mode (SOUND_MODE, given to the assembler), the {6-6}
;|; variables, the sprite shapes, the interrupt; then the {6-6}
;|; game at once, in the room START_ROOM. {6-6}

init:
        di
        ld sp,STACK
        call slot_page2         ; #8000-#BFFF: ours too
        ld a,(MSXID1)           ; 50 or 60 Hz {6}
        ld (msx_id1),a          ; {6}
        call psg_init           ; silent, the music's speed {6}
        call vdp_init           ; Screen 2, screen off, no
                                ; interrupt from the VDP
        ld a,SOUND_MODE         ; MUSIC, SOUND FX or SILENT {6}
        call set_audio          ; {6}
        call vars_init          ; every variable at its {2}
;|        call vars_init          ; every variable {-1}
        xor a                   ; first value, the title too {7}
;|        xor a                   ; first value {2-6}
        ld (input),a            ; {2}
        call load_shapes        ; the sprites' images {2}
        call irq_init
    IF START_PLAY               ; {7}
        call game_init          ; the game at once {2}
;|        call game_init          ; the first room {-1}
        call put_sprites        ; {2}
        ld a,STATE_PLAY         ; {7}
        ld (game_state),a       ; {7}
        in a,(VDP_STAT)         ; clear an old request
        ld a,R1_ON              ; screen on, interrupt on
        call vdp_r1             ; and EI
    ELSE                        ; {7}
        in a,(VDP_STAT)         ; clear an old request {7}
        ld a,R1_BLANK           ; interrupt on, picture off {7}
        call vdp_r1             ; and EI {7}
        call show_opening       ; then the title {8}
;|        call show_title         ; the title {7-7}
    ENDIF                       ; {7}
        jp main_loop

; ---- game_init ----------------------------------------
; A new game: every variable from its first value, the {3}
; fixed slots of the HUD and of the name, the start room {3}
; (its zone loaded again: the screens of the title and of {7}
; the end use the tables), the explorer, its sprites. {7}
;|; and the explorer, its sprites. {3-6}
;|; The first room: every variable from its first value, {-2}
;|; the fixed slots of the HUD and of the name, the start {-2}
;|; room. {-1}
;|; room, the explorer, its sprites. {2-2}
game_init:
        call vars_init
        call load_glyphs        ; HUD and name slots
        ld a,START_ROOM
        call enter_room         ; zone, room, HUD, name {3}
;|        call enter_room         ; zone, room, name {-2}
        call put_names          ; the room's slots
        call hero_init          ; {2}
        jp show_combat          ; the first frame's sprites {2}
;|        ret {-1}

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

; ---- the PSG: silent, port A in, port B out ----------- {6}
; The music's speed by the machine: bit 7 of #002B is 1 {6}
; at 50 Hz (SPEED_50 frames a step), 0 at 60 (SPEED_60). {6}
; SILENT until set_audio; nothing asked; every register {6}
; of the sound to 0 and the mixer off (psg_silence). {6}
psg_init:                       ; {6}
        ld a,(msx_id1)          ; {6}
        rlca                    ; bit 7 to the carry {6}
        ld a,SPEED_50           ; {6}
        jr c,pi_speed           ; {6}
        ld a,SPEED_60           ; {6}
pi_speed:                       ; {6}
        ld (music_speed),a      ; {6}
        ld a,MODE_SILENT        ; {6}
        ld (audio_mode),a       ; {6}
        xor a                   ; {6}
        ld (music_owed),a       ; {6}
        ld (music_by_isr),a     ; {6}
        ld (sfx_next),a         ; {6}
        ld (sfx_pos),a          ; {6}
        ld (sfx_prio),a         ; {6}
        jp psg_silence          ; {6}

; ---- the variables ------------------------------------
vars_init:
        ld hl,0
        ld (frames),hl
        xor a
        ld (vdp_status),a       ; {5}
        ld (key_set),a          ; {3}
        ld (doors_open),a       ; {4}
        ld (game_ended),a       ; {4}
        ld (hud_dirty),a        ; {3}
        ld (room_shown),a       ; {4}
        ld (seals),a            ; {3}
        ld (score),a            ; {3}
        ld (score+1),a          ; {3}
        ld (score+2),a          ; {3}
        ld hl,taken             ; nothing taken {4}
        ld b,TAKEN_SIZE         ; {4}
vi_taken:                       ; {4}
        ld (hl),a               ; {4}
        inc hl                  ; {4}
        djnz vi_taken           ; {4}
        ld (flame_count),a
        ld (reveal_due),a       ; {3}
        ld (turn),a             ; {5}
        ld (slash_timer),a      ; {5}
        ld (blade_dir),a        ; {5}
        ld (fire_held),a        ; {5}
        ld (invulnerable),a     ; {5}
        ld (spr_rot),a          ; {5}
        ld (rooms_seen),a       ; none (put_names marks) {7}
        ld (rooms_seen+1),a     ; {7}
        ld (end_timer),a        ; the states (screens.asm) {7}
        ld (fire_armed),a       ; {7}
        ld (stick_held),a       ; {7}
        dec a                   ; #FF: no zone loaded
        ld (zone),a
        ld a,8                  ; {3}
        ld (energy),a           ; {3}
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
