; screens.asm - the states of the program, as in the C64
; game and in the ZX one: the title with the menu of the
; sound, the game, the end of a game in the room, the
; end screen; then the title again and a new game.
; The title and the end screens are bitmaps. While one is
; drawn the picture is off (R1_BLANK: the VDP shows only
; the black border) and the name table holds the slots
; 0-255 in each third, once: the cell at row r, column c
; has its own pattern, at r x 256 + c x 8, and its own
; colours, #2000 further on. Then the picture comes on.

STATE_TITLE     equ 0           ; game_state: what the
STATE_PLAY      equ 1           ; main loop runs
STATE_ENDING    equ 2           ; the room stands still
STATE_END       equ 3           ; the end screen
ENDING_FRAMES   equ 50          ; passes in the room
END_DELAY       equ 50          ; passes before FIRE
MENU_ROW        equ 15          ; MUSIC, SOUND FX, SILENT
MENU_COLUMN     equ 11
PROMPT_ROW      equ 21          ; PRESS FIRE
PROMPT_COLUMN   equ 11
PROMPT_LEN      equ 10
PULSE_BIT       equ 16          ; PRESS FIRE: 16 passes
                                ; bright, 16 not
CREDIT_ROW      equ 23
CREDIT_COLUMN   equ 6
STATS_ROW       equ 15          ; SCORE, SEALS, ROOMS
STATS_COLUMN    equ 10
VALUE_COLUMN    equ 16
TITLE_Y         equ 80          ; the sprites of the title:
HERO_TX         equ 120         ; the explorer before the
SKEL_TX         equ 52          ; gate, a skeleton stepping
BAT_TX          equ 184         ; on the spot, a bat that
BAT_TY          equ 78          ; flutters up and down
BIG_STRIDE      equ 34          ; big_in: a byte each side

; ---- run_state ----------------------------------------
; Jumps to the pass of game_state, which returns to the
; main loop: the game's at once (its passes have the
; least time to spare), the others from a table.
run_state:
        ld a,(game_state)
        cp STATE_PLAY
        jp z,play_frame
        add a,a                 ; two bytes an address
        ld e,a
        ld d,0
        ld hl,state_code
        add hl,de
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        jp (hl)

state_code:
        dw title_frame,play_frame,ending_frame,end_frame

; ---- show_title ---------------------------------------
; The title: the logo with its moss, the band of the Moss
; Gate, the menu of the sound, PRESS FIRE, the credit;
; the explorer, a skeleton and a bat. The sound starts
; again in the chosen mode (the theme from its start).
show_title:
        ld a,(audio_mode)       ; first the sound
        call set_audio
        call bitmap_screen
        xor a                   ; STATE_TITLE
        ld (game_state),a
        ld (fire_armed),a
        ld a,(input)            ; what is held already does
        and JOY_UP+JOY_DOWN     ; not move the cursor
        ld (stick_held),a
        ld hl,band_title
        call draw_band
        ld hl,word_logo
        call print_big
        call show_menu
        ld bc,PROMPT_ROW*256+PROMPT_COLUMN
        ld hl,txt_prompt
        ld a,TEXT_HUD
        call print_text
        ld bc,CREDIT_ROW*256+CREDIT_COLUMN
        ld hl,txt_credit
        ld a,TEXT_NUM
        call print_text
        ld a,TEXT_HUD           ; as drawn
        ld (prompt_colour),a
        call screen_show
                                ; on to title_sprites

; ---- title_sprites, animate_title ---------------------
; The explorer facing down; a skeleton and a bat (a new
; image every 8 and every 4 passes, the bat a pixel up or
; down every 4): the sprites of the next frame.
title_sprites:
        ld a,HERO_TX
        ld (hero_x),a
        ld a,TITLE_Y
        ld (hero_y),a
        xor a                   ; DIR_DOWN, standing
        ld (hero_dir),a
        ld (hero_frame),a
        call hero_sprites
        ld a,1
        ld (hero_shown),a
animate_title:
        ld hl,spr_list
        ld a,(turn)             ; the skeleton: pass / 8
        rrca
        rrca
        rrca
        and 1
        add a,IMG_SKELETON
        ld bc,TITLE_Y*256+SKEL_TX
        call list_sprite
        ld a,(turn)             ; the bat: pass / 4
        rrca
        rrca
        push af
        and 7
        ld e,a
        ld d,0
        push hl
        ld hl,bat_bob
        add hl,de
        ld a,(hl)
        add a,BAT_TY
        ld b,a                  ; its y
        pop hl
        pop af
        and 1
        add a,IMG_BAT
        ld c,BAT_TX
        call list_sprite
        ld a,2
        ld (spr_count),a
                                ; on to pulse_prompt

; pulse_prompt: PRESS FIRE bright for 16 passes, then
; not for 16 (its ten colours, when they change).
pulse_prompt:
        ld a,(turn)
        and PULSE_BIT
        ld a,TEXT_HUD
        jr z,pp_colour
        ld a,TEXT_NUM
pp_colour:
        ld hl,prompt_colour
        cp (hl)
        ret z                   ; shown already
        ld (hl),a
        ld de,COLOURS+PROMPT_ROW*256+PROMPT_COLUMN*8
        ld b,PROMPT_LEN*8
        jp vram_fill

; ---- title_frame --------------------------------------
; Up and down choose the sound; FIRE, pressed and let
; go, starts a game.
title_frame:
        call read_input
        call move_cursor
        call animate_title
        call fire_released
        ret nc
                                ; on to start_game

; ---- start_game ---------------------------------------
; A new game in the chosen mode of the sound (the theme
; from its start): every variable from its first value,
; the start room, the explorer.
start_game:
        call screen_blank
        ld a,(audio_mode)
        call set_audio
        call game_init
        ld a,STATE_PLAY
        ld (game_state),a
        ld a,R1_ON              ; the picture on
        jp vdp_r1

; ---- move_cursor --------------------------------------
; A line up or down each time the stick leaves the
; centre (up wins over down). The mode changes at once,
; so that it can be heard: SOUND FX plays an effect.
move_cursor:
        ld a,(input)
        and JOY_UP+JOY_DOWN
        ld hl,stick_held
        cp (hl)
        ld (hl),a
        ret z                   ; no change
        or a
        ret z                   ; back to the centre
        and JOY_UP
        ld a,(audio_mode)
        jr z,mc_down
        or a                    ; MODE_MUSIC: the first
        ret z
        dec a
        jr mc_moved
mc_down:
        cp MODE_SILENT
        ret z                   ; on the last line
        inc a
mc_moved:
        call set_audio
        call show_menu
        ld a,(audio_mode)
        cp MODE_FX
        ret nz
        ld a,SFX_PICKUP         ; a sample of the effects
        jp sound_effect

; ---- show_menu ----------------------------------------
; The three lines: the chosen one yellow with the cursor,
; the others white.
show_menu:
        xor a                   ; the mode of the line
sm_line:
        ld (menu_mode),a
        ld hl,audio_mode
        cp (hl)
        ld hl,txt_off           ; two blanks
        ld a,TEXT_MENU
        jr nz,sm_paint
        ld hl,txt_on            ; the cursor and a blank
        ld a,TEXT_MENU_ON
sm_paint:
        ld (menu_colour),a
        ld a,(menu_mode)
        add a,MENU_ROW
        ld b,a
        ld c,MENU_COLUMN
        ld a,(menu_colour)
        call print_text         ; C moves on: the name
        ld a,(menu_mode)
        add a,a
        ld e,a
        ld d,0
        ld hl,mode_names
        add hl,de
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a
        ld a,(menu_colour)
        call print_text
        ld a,(menu_mode)
        inc a
        cp MODE_SILENT+1
        jr nz,sm_line
        ret

; ---- fire_released ------------------------------------
; Carry set when FIRE is let go after a press seen in
; this state (fire_armed): pressed and let go, as on the
; C64.
fire_released:
        ld a,(input)
        and JOY_FIRE
        ld hl,fire_held
        cp (hl)
        ld (hl),a
        jr z,fr_not             ; no change
        or a
        jr nz,fr_pressed
        ld a,(fire_armed)       ; let go: after a press?
        or a
        jr z,fr_not
        scf
        ret
fr_pressed:
        ld a,1
        ld (fire_armed),a
fr_not:
        or a                    ; carry clear
        ret

; ---- end_game -----------------------------------------
; A = ENDED_LOST or ENDED_WON (from game_over, victory,
; after the VRAM): the room stands still ENDING_FRAMES
; passes, while the end plays.
end_game:
        ld b,a
        ld a,STATE_ENDING
        ld (game_state),a
        ld a,ENDING_FRAMES
        ld (end_timer),a
        ld a,b
        jp end_sound

; ---- ending_frame -------------------------------------
; The room still: the HUD of the last pass (and the room,
; if the game ended in a change of room); then the end
; screen.
ending_frame:
        call hud_update
        call reveal_room
        ld hl,end_timer
        dec (hl)
        ret nz
                                ; on to show_end

; ---- show_end -----------------------------------------
; The end screen: VICTORY and the open gate, or GAME OVER
; and the shut gate among the bones; the score, the
; seals, the rooms explored. PRESS FIRE comes after
; END_DELAY passes. The end goes on playing.
show_end:
        call bitmap_screen
        ld a,STATE_END
        ld (game_state),a
        ld a,END_DELAY
        ld (end_timer),a
        xor a
        ld (fire_armed),a
        ld a,(game_ended)
        cp ENDED_WON
        jr z,se_won
        ld hl,band_lost
        call draw_band
        ld hl,word_lost
        jr se_word
se_won:
        ld hl,band_won
        call draw_band
        ld hl,word_won
se_word:
        call print_big
        call print_stats
        jp screen_show

; ---- end_frame ----------------------------------------
; FIRE is followed but does not count for END_DELAY
; passes; then PRESS FIRE appears and glows, and FIRE,
; pressed and let go, leads back to the title.
end_frame:
        call read_input
        ld a,(end_timer)
        or a
        jr z,ef_ready
        call fire_released      ; only to follow the button
        xor a
        ld (fire_armed),a       ; presses do not count yet
        ld hl,end_timer
        dec (hl)
        ret nz
        ld a,TEXT_HUD           ; PRESS FIRE appears
        ld (prompt_colour),a
        ld bc,PROMPT_ROW*256+PROMPT_COLUMN
        ld hl,txt_prompt
        jp print_text
ef_ready:
        call pulse_prompt
        call fire_released
        ret nc
        jp show_title

; ---- print_stats --------------------------------------
; SCORE, SEALS and ROOMS with their values: six digits,
; a digit of 3, two digits of 16.
print_stats:
        ld bc,STATS_ROW*256+STATS_COLUMN
        ld hl,txt_score
        ld a,TEXT_NUM
        call print_text
        ld bc,256*(STATS_ROW+1)+STATS_COLUMN
        ld hl,txt_seals
        ld a,TEXT_NUM
        call print_text
        ld bc,256*(STATS_ROW+2)+STATS_COLUMN
        ld hl,txt_rooms
        ld a,TEXT_NUM
        call print_text
        ld hl,stat_text         ; the score
        ld de,score
        ld b,3
ps_score:
        ld a,(de)
        call bcd_chars
        inc de
        djnz ps_score
        ld (hl),0
        ld bc,STATS_ROW*256+VALUE_COLUMN
        call stat_print
        ld hl,stat_text         ; the seals
        ld a,(seals)
        add a,'0'
        ld (hl),a
        inc hl
        ld (hl),'/'
        inc hl
        ld (hl),'3'
        inc hl
        ld (hl),0
        ld bc,256*(STATS_ROW+1)+VALUE_COLUMN
        call stat_print
        ld hl,(rooms_seen)      ; the rooms: the bits set
        ld bc,16*256+0          ; B: 16 bits, C: the count
ps_bit:
        add hl,hl               ; the top bit to the carry
        jr nc,ps_next
        inc c
ps_next:
        djnz ps_bit
        ld a,c
        cp 10
        jr c,ps_bcd
        add a,6                 ; 10-16 as BCD: #10-#16
ps_bcd:
        ld hl,stat_text
        call bcd_chars
        ld de,txt_of_16
ps_copy:
        ld a,(de)               ; "/16" and the 0
        ld (hl),a
        inc hl
        inc de
        or a
        jr nz,ps_copy
        ld bc,256*(STATS_ROW+2)+VALUE_COLUMN
stat_print:
        ld hl,stat_text
        ld a,TEXT_HUD
        jp print_text

; bcd_chars: A = two BCD digits, written as characters
; at HL; HL moves on by 2. B and DE stay.
bcd_chars:
        push af
        rrca
        rrca
        rrca
        rrca
        and #0F
        add a,'0'
        ld (hl),a
        inc hl
        pop af
        and #0F
        add a,'0'
        ld (hl),a
        inc hl
        ret

; ---- the picture off, a bitmap, the picture on --------
; screen_blank: the music's next frame now, then the
; interrupt's work until the end of the pass (drawing
; takes several frames); the picture off; no sprite and
; no flame.
screen_blank:
        call music_due
        ld a,1
        ld (music_by_isr),a
        ld a,R1_BLANK
        call vdp_r1
        xor a
        ld (flame_count),a
        ld (hero_shown),a
        ld (spr_count),a
        ld de,SPRITES           ; the list ends at sprite 0
        ld a,208
        ld b,1
        jp vram_fill

; bitmap_screen: the picture off; every slot named once,
; its pattern and colours 0 (the black border shows
; through).
bitmap_screen:
        call screen_blank
        ld de,NAMES
        call vram_write_at
        ld c,3                  ; the thirds
bs_third:
        xor a
bs_name:
        out (VDP_DATA),a        ; 12 T: slots 0-255
        inc a                   ; 5 T
        nop                     ; 5 T
        jr nz,bs_name           ; 13 T
        dec c
        jr nz,bs_third
        ld de,PATTERNS
        call vram_clear
        ld de,COLOURS
                                ; on to vram_clear

; 24 x 256 bytes of 0 from DE on (a table of the three
; thirds): 31 T a byte.
vram_clear:
        call vram_write_at
        xor a
        ld c,24
vcl_page:
        ld b,0
vcl_byte:
        out (VDP_DATA),a        ; 12 T
        nop                     ; 5 T
        djnz vcl_byte           ; 14 T
        dec c
        jr nz,vcl_page
        ret

; screen_show: the flames drawn are in phase 0; the
; picture on.
screen_show:
        xor a
        ld (flame_phase),a
        ld a,R1_ON
        jp vdp_r1

; ---- put_cell, print_text -----------------------------
; B = row, C = column of a bitmap screen, HL = 8 pattern
; bytes, A = colour (put_colour): the cell. HL moves on
; by 8; BC stays.
put_cell:
        push af
        ld d,b                  ; row x 256
        ld a,c
        add a,a
        add a,a
        add a,a
        ld e,a                  ; + column x 8
        push de
        call vram_write_at
        push bc
        ld bc,8*256+VDP_DATA
pce_row:
        outi                    ; 18 T
        jp nz,pce_row           ; 11 T
        pop bc
        pop de
        ld a,d
        add a,COLOURS/256
        ld d,a
        call vram_write_at
        pop af
        push bc
        call put_colour
        pop bc
        ret

; B = row, C = column, A = colour, HL = a text (the
; characters of text_chars, ending with 0). C moves on
; past it; HL after its 0.
print_text:
        ld (text_colour),a
pt_char:
        ld a,(hl)
        inc hl
        or a
        ret z
        push hl
        push bc
        ld hl,text_chars
        ld bc,TEXT_COUNT
        cpir                    ; HL: after the character
        ld de,text_chars+1
        or a
        sbc hl,de               ; its number
        add hl,hl
        add hl,hl
        add hl,hl               ; x 8
        ld de,text_font
        add hl,de
        pop bc
        ld a,(text_colour)
        call put_cell
        pop hl
        inc c
        jr pt_char

; ---- draw_band ----------------------------------------
; HL = a band (band_title, band_won, band_lost): its
; zone, then 4 rows of 16 metatiles, drawn from BAND_ROW
; with the cells of the zone (build_msx.py cut the bands
; as rows 2-5 of a room: their top row has slots in
; third 0, the others in third 1). A cell of a flame
; joins flame_list at its place here.
draw_band:
        ld a,(hl)               ; the zone
        inc hl
        push hl
        add a,a
        ld l,a
        ld h,0
        ld de,zone_table
        add hl,de
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a                  ; HL: the zone's record
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld (zone_mt),de         ; its metatiles
        inc hl                  ; (the solid kinds)
        inc hl
        ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld (band_flames),de     ; its flame slots
        ld (band_cells),hl      ; third 0: counts, cells
        call cells_after        ; HL: third 1
        ld (band_cells+2),hl
        pop hl                  ; the metatiles
        ld b,BAND_ROW
db_row:
        ld a,b
        cp BAND_ROW+2           ; 0: third 0, else third 1
        ld a,0
        jr c,db_third
        inc a
db_third:
        ld (band_third),a
        ld c,0                  ; the column
db_metatile:
        push hl
        push bc
        ld l,(hl)               ; the metatile
        ld h,0
        add hl,hl
        add hl,hl               ; x 4
        ld e,l
        ld d,h
        add hl,hl               ; x 8
        add hl,de               ; x 12: its record
        ld de,(zone_mt)
        add hl,de
        ld a,(band_third)
        add a,a
        add a,a                 ; its 4 slots there
        ld e,a
        ld d,0
        add hl,de
        call band_cell          ; top left
        inc c
        call band_cell          ; top right
        inc b
        dec c
        call band_cell          ; bottom left
        inc c
        call band_cell          ; bottom right
        pop bc
        pop hl
        inc hl                  ; the next metatile
        inc c
        inc c
        ld a,c
        cp 32
        jr nz,db_metatile
        inc b
        inc b
        ld a,b
        cp BAND_ROW+2*BAND_H
        jr nz,db_row
        ret

; HL = a third's cells (the game's count, the count of
; all): HL after them all (8 pattern bytes and a colour
; each). DE is lost.
cells_after:
        inc hl                  ; past the game's count
        ld e,(hl)               ; all of them
        ld d,0
        inc hl
        add hl,de               ; the colours
        ex de,hl
        add hl,hl
        add hl,hl
        add hl,hl               ; the patterns
        add hl,de
        ret

; HL: a slot of the zone (in a metatile's record, for
; band_third), B = row, C = column: that cell there. HL
; moves on; BC stays.
band_cell:
        ld a,(hl)               ; the slot
        inc hl
        push hl
        push bc
        ld (band_slot),a
        ld a,(band_third)
        add a,a
        ld e,a
        ld d,0
        ld hl,band_cells
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)               ; DE: the third's counts
        inc de                  ; (the game's)
        ld a,(de)               ; all its cells
        inc de                  ; DE: its patterns
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl               ; count x 8
        add hl,de               ; HL: its colours
        ld a,(band_slot)
        ld c,a
        ld b,0
        add hl,bc
        ld a,(hl)
        ld (band_colour),a      ; the slot's colour
        ld l,c
        ld h,b
        add hl,hl
        add hl,hl
        add hl,hl               ; slot x 8
        add hl,de               ; its pattern
        pop bc
        ld a,(band_colour)
        call put_cell
        call band_flame
        pop hl
        ret

; B = row, C = column of the cell just drawn, from slot
; band_slot of band_third: if the zone has a flame there,
; this place joins flame_list (VRAM address, type). BC
; stays.
band_flame:
        ld hl,(band_flames)
bf_next:
        ld a,(hl)               ; third, or #FF: the end
        cp #FF
        ret z
        inc hl
        cp #FE                  ; then the bands' own
        jr z,bf_next
        ld e,a
        ld a,(band_third)
        cp e
        ld a,(hl)               ; the slot
        inc hl
        ld d,(hl)               ; the type
        inc hl
        jr nz,bf_next
        ld e,a
        ld a,(band_slot)
        cp e
        jr nz,bf_next
        ld a,(flame_count)      ; a flame: its place
        ld e,a
        add a,a
        add a,e                 ; 3 bytes each
        ld e,a
        push de
        ld d,0
        ld hl,flame_list
        add hl,de
        ld a,c
        add a,a
        add a,a
        add a,a
        ld (hl),a               ; column x 8
        inc hl
        ld (hl),b               ; + row x 256
        inc hl
        pop de
        ld (hl),d               ; its type
        ld hl,flame_count
        inc (hl)
        ret

; ---- print_big ----------------------------------------
; HL = a big word (word_logo, word_won, word_lost): its
; first pixel column, its character row, the colours of
; its rows 1-2, of row 3, of the moss row under them
; (NO_MOSS: none), the letters. Each letter of the logo
; font is 12 rows of 10 squares of 2 x 2 pixels, 22
; pixels from the next. First the squares go to big_in
; (24 rows of the word, a blank byte on each side and a
; blank row above and below); then each pixel of a
; square is lit on the edges at the top and on the left,
; in shadow on those at the bottom and on the right; the
; joints of the courses are its rows 7 and 15 (dark) and
; 6 and 14 (half lit), as art.py draws the logo. The
; result goes to big_out, the drips of moss under it,
; and then cell by cell to the screen.
print_big:
        ld a,(hl)
        ld (big_x),a
        inc hl
        ld a,(hl)
        ld (big_row),a
        inc hl
        ld de,big_colours       ; three colours
        ld bc,3
        ldir
        push hl
        ld hl,big_in            ; both buffers clear
        ld de,big_in+1
        ld bc,BIG_IN_SIZE+BIG_OUT_SIZE-1
        ld (hl),0
        ldir
        pop hl
pb_letter:
        ld a,(hl)
        inc hl
        or a
        jr z,pb_squares
        push hl
        cp ' '
        call nz,big_letter
        pop hl
        ld a,(big_x)            ; the next letter
        add a,22
        ld (big_x),a
        jr pb_letter
pb_squares:
        call big_edges
        ld a,(big_colours+2)
        cp NO_MOSS
        call nz,big_drips
        jp big_cells

; A = a letter of big_letters: its 12 rows, each doubled
; (rows 2y and 2y+1 of big_in), from pixel big_x.
big_letter:
        ld hl,big_letters
        ld bc,BIG_COUNT
        cpir
        ld de,big_letters+1
        or a
        sbc hl,de               ; its number
        ld e,l
        ld d,h
        add hl,hl
        add hl,hl
        add hl,hl               ; x 8
        add hl,de               ; x 9
        add hl,hl
        add hl,hl               ; x 36: 12 rows of 3
        ld de,big_font
        add hl,de
        ld (big_src),hl
        ld a,(big_x)
        rrca
        rrca
        rrca
        and 31                  ; its first byte
        ld e,a
        ld d,0
        ld hl,big_in+BIG_STRIDE+1
        add hl,de
        ld (big_dst),hl
        ld b,12
bl_row:
        push bc
        ld hl,(big_src)
        ld c,(hl)               ; the row: C D E, then L
        inc hl
        ld d,(hl)
        inc hl
        ld e,(hl)
        inc hl
        ld (big_src),hl
        ld l,0
        ld a,(big_x)
        and 7                   ; shifted right so much
        jr z,bl_put
        ld b,a
bl_shift:
        srl c
        rr d
        rr e
        rr l
        djnz bl_shift
bl_put:
        ld a,l
        ld (big_tmp),a
        ld hl,(big_dst)
        call or_four            ; row 2y
        push de
        ld de,BIG_STRIDE
        add hl,de
        pop de
        call or_four            ; row 2y + 1
        push de
        ld de,BIG_STRIDE
        add hl,de
        pop de
        ld (big_dst),hl
        pop bc
        djnz bl_row
        ret

; C, D, E and big_tmp OR-ed into the 4 bytes at HL.
; HL, BC, DE stay.
or_four:
        push hl
        ld a,c
        or (hl)
        ld (hl),a
        inc hl
        ld a,d
        or (hl)
        ld (hl),a
        inc hl
        ld a,e
        or (hl)
        ld (hl),a
        inc hl
        ld a,(big_tmp)
        or (hl)
        ld (hl),a
        pop hl
        ret

; big_out rows 0-23 from the squares of big_in: of the
; pixels of a square, those with no square above or on
; the left are lit; of the others, those with no square
; below or on the right are in shadow; the rest are lit
; but on rows 7 and 15 (dark) and 6 and 14 (one pixel in
; two). Eight pixels at a time, I the byte, U and D those
; above and below, L and R the byte shifted from the
; left and from the right:
; out = I and not (U and L) or (I and U and L and D and R
; and the row's mask).
big_edges:
        ld hl,big_in+BIG_STRIDE+1
        ld de,big_out
        ld c,0                  ; the row
be_row:
        ld a,c
        ld b,0                  ; rows 7 and 15: dark
        cp 7
        jr z,be_mask
        cp 15
        jr z,be_mask
        ld b,%01010101          ; rows 6 and 14: x odd
        cp 6
        jr z,be_mask
        cp 14
        jr z,be_mask
        ld b,%11111111
be_mask:
        ld a,b
        ld (big_mask),a
        ld b,32
be_byte:
        push bc
        push hl
        ld bc,-BIG_STRIDE
        add hl,bc
        ld a,(hl)               ; U
        ld (big_u),a
        ld bc,2*BIG_STRIDE
        add hl,bc
        ld a,(hl)               ; D
        ld (big_d),a
        pop hl
        dec hl
        ld a,(hl)               ; the byte on the left:
        inc hl
        rrca                    ; its last pixel
        ld a,(hl)
        rra                     ; L
        ld c,a
        inc hl
        ld a,(hl)               ; the byte on the right:
        dec hl
        rlca                    ; its first pixel
        ld a,(hl)
        rla                     ; R
        ld b,a
        ld a,(big_u)
        and c                   ; U and L
        ld c,a
        cpl
        and (hl)                ; lit: I and not (U and L)
        ld (big_lit),a
        ld a,c
        and (hl)
        and b                   ; I and U and L and R
        ld b,a
        ld a,(big_d)
        and b                   ; and D
        ld b,a
        ld a,(big_mask)
        and b
        ld b,a
        ld a,(big_lit)
        or b
        ld (de),a
        inc de
        inc hl
        pop bc
        djnz be_byte
        inc hl                  ; past the blank bytes
        inc hl
        inc c
        ld a,c
        cp 24
        jr nz,be_row
        ret

; The drips of moss under the logo (logo_drips: x and
; length n): pixels x on rows 24 to 23 + n of big_out; a
; drip longer than 4 ends in a drop, x + 1 on row 23 + n
; and x, x + 1 on row 24 + n.
big_drips:
        ld hl,logo_drips
bd_next:
        ld a,(hl)
        or a
        ret z
        ld d,a                  ; x
        inc hl
        ld b,(hl)               ; n
        inc hl
        push hl
        ld c,b
        ld e,24
bd_down:
        call big_plot
        inc e
        djnz bd_down            ; E: 24 + n
        ld a,c
        cp 5
        jr c,bd_done
        dec e                   ; 23 + n
        inc d
        call big_plot
        inc e                   ; 24 + n
        call big_plot
        dec d
        call big_plot
bd_done:
        pop hl
        jr bd_next

; D = x, E = row of big_out: that pixel set. BC, DE stay.
big_plot:
        push bc
        ld l,e
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl               ; row x 32
        ld a,d
        rrca
        rrca
        rrca
        and 31
        ld c,a
        ld b,0
        add hl,bc
        ld bc,big_out
        add hl,bc
        ld a,d
        and 7
        ld b,a
        ld a,%10000000
        jr z,bp_set
bp_shift:
        rrca
        djnz bp_shift
bp_set:
        or (hl)
        ld (hl),a
        pop bc
        ret

; big_out to the screen, cell by cell from big_row:
; rows 1-2 of the word in the first colour, row 3 in the
; second, the moss row (if any) in the third.
big_cells:
        ld a,(big_colours+2)
        cp NO_MOSS
        ld a,3
        jr z,bc_count
        inc a
bc_count:
        ld (big_rows),a
        ld a,(big_row)
        ld b,a
        ld hl,big_out
        xor a
bc_row:
        ld (big_r),a            ; the row of the word, 0-3
        ld de,big_colours
        cp 2
        jr c,bc_colour          ; 0, 1: the first colour
        inc de
        jr z,bc_colour          ; 2: the second
        inc de                  ; 3: the moss
bc_colour:
        ld a,(de)
        ld (big_colour),a
        ld c,0
bc_cell:
        push hl
        push bc
        ld de,big_tmp8
        ld b,8
bc_gather:
        ld a,(hl)
        ld (de),a
        inc de
        push de
        ld de,32
        add hl,de
        pop de
        djnz bc_gather
        pop bc
        ld hl,big_tmp8
        ld a,(big_colour)
        call put_cell
        pop hl
        inc hl
        inc c
        ld a,c
        cp 32
        jr nz,bc_cell
        ld de,7*32              ; the next row of cells
        add hl,de
        inc b
        ld a,(big_r)
        inc a
        ld e,a
        ld a,(big_rows)
        cp e
        ld a,e
        jr nz,bc_row
        ret

; ---- texts and tables ---------------------------------
bat_bob:        db 0,1,2,3,3,2,1,0
mode_names:     dw txt_music,txt_fx,txt_silent
txt_music:      db "MUSIC",0
txt_fx:         db "SOUND FX",0
txt_silent:     db "SILENT",0
txt_on:         db "> ",0
txt_off:        db "  ",0
txt_prompt:     db "PRESS FIRE",0
txt_credit:     db "(C) 2026 ERIC A. NORTON",0
txt_score:      db "SCORE",0
txt_seals:      db "SEALS",0
txt_rooms:      db "ROOMS",0
txt_of_16:      db "/16",0
