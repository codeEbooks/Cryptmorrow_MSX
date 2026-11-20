; vars.asm - the RAM of page 3 (#C000-#F37F): every byte
; has one owner, named here.

; ---- the frame ----------------------------------------
frames          equ #C000       ; 2: interrupts counted
vdp_status      equ #C002       ; status read by the IRQ {5}

; ---- start-up -----------------------------------------
cart_slot       equ #C003       ; our slot, E000SSPP
msx_id1         equ #C004       ; byte #002B of the BIOS {6}

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
reveal_due      equ #C057       ; 1: a room to reveal {3}

; ---- the HUD ------------------------------------------ {3}
energy          equ #C01C       ; 0-8 {3}
key_set         equ #C01D       ; keys carried: bits 0-2 A-C {3}
seals           equ #C01E       ; seals carried, 0-3 {3}
score           equ #C01F       ; 3: BCD, high byte first {3}
hud_row         equ #C022       ; 32: row 0 of the screen {3}
hud_dirty       equ #C05D       ; 1: row 0 to draw again {3}

; ---- work ---------------------------------------------
cells_left      equ #C042       ; load_third: cells to go
cells_skip      equ #C716       ; load_third: the bands'
row_third       equ #C043       ; build_room: third x 4

; ---- the explorer ------------------------------------- {2}
input           equ #C044       ; 1 = held: bits of JOY_* {2}
hero_x          equ #C045       ; screen pixels, top left {2}
hero_y          equ #C046 ; {2}
hero_dir        equ #C047       ; DIR_DOWN, UP, LEFT, RIGHT {2}
hero_frame      equ #C048       ; 0 standing, 1 the step {2}
hero_timer      equ #C049       ; frames since the last step {2}
hero_moving     equ #C04A       ; 1 if it moved this frame {2}
hero_block      equ #C04B       ; 1 if a solid cell stops it {4}
hero_sat        equ #C04C       ; 8: 2 x Y, X, shape, ink {2}

; ---- the game ----------------------------------------- {4}
doors_open      equ #C058       ; bits 0-2 doors A-C, 3 gate {4}
game_ended      equ #C059       ; ENDED_LOST, ENDED_WON {4}
door_here       equ #C05A       ; door of this room, 0 none {4}
obj_slot        equ #C05E       ; slot being looked at {4}
hit_col         equ #C05F       ; metatile under the middle {4}
hit_row         equ #C060       ; of the hitbox {4}
room_shown      equ #C061       ; 1: room_names is shown {4}
taken           equ #C062       ; 32: 1 = taken (room x 2 {4}
TAKEN_SIZE      equ 32          ; + slot) {4}

; ---- the combat --------------------------------------- {5}
turn            equ #C082       ; passes of the main loop {5}
slash_timer     equ #C083       ; 20 at a blow, down to 0 {5}
blade_dir       equ #C084       ; direction of the blow {5}
fire_held       equ #C085       ; JOY_FIRE if held last pass {5}
invulnerable    equ #C086       ; passes left without damage {5}
pt_x            equ #C087       ; 2: a point, for measure {5}
pt_y            equ #C089 ; {5}
far_x           equ #C08A       ; its distance from an enemy {5}
far_y           equ #C08B ; {5}
west            equ #C08C       ; #FF: the point is left {5}
north           equ #C08D       ; #FF: the point is above {5}
hero_shown      equ #C08E       ; 1: sprites 0-1 are listed {4}
spr_rot         equ #C08F       ; the first of the others {5}
spr_count       equ #C090       ; the others in spr_list {5}
spr_list        equ #C091       ; 16: 4 x Y, X, shape, ink {5}
enemies         equ #C0A1       ; 27: 3 x EN_SIZE {5}

; ---- buffers ------------------------------------------
room_names      equ #C100       ; 640: rows 2-21 of names
name_row        equ #C380       ; 32: row 23, the name
solid_map       equ #C400       ; 640: 1 = solid, 32 x 20

; ---- the sound ---------------------------------------- {6}
music_speed     equ #C680       ; frames a step: 6 or 7 {6}
audio_mode      equ #C681       ; MODE_MUSIC, _FX, _SILENT {6}
music_song      equ #C682       ; song being played {6}
music_tick      equ #C683       ; frame inside the step {6}
music_frames    equ #C684       ; 2: frames since init {6}
music_owed      equ #C686       ; 1: music_step is due {6}
music_by_isr    equ #C687       ; 1: the interrupt does it {6}
voice_n         equ #C688       ; voice being worked out {6}
sfx_next        equ #C689       ; effect to start, 0 none {6}
sfx_pos         equ #C68A       ; next entry, 0 none {6}
sfx_prio        equ #C68B       ; priority of the effect {6}
                                ; asked or playing, 0 none {6}
psg_shadow      equ #C690       ; 11: registers 0-10, the {6}
                                ; next frame {6}
voices          equ #C6A0       ; 57: 3 x VOICE_SIZE {6}

; ---- the states --------------------------------------- {7}
game_state      equ #C6E0       ; STATE_TITLE, _PLAY, ... {7}
end_timer       equ #C6E1       ; passes of ENDING, of END {7}
fire_armed      equ #C6E2       ; 1: FIRE pressed here {7}
stick_held      equ #C6E3       ; up and down of last pass {7}
rooms_seen      equ #C6E4       ; 2: a bit for each room {7}
menu_mode       equ #C6E6       ; the line being drawn {7}
menu_colour     equ #C6E7       ; its colour {7}
text_colour     equ #C6E8       ; print_text's colour {7}
prompt_colour   equ #C6E9       ; PRESS FIRE's, as shown {7}
band_cells      equ #C6EA       ; 4: the zone's thirds 0, 1 {7}
band_flames     equ #C6EE       ; 2: the zone's flame slots {7}
band_third      equ #C6F0       ; the band's third: 0 or 1 {7}
band_slot       equ #C6F1       ; the slot being drawn {7}
band_colour     equ #C6F2       ; its colour {7}
big_x           equ #C6F3       ; pixel column of a letter {7}
big_row         equ #C6F4       ; the word's character row {7}
big_colours     equ #C6F5       ; 3: its rows' colours {7}
big_src         equ #C6F8       ; 2: in the letter's rows {7}
big_dst         equ #C6FA       ; 2: in big_in {7}
big_tmp         equ #C6FC       ; a letter row's 4th byte {7}
big_u           equ #C6FD       ; the byte above {7}
big_d           equ #C6FE       ; the byte below {7}
big_lit         equ #C6FF       ; the lit pixels {7}
big_mask        equ #C700       ; the row's mask {7}
big_rows        equ #C701       ; rows of cells of a word {7}
big_r           equ #C702       ; the one being drawn {7}
big_colour      equ #C703       ; its colour {7}
big_tmp8        equ #C704       ; 8: a cell's pattern {7}
stat_text       equ #C70C       ; 10: a value as text {7}
open_timer      equ #C717       ; the opening's passes {8}
big_in          equ #C720       ; 26 x 34: the squares of {7}
BIG_IN_SIZE     equ 26*34       ; a word, a blank row above {7}
                                ; and below, a blank byte {7}
                                ; on each side {7}
big_out         equ big_in+BIG_IN_SIZE ; 32 x 32: its pixels {7}
BIG_OUT_SIZE    equ 32*32       ; and the moss under it {7}

; ---- the interrupt and the stack ----------------------
IM2_TAB         equ #F000       ; 257 bytes of IM2_HI
IM2_HI          equ #F1         ; the table points at #F1F1
IM2_JP          equ #F1F1       ; JP isr
STACK           equ #F380       ; BIOS work area above
