; vars.asm - the RAM of page 3 (#C000-#F37F): every byte
; has one owner, named here.

; ---- the frame ----------------------------------------
frames          equ #C000       ; 2: interrupts counted
vdp_status      equ #C002       ; status read by the IRQ

; ---- start-up -----------------------------------------
cart_slot       equ #C003       ; our slot, E000SSPP
msx_id1         equ #C004       ; byte #002B of the BIOS

; ---- the room -----------------------------------------
room            equ #C005       ; number of the room shown
zone            equ #C006       ; its zone, #FF = none yet
zone_mt         equ #C007       ; 2: the zone's metatiles
room_rec        equ #C05B       ; 2: this room's record
zone_so         equ #C054       ; 2: the zone's solid kinds
flame_count     equ #C009       ; flame slots of the zone
flame_list      equ #C00A       ; 6 x 3: VRAM address, type
FLAME_MAX       equ 6           ; build_msx.py: no more
flame_phase     equ #C056       ; phase drawn, x 8
reveal_due      equ #C057       ; 1: a room to reveal

; ---- the HUD ------------------------------------------
energy          equ #C01C       ; 0-8
key_set         equ #C01D       ; keys carried: bits 0-2 A-C
seals           equ #C01E       ; seals carried, 0-3
score           equ #C01F       ; 3: BCD, high byte first
hud_row         equ #C022       ; 32: row 0 of the screen
hud_dirty       equ #C05D       ; 1: row 0 to draw again

; ---- work ---------------------------------------------
cells_left      equ #C042       ; load_third: cells to go
cells_skip      equ #C716       ; load_third: the bands'
row_third       equ #C043       ; build_room: third x 4

; ---- the explorer -------------------------------------
input           equ #C044       ; 1 = held: bits of JOY_*
hero_x          equ #C045       ; screen pixels, top left
hero_y          equ #C046
hero_dir        equ #C047       ; DIR_DOWN, UP, LEFT, RIGHT
hero_frame      equ #C048       ; 0 standing, 1 the step
hero_timer      equ #C049       ; frames since the last step
hero_moving     equ #C04A       ; 1 if it moved this frame
hero_block      equ #C04B       ; 1 if a solid cell stops it
hero_sat        equ #C04C       ; 8: 2 x Y, X, shape, ink

; ---- the game -----------------------------------------
doors_open      equ #C058       ; bits 0-2 doors A-C, 3 gate
game_ended      equ #C059       ; ENDED_LOST, ENDED_WON
door_here       equ #C05A       ; door of this room, 0 none
obj_slot        equ #C05E       ; slot being looked at
hit_col         equ #C05F       ; metatile under the middle
hit_row         equ #C060       ; of the hitbox
room_shown      equ #C061       ; 1: room_names is shown
taken           equ #C062       ; 32: 1 = taken (room x 2
TAKEN_SIZE      equ 32          ; + slot)

; ---- the combat ---------------------------------------
turn            equ #C082       ; passes of the main loop
slash_timer     equ #C083       ; 20 at a blow, down to 0
blade_dir       equ #C084       ; direction of the blow
fire_held       equ #C085       ; JOY_FIRE if held last pass
invulnerable    equ #C086       ; passes left without damage
pt_x            equ #C087       ; 2: a point, for measure
pt_y            equ #C089
far_x           equ #C08A       ; its distance from an enemy
far_y           equ #C08B
west            equ #C08C       ; #FF: the point is left
north           equ #C08D       ; #FF: the point is above
hero_shown      equ #C08E       ; 1: sprites 0-1 are listed
spr_rot         equ #C08F       ; the first of the others
spr_count       equ #C090       ; the others in spr_list
spr_list        equ #C091       ; 16: 4 x Y, X, shape, ink
enemies         equ #C0A1       ; 27: 3 x EN_SIZE

; ---- buffers ------------------------------------------
room_names      equ #C100       ; 640: rows 2-21 of names
name_row        equ #C380       ; 32: row 23, the name
solid_map       equ #C400       ; 640: 1 = solid, 32 x 20

; ---- the sound ----------------------------------------
music_speed     equ #C680       ; frames a step: 6 or 7
audio_mode      equ #C681       ; MODE_MUSIC, _FX, _SILENT
music_song      equ #C682       ; song being played
music_tick      equ #C683       ; frame inside the step
music_frames    equ #C684       ; 2: frames since init
music_owed      equ #C686       ; 1: music_step is due
music_by_isr    equ #C687       ; 1: the interrupt does it
voice_n         equ #C688       ; voice being worked out
sfx_next        equ #C689       ; effect to start, 0 none
sfx_pos         equ #C68A       ; next entry, 0 none
sfx_prio        equ #C68B       ; priority of the effect
                                ; asked or playing, 0 none
psg_shadow      equ #C690       ; 11: registers 0-10, the
                                ; next frame
voices          equ #C6A0       ; 57: 3 x VOICE_SIZE

; ---- the states ---------------------------------------
game_state      equ #C6E0       ; STATE_TITLE, _PLAY, ...
end_timer       equ #C6E1       ; passes of ENDING, of END
fire_armed      equ #C6E2       ; 1: FIRE pressed here
stick_held      equ #C6E3       ; up and down of last pass
rooms_seen      equ #C6E4       ; 2: a bit for each room
menu_mode       equ #C6E6       ; the line being drawn
menu_colour     equ #C6E7       ; its colour
text_colour     equ #C6E8       ; print_text's colour
prompt_colour   equ #C6E9       ; PRESS FIRE's, as shown
band_cells      equ #C6EA       ; 4: the zone's thirds 0, 1
band_flames     equ #C6EE       ; 2: the zone's flame slots
band_third      equ #C6F0       ; the band's third: 0 or 1
band_slot       equ #C6F1       ; the slot being drawn
band_colour     equ #C6F2       ; its colour
big_x           equ #C6F3       ; pixel column of a letter
big_row         equ #C6F4       ; the word's character row
big_colours     equ #C6F5       ; 3: its rows' colours
big_src         equ #C6F8       ; 2: in the letter's rows
big_dst         equ #C6FA       ; 2: in big_in
big_tmp         equ #C6FC       ; a letter row's 4th byte
big_u           equ #C6FD       ; the byte above
big_d           equ #C6FE       ; the byte below
big_lit         equ #C6FF       ; the lit pixels
big_mask        equ #C700       ; the row's mask
big_rows        equ #C701       ; rows of cells of a word
big_r           equ #C702       ; the one being drawn
big_colour      equ #C703       ; its colour
big_tmp8        equ #C704       ; 8: a cell's pattern
stat_text       equ #C70C       ; 10: a value as text
big_in          equ #C720       ; 26 x 34: the squares of
BIG_IN_SIZE     equ 26*34       ; a word, a blank row above
                                ; and below, a blank byte
                                ; on each side
big_out         equ big_in+BIG_IN_SIZE ; 32 x 32: its pixels
BIG_OUT_SIZE    equ 32*32       ; and the moss under it

; ---- the interrupt and the stack ----------------------
IM2_TAB         equ #F000       ; 257 bytes of IM2_HI
IM2_HI          equ #F1         ; the table points at #F1F1
IM2_JP          equ #F1F1       ; JP isr
STACK           equ #F380       ; BIOS work area above
