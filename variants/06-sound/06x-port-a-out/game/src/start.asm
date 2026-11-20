; start.asm - from the BIOS's call to INIT to the first
; frame: the slots, the PSG, the VDP, the sound in its
; first mode (SOUND_MODE, given to the assembler), the
; variables, the sprite shapes, the interrupt; then the
; game at once, in the room START_ROOM.

init:
        di
        ld sp,STACK
        call slot_page2         ; #8000-#BFFF: ours too
        ld a,(MSXID1)           ; 50 or 60 Hz
        ld (msx_id1),a
        call psg_init           ; silent, the music's speed
        call vdp_init           ; Screen 2, screen off, no
                                ; interrupt from the VDP
        ld a,SOUND_MODE         ; MUSIC, SOUND FX or SILENT
        call set_audio
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
; A new game: every variable from its first value, the
; fixed slots of the HUD and of the name, the start room
; and the explorer, its sprites.
game_init:
        call vars_init
        call load_glyphs        ; HUD and name slots
        ld a,START_ROOM
        call enter_room         ; zone, room, HUD, name
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

; ---- the PSG: silent, port A in, port B out -----------
; The music's speed by the machine: bit 7 of #002B is 1
; at 50 Hz (SPEED_50 frames a step), 0 at 60 (SPEED_60).
; SILENT until set_audio; nothing asked; every register
; of the sound to 0 and the mixer off (psg_silence).
psg_init:
        ld a,(msx_id1)
        rlca                    ; bit 7 to the carry
        ld a,SPEED_50
        jr c,pi_speed
        ld a,SPEED_60
pi_speed:
        ld (music_speed),a
        ld a,MODE_SILENT
        ld (audio_mode),a
        xor a
        ld (music_owed),a
        ld (music_by_isr),a
        ld (sfx_next),a
        ld (sfx_pos),a
        ld (sfx_prio),a
        jp psg_silence

; ---- the variables ------------------------------------
vars_init:
        ld hl,0
        ld (frames),hl
        xor a
        ld (vdp_status),a
        ld (key_set),a
        ld (doors_open),a
        ld (game_ended),a
        ld (hud_dirty),a
        ld (room_shown),a
        ld (seals),a
        ld (score),a
        ld (score+1),a
        ld (score+2),a
        ld hl,taken             ; nothing taken
        ld b,TAKEN_SIZE
vi_taken:
        ld (hl),a
        inc hl
        djnz vi_taken
        ld (flame_count),a
        ld (reveal_due),a
        ld (turn),a
        ld (slash_timer),a
        ld (blade_dir),a
        ld (fire_held),a
        ld (invulnerable),a
        ld (spr_rot),a
        dec a                   ; #FF: no zone loaded
        ld (zone),a
        ld a,8
        ld (energy),a
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
