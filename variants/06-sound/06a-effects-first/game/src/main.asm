; main.asm - the main loop: a pass a frame. First, in
; the border, what the last pass prepared goes to the
; VRAM: the sprites, the torches; then the pass of the
; game: the HUD and a room after a change go to the
; VRAM first, then the pass works out the next frame
; (a door that opens, an object taken go to the VRAM
; at once); after the end the room stands still.
; Last the music's next frame, which the interrupt will
; send to the PSG. A change of room takes several
; frames: then the
; interrupt works out the music until the end of the
; pass.

main_loop:
        halt                    ; wait for the frame
        call put_sprites        ; prepared by the last pass
        call animate_torches
        ld hl,turn
        inc (hl)
        call play_frame         ; the game's pass
pass_done:
        xor a                   ; the music is the main
        ld (music_by_isr),a     ; loop's work again
        call music_due          ; the PSG's next frame
frame_ready:                    ; the tests stop here
        jr main_loop

; ---- play_frame ---------------------------------------
; A pass of the game.
play_frame:
        call hud_update         ; if a value changed
        call reveal_room        ; after a change
        ld a,(game_ended)       ; (the tests stop a game by
        or a                    ; putting it in RAM)
        ret nz
        call read_input
        call check_fire         ; a blow may hold it still
        call update_hero
        call check_exits        ; another room, the end?
        ld a,(game_ended)
        or a
        ret nz                  ; out through the portal
        call check_door         ; a door to open?
        call check_objects      ; an object to take?
        call update_enemies
        call check_blade
        call check_contact      ; may end the game
        jp show_combat          ; the next frame's sprites
