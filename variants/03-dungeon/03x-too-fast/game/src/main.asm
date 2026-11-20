; main.asm - the main loop: a pass a frame. First, in
; the border, what the last pass prepared goes to the
; VRAM: the sprites, the torches; then the pass of the
; game: the HUD and a room after a change go to the
; VRAM first, then the pass works out the next frame.

main_loop:
        halt                    ; wait for the frame
        call put_sprites        ; prepared by the last pass
        call animate_torches
        call play_frame         ; the game's pass
frame_ready:                    ; the tests stop here
        jr main_loop

; ---- play_frame ---------------------------------------
; A pass of the game.
play_frame:
        call hud_update         ; if a value changed
        call reveal_room        ; after a change
        call read_input
        call update_hero
        call check_exits        ; another room?
        jp show_combat          ; the next frame's sprites
