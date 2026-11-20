; main.asm - the main loop: a pass a frame. First, in
; the border, what the last pass prepared goes to the
; VRAM: the sprites, the torches; then the pass of the
; game: the next frame worked out.

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
        call read_input
        call update_hero
        jp show_combat          ; the next frame's sprites
