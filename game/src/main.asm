; main.asm - the main loop: a pass a frame. First, in {2}
;|; main.asm - the main loop: a frame at a time. It waits {1-1}
;|; for the frame, then the torches. {1-1}
; the border, what the last pass prepared goes to the {2}
; VRAM: the sprites, the torches; then the pass of the {2}
; state (screens.asm): the title, the game, the room {7}
; standing still after the end, the end screen. In the {7}
; game the HUD and a room after a change go to the VRAM {7}
; first, then the pass works out the next frame (a door {7}
; that opens, an object taken go to the VRAM at once). {7}
;|; game: the next frame worked out. {2-2}
;|; game: the HUD and a room after a change go to the {3-6}
;|; VRAM first, then the pass works out the next frame. {3-3}
;|; VRAM first, then the pass works out the next frame {4-6}
;|; (a door that opens, an object taken go to the VRAM {4-6}
;|; at once); after the end the room stands still. {4-6}
; Last the music's next frame, which the interrupt will {6}
; send to the PSG. A change of room, a screen of the {7}
; title or of the end take several frames: then the {7}
;|; send to the PSG. A change of room takes several {6-6}
;|; frames: then the {6-6}
; interrupt works out the music until the end of the {6}
; pass. {6}

main_loop:
        halt                    ; wait for the frame
        call put_sprites        ; prepared by the last pass {2}
        call animate_torches
        ld hl,turn              ; {5}
        inc (hl)                ; {5}
        call run_state          ; {7}
;|        call play_frame         ; the game's pass {2-6}
pass_done:                      ; {6}
        xor a                   ; the music is the main {6}
        ld (music_by_isr),a     ; loop's work again {6}
        call music_due          ; the PSG's next frame {6}
frame_ready:                    ; the tests stop here
        jr main_loop

; ---- play_frame --------------------------------------- {2}
; A pass of the game. {2}
play_frame:                     ; {2}
        call hud_update         ; if a value changed {3}
        call reveal_room        ; after a change {3}
        ld a,(game_ended)       ; (the tests stop a game by {4}
        or a                    ; putting it in RAM) {4}
        ret nz                  ; {4}
        call read_input         ; {2}
        call check_fire         ; a blow may hold it still {5}
        call update_hero        ; {2}
        call check_exits        ; another room, the end? {4}
;|        call check_exits        ; another room? {3-3}
        ld a,(game_ended)       ; {4}
        or a                    ; {4}
        ret nz                  ; out through the portal {4}
        call check_door         ; a door to open? {4}
        call check_objects      ; an object to take? {4}
        call update_enemies     ; {5}
        call check_blade        ; {5}
        call check_contact      ; may end the game {5}
        jp show_combat          ; the next frame's sprites {2}
