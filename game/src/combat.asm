; combat.asm - the sword, the skeletons and the bats, the {5}
; damage and GAME OVER: the rules of the C64 game (1.0.1) {5}
; as Cryptmorrow ZX brought them to sprites of 16 x 16. {5}
; The VDP draws the sprites: each pass prepares the list {5}
; of the next frame in RAM (show_combat), put_sprites {5}
; gives it to the VDP at the top of that frame. Sprites {5}
; 0-1 are the explorer, then the blade and the enemies, {5}
; a sprite each in a colour of its own. The enemies of a {5}
; room come back each time the room is entered. {5}
;|; combat.asm - the sprites: the VDP draws them. Each {2-4}
;|; pass prepares the explorer's two sprites in RAM {2-4}
;|; (show_combat), put_sprites gives them to the VDP at {2-4}
;|; the top of the next frame. The sword, the skeletons {2-4}
;|; and the bats come in step 5. {2-4}

;{5}
SLASH_FRAMES    equ 20          ; a blow lasts 20 passes:
BLADE_FRAMES    equ 8           ; the blade is out for 8
BLADE_UNTIL     equ SLASH_FRAMES-BLADE_FRAMES
SAFE_FRAMES     equ 30          ; passes safe after a hit
DAMAGE          equ 2           ; energy lost at a touch
FLASH_FRAMES    equ 8           ; a hit enemy is red, stops
DUST_FRAMES     equ 12          ; a defeated enemy: dust
REACH_X         equ 8           ; closer than this on both
REACH_Y         equ 9           ; axes: a touch, or a hit
CHASE_X         equ 96          ; a bat chases the explorer
CHASE_Y         equ 90          ; inside this distance
RING_LEFT       equ 8           ; skeletons stay out of the
RING_RIGHT      equ 248         ; outer ring of cells, where
RING_TOP        equ ROOM_TOP+8  ; the openings are
RING_BOTTOM     equ ROOM_TOP+ROOM_LINES-8
BLADE_MAX_X     equ 239         ; the blade within the room
;{}
ENDED_LOST      equ 1           ; game_ended: GAME OVER {5}
ENDED_WON       equ 2           ; game_ended: VICTORY {4}
;{5}

; The images of combat_shapes, and the colours
IMG_SKELETON    equ 0           ; two images each
IMG_BAT         equ 2
IMG_DUST        equ 4
IMG_BLADE       equ 5           ; + direction
COMBAT_SHAPE    equ 64          ; the shape of image 0
SKELETON_INK    equ 15          ; white
BAT_INK         equ 13          ; magenta
DUST_INK        equ 14          ; grey
BLADE_INK       equ 7           ; cyan
HIT_INK         equ 8           ; red: an enemy just hit

; An enemy: EN_SIZE bytes in enemies, IX points to it.
EN_KIND         equ 0           ; 0 none, SKELETON, BAT
EN_X            equ 1           ; sprite corner, pixels
EN_Y            equ 2
EN_DIR          equ 3           ; a skeleton's DIR_ value
EN_HP           equ 4           ; hits still needed
EN_FLASH        equ 5           ; passes of the hit
EN_DUST         equ 6           ; passes of dust left
EN_HIT          equ 7           ; 1: hit by this blow
EN_FAST         equ 8           ; FAST_FLAG: every pass
EN_SIZE         equ 9
;{}

;{5}
; ---- check_fire ---------------------------------------
; Before the explorer moves. FIRE starts a blow when the
; last one is over and FIRE was up in the pass before: no
; repeat while it is held. While the blade is out the
; explorer stands still: the input is ignored.
check_fire:
        ld a,(slash_timer)
        or a
        jr z,cf_ready
        dec a
        ld (slash_timer),a
cf_ready:
        ld a,(input)
        and JOY_FIRE
        ld hl,fire_held
        cp (hl)
        ld (hl),a
        jr z,cf_blade           ; no change
        or a
        jr z,cf_blade           ; released
        ld a,(slash_timer)
        or a
        jr nz,cf_blade          ; the last blow goes on
        ld a,SLASH_FRAMES       ; a new blow
        ld (slash_timer),a
        ld a,(hero_dir)
        ld (blade_dir),a
        ld ix,enemies           ; nobody hit by it yet
        ld de,EN_SIZE
        ld b,MAX_ENEMIES
cf_clear:
        ld (ix+EN_HIT),0
        add ix,de
        djnz cf_clear
        ld a,SFX_SLASH          ; {6}
        call sound_effect       ; {6}
cf_blade:
        ld a,(slash_timer)
        cp BLADE_UNTIL+1
        ret c
        xor a                   ; the blade is out
        ld (input),a
        ret

; ---- spawn_enemies ------------------------------------
; From enter_room: the enemies of the room at their
; places, each exactly on its metatile: x = 16 column,
; y = 16 row + ROOM_TOP. The room's record has three
; slots: kind (0 none), column, row, flags (AXIS_FLAG up
; and down, FAST_FLAG every pass).
spawn_enemies:
        ld hl,(room_rec)
        ld de,ROOM_ENEMIES
        add hl,de
        ld ix,enemies
        ld b,MAX_ENEMIES
se_slot:
        ld a,(hl)               ; kind, 0 none
        ld (ix+EN_KIND),a
        inc hl
        push hl
        ld e,a
        ld d,0
        ld hl,enemy_hp
        add hl,de
        ld a,(hl)
        ld (ix+EN_HP),a
        pop hl
        ld a,(hl)               ; column
        add a,a
        add a,a
        add a,a
        add a,a
        ld (ix+EN_X),a
        inc hl
        ld a,(hl)               ; row
        add a,a
        add a,a
        add a,a
        add a,a
        add a,ROOM_TOP
        ld (ix+EN_Y),a
        inc hl
        ld a,(hl)               ; flags
        inc hl
        ld c,a
        and FAST_FLAG
        ld (ix+EN_FAST),a
        ld a,c
        and AXIS_FLAG
        ld a,DIR_RIGHT          ; across: right first
        jr z,se_patrol
        ld a,DIR_DOWN           ; up and down: down first
se_patrol:
        ld (ix+EN_DIR),a
        xor a
        ld (ix+EN_FLASH),a
        ld (ix+EN_DUST),a
        ld (ix+EN_HIT),a
        ld de,EN_SIZE
        add ix,de
        djnz se_slot
        ret

; ---- update_enemies -----------------------------------
; Dust stays for a moment, then the slot is empty; a hit
; enemy stands still while it is red; the others move.
update_enemies:
        ld ix,enemies
        ld b,MAX_ENEMIES
ue_enemy:
        push bc
        ld a,(ix+EN_KIND)
        or a
        jr z,ue_next            ; an empty slot, or gone
        ld a,(ix+EN_DUST)
        or a
        jr z,ue_alive
        dec (ix+EN_DUST)        ; dust for a moment,
        jr nz,ue_next
        ld (ix+EN_KIND),0       ; then gone
        jr ue_next
ue_alive:
        ld a,(ix+EN_FLASH)
        or a
        jr z,ue_moves
        dec (ix+EN_FLASH)       ; just hit: stands still
        jr ue_next
ue_moves:
        ld a,(ix+EN_KIND)
        cp SKELETON
        jr nz,ue_bat
        call skeleton_step
        jr ue_next
ue_bat:
        call bat_step
ue_next:
        ld de,EN_SIZE
        add ix,de
        pop bc
        djnz ue_enemy
        ret

; ---- skeleton_step ------------------------------------
; A skeleton walks a pixel every other pass along its
; patrol (every pass if fast) and turns back at anything
; solid or at the ring of the openings.
skeleton_step:
        ld a,(ix+EN_FAST)
        or a
        jr nz,sk_now            ; fast: no rest
        ld a,(turn)
        rrca
        ret c                   ; odd pass: it rests
sk_now:
        call enemy_blocked
        jr z,sk_ahead
        ld a,(ix+EN_DIR)        ; turn round: down-up,
        xor 1                   ; left-right
        ld (ix+EN_DIR),a
        ret
sk_ahead:
        ld a,(ix+EN_DIR)
        cp DIR_LEFT
        jr z,enemy_left
        cp DIR_RIGHT
        jr z,enemy_right
        cp DIR_UP
        jr z,enemy_up
enemy_down:
        inc (ix+EN_Y)
        ret
enemy_up:
        dec (ix+EN_Y)
        ret
enemy_left:
        dec (ix+EN_X)
        ret
enemy_right:
        inc (ix+EN_X)
        ret

; ---- bat_step -----------------------------------------
; A bat hangs still until the explorer comes within
; CHASE_X x CHASE_Y, then flies after it: across on even
; passes, up or down on odd ones, over walls and pillars.
bat_step:
        call aim_at_hero
        call measure
        ld a,(far_x)
        cp CHASE_X
        ret nc                  ; too far: it waits
        ld a,(far_y)
        cp CHASE_Y
        ret nc
        ld a,(turn)
        rrca
        jr c,bt_vertical        ; odd pass
        ld a,(far_x)
        or a
        ret z                   ; the same column already
        ld a,(west)
        or a
        jr nz,enemy_left
        jr enemy_right
bt_vertical:
        ld a,(far_y)
        or a
        ret z
        ld a,(north)
        or a
        jr nz,enemy_up
        jr enemy_down

; ---- enemy_blocked ------------------------------------
; NZ if the feet of the enemy (the explorer's hitbox)
; cannot move a pixel in its direction: two points on
; the edge that moves.
enemy_blocked:
        ld a,(ix+EN_DIR)
        cp DIR_LEFT
        jr nc,eb_across         ; left or right
        ld c,BOX_BOTTOM+1       ; down: below the feet
        or a
        jr z,eb_row
        ld c,BOX_TOP-1          ; up: above them
eb_row:
        ld a,(ix+EN_Y)
        add a,c
        ld e,a                  ; E = y of the points
        ld a,(ix+EN_X)
        add a,BOX_LEFT
        ld d,a
        call enemy_cell
        ret nz
        ld a,(ix+EN_X)
        add a,BOX_RIGHT
        ld d,a
        jr enemy_cell
eb_across:
        ld c,BOX_LEFT-1         ; left of the feet
        jr z,eb_column
        ld c,BOX_RIGHT+1        ; right of them
eb_column:
        ld a,(ix+EN_X)
        add a,c
        ld d,a                  ; D = x of the points
        ld a,(ix+EN_Y)
        add a,BOX_TOP
        ld e,a
        call enemy_cell
        ret nz
        ld a,(ix+EN_Y)
        add a,BOX_BOTTOM
        ld e,a
                                ; on into enemy_cell

; D = x, E = y of a point: NZ if it is in the ring of the
; room or in a solid cell (is_solid, hero.asm)
enemy_cell:
        ld a,e
        cp RING_TOP
        jr c,ec_ring
        cp RING_BOTTOM
        jr nc,ec_ring
        ld a,d
        cp RING_LEFT
        jr c,ec_ring
        cp RING_RIGHT
        jp c,is_solid           ; inside the ring
ec_ring:
        ld a,1
        or a
        ret

; ---- aim_at_hero, measure, near -----------------------
; aim_at_hero: the point (pt_x, pt_y) = the explorer's
; corner. measure: from enemy IX to the point: far_x and
; far_y (255 if farther), west = #FF if the point is left
; of the enemy, north = #FF if above. pt_x has 16 bits: a
; point of the blade may lie off the screen.
aim_at_hero:
        ld a,(hero_x)
        ld l,a
        ld h,0
        ld (pt_x),hl
        ld a,(hero_y)
        ld (pt_y),a
        ret

measure:
        xor a
        ld (west),a
        ld (north),a
        ld hl,(pt_x)
        ld e,(ix+EN_X)
        ld d,0
        or a
        sbc hl,de               ; the point - the enemy
        ld a,h
        or a
        jr z,ms_east            ; 0-255 to the east
        inc a
        jr nz,ms_far            ; 256 or more
        ld a,#FF                ; to the west
        ld (west),a
        xor a
        sub l                   ; minus the difference
        jr nz,ms_x
ms_far:
        ld a,255
        jr ms_x
ms_east:
        ld a,l
ms_x:
        ld (far_x),a
        ld a,(pt_y)
        sub (ix+EN_Y)
        jr nc,ms_y              ; the point is lower
        neg                     ; above: minus that
        ld hl,north
        dec (hl)
ms_y:
        ld (far_y),a
        ret

; carry set if far_x < REACH_X and far_y < REACH_Y
near:
        ld a,(far_x)
        cp REACH_X
        ret nc
        ld a,(far_y)
        cp REACH_Y
        ret

; ---- check_blade --------------------------------------
; While the blade is out every enemy near its point is
; hit, once a blow; then the same for a point half way
; back, so that an enemy on top of the explorer can be
; hit too. A skeleton takes three hits, a bat one.
check_blade:
        ld a,(slash_timer)
        cp BLADE_UNTIL+1
        ret c
        ld a,(blade_dir)        ; the point of the blow
        call blade_point
        ld a,(blade_dir)        ; the point half way
        add a,4                 ; (entries 4-7)
blade_point:
        ld e,a
        ld d,0
        ld hl,strike_y
        add hl,de
        ld a,(hero_y)
        add a,(hl)
        ld (pt_y),a
        ld hl,strike_x
        add hl,de
        ld a,(hl)
        ld e,a                  ; DE = the signed offset
        rla
        sbc a,a
        ld d,a
        ld a,(hero_x)
        ld l,a
        ld h,0
        add hl,de
        ld (pt_x),hl
        ld ix,enemies
        ld b,MAX_ENEMIES
cb_enemy:
        push bc
        ld a,(ix+EN_KIND)
        or a
        jr z,cb_next
        ld a,(ix+EN_DUST)
        or (ix+EN_HIT)
        jr nz,cb_next           ; dust, or hit already
        call measure
        call near
        jr nc,cb_next
        ld (ix+EN_HIT),1
        dec (ix+EN_HP)
        jr nz,cb_hurt
        ld (ix+EN_DUST),DUST_FRAMES ; gone
        ld a,(ix+EN_KIND)
        dec a
        add a,a
        ld e,a
        ld d,0
        ld hl,enemy_points
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        call add_score
        ld a,1
        ld (hud_dirty),a
        ld a,SFX_DUST           ; {6}
        call sound_effect       ; {6}
        jr cb_next
cb_hurt:
        ld (ix+EN_FLASH),FLASH_FRAMES
        ld a,SFX_HIT            ; {6}
        call sound_effect       ; {6}
cb_next:
        ld de,EN_SIZE
        add ix,de
        pop bc
        djnz cb_enemy
        ret

; ---- check_contact ------------------------------------
; An enemy touching the explorer takes DAMAGE segments of
; energy (not below zero); then the explorer cannot be
; hurt for a while and blinks. With no energy left the
; game is over.
check_contact:
        ld a,(invulnerable)
        or a
        jr z,cc_test
        dec a
        ld (invulnerable),a
        ret
cc_test:
        call aim_at_hero
        ld ix,enemies
        ld b,MAX_ENEMIES
cc_enemy:
        push bc
        ld a,(ix+EN_KIND)
        or a
        jr z,cc_next
        ld a,(ix+EN_DUST)
        or a
        jr nz,cc_next
        call measure
        call near
        jr nc,cc_next
        pop bc
        ld a,(energy)           ; hurt
        sub DAMAGE
        jr nc,cc_energy
        xor a                   ; not below zero
cc_energy:
        ld (energy),a
        ld a,SAFE_FRAMES
        ld (invulnerable),a
        ld a,1
        ld (hud_dirty),a
        ld a,SFX_HURT           ; {6}
        call sound_effect       ; {6}
        ld a,(energy)
        or a
        ret nz
        jr game_over
cc_next:
        ld de,EN_SIZE
        add ix,de
        pop bc
        djnz cc_enemy
        ret

; ---- game_over ----------------------------------------
; No energy left: the game ends. The room stands still
; with the explorer in view and no blade; GAME OVER takes
; the place of the name, its letters in LOST_COLOUR; then {6}
; the end plays (the piece of the defeat, or its effect). {6}
;|; the place of the name, its letters in LOST_COLOUR. {5-5}
game_over:
        ld a,ENDED_LOST
        ld (game_ended),a
        xor a
        ld (invulnerable),a
        ld (slash_timer),a
        ld hl,txt_over
        call hud_name           ; centred, as a name
        ld hl,txt_over
        ld c,LOST_COLOUR
        call word_colour
        ld a,ENDED_LOST         ; the VRAM first, then the {6}
        jp end_game             ; end (screens.asm) {7}
;|        jp end_sound            ; end: its piece {6-6}
;|        ret {5-5}

txt_over:
        db "GAME OVER",0
;{}

; ---- show_combat --------------------------------------
; At the end of the pass: the sprites of the next frame.
; The explorer blinks while it cannot be hurt; then the {5}
; blade while it is out, the enemies (two images each, a {5}
; new one every 8 passes for a skeleton and every 4 for a {5}
; bat; dust); an enemy just hit is red, as in the C64 {5}
; game (each sprite of the VDP has its own colour). {5}
;|; The explorer's two sprites. {2-4}
show_combat:
        ld a,(invulnerable)     ; {5}
        and 4                   ; {5}
        ld a,1                  ; {4}
        jr z,sc_hero            ; {5}
        xor a                   ; 4 passes off, 4 on {5}
sc_hero:                        ; {5}
        ld (hero_shown),a       ; {4}
        call hero_sprites
;|        ret {2-4}
;{5}
        ld hl,spr_list          ; the others from here
        ld a,(slash_timer)
        cp BLADE_UNTIL+1
        jr c,sc_enemies         ; no blade
        push hl
        ld a,(blade_dir)
        ld e,a
        ld d,0
        ld hl,blade_dy
        add hl,de
        ld a,(hero_y)
        add a,(hl)
        ld b,a                  ; B = y
        ld hl,blade_dx
        add hl,de
        ld a,(hero_x)
        add a,(hl)
        bit 7,(hl)              ; (carry stays)
        jr z,sc_ahead
        jr c,sc_x               ; left: no borrow
        xor a                   ; past the left edge: 0
        jr sc_x
sc_ahead:
        jr c,sc_edge            ; carried: past 255
        cp BLADE_MAX_X+1
        jr c,sc_x
sc_edge:
        ld a,BLADE_MAX_X
sc_x:
        ld c,a                  ; C = x
        ld a,(blade_dir)
        add a,IMG_BLADE
        pop hl
        call list_sprite
sc_enemies:
        ld ix,enemies
        ld b,MAX_ENEMIES
sc_enemy:
        push bc
        ld a,(ix+EN_KIND)
        or a
        jr z,sc_next
        ld a,(ix+EN_DUST)
        or a
        ld a,IMG_DUST
        jr nz,sc_image
        ld a,(turn)
        rrca                    ; a bat: pass / 4
        rrca
        ld b,(ix+EN_KIND)
        djnz sc_frame           ; a skeleton (1): pass / 8
        rrca
sc_frame:
        and 1
        add a,IMG_SKELETON
        bit 1,(ix+EN_KIND)      ; a bat: images 2-3
        jr z,sc_image
        add a,IMG_BAT-IMG_SKELETON
sc_image:
        ld b,(ix+EN_Y)
        ld c,(ix+EN_X)
        call list_sprite
        ld a,(ix+EN_FLASH)      ; (0 for dust: a blow
        or a                    ; comes 20 passes after
        jr z,sc_next            ; the last)
        dec hl                  ; just hit: its colour
        ld (hl),HIT_INK         ; red
        inc hl
sc_next:
        ld de,EN_SIZE
        add ix,de
        pop bc
        djnz sc_enemy
        ld a,l                  ; the entries written
        sub spr_list & #FF
        rrca
        rrca
        ld (spr_count),a
        ret

; A = combat image, B = y, C = x: an entry of spr_list at
; HL (Y a line higher: the VDP shows it one lower), the
; image's shape and colour; HL moves on. DE, IX stay.
list_sprite:
        push de
        ld e,a
        ld d,0
        ld (hl),b
        dec (hl)                ; Y
        inc hl
        ld (hl),c               ; X
        inc hl
        add a,a
        add a,a                 ; x 4: shapes of 16 x 16
        add a,COMBAT_SHAPE
        ld (hl),a               ; the shape
        inc hl
        push hl
        ld hl,image_ink
        add hl,de
        ld a,(hl)
        pop hl
        ld (hl),a               ; the colour
        inc hl
        pop de
        ret
;{}

; ---- put_sprites --------------------------------------
; At the top of the frame, in the border: the list the
; last pass prepared, to the VDP. The explorer first {5}
; (unless it blinks), then the others. The VDP shows four {5}
; sprites on a line; if in the last picture it had to {5}
; leave one out (bit 6 of the status, which the interrupt {5}
; keeps), the others start one place further on: the one {5}
; left out changes every frame, it flickers instead of {5}
; vanishing. {5}
;|; last pass prepared, to the VDP: the explorer's two {2-4}
;|; sprites. {2-3}
;|; sprites, unless the game has ended (hero_shown). {4-4}
put_sprites:
        ld hl,spr_rot           ; {5}
        ld a,(vdp_status)       ; {5}
        and %01000000           ; a fifth sprite on a line {5}
        jr z,ps_first           ; {5}
        inc (hl)                ; a place further on {5}
ps_first:                       ; {5}
        ld a,(spr_count)        ; {5}
        ld c,a                  ; {5}
        ld a,(hl)               ; {5}
        cp c                    ; {5}
        jr c,ps_list            ; {5}
        xor a                   ; past the last: the first {5}
        ld (hl),a               ; {5}
ps_list:                        ; {5}
        ld de,SPRITES
        call vram_write_at
        ld a,(hero_shown)       ; {4}
        or a                    ; {4}
        jr z,ps_others          ; {4}
        ld hl,hero_sat
        ld b,8
        call ps_bytes
ps_others:                      ; {4}
        ld a,(spr_rot)          ; {5}
        add a,a                 ; {5}
        add a,a                 ; x 4: bytes before the {5}
        ld e,a                  ; first {5}
        ld d,0                  ; {5}
        ld hl,spr_list          ; {5}
        add hl,de               ; {5}
        ld a,(spr_count)        ; {5}
        add a,a                 ; {5}
        add a,a                 ; {5}
        sub e                   ; from the first to the end {5}
        ld b,a                  ; {5}
        call ps_bytes           ; {5}
        ld hl,spr_list          ; then those before it {5}
        ld b,e                  ; {5}
        call ps_bytes           ; {5}
        ld a,208                ; the end of the list
        out (VDP_DATA),a
        ret

; B bytes (0: none) from HL to the VDP: 29 T a byte
ps_bytes:
        ld a,b
        or a
        ret z
        ld c,VDP_DATA
ps_byte:
        outi                    ; 18 T
        jp nz,ps_byte           ; 11 T
        ret

;{5}
; ---- tables -------------------------------------------
; By direction (down, up, left, right): the point of a
; blow from the explorer's corner (0-3), the point half
; way back (4-7); where the blade is drawn.
strike_x:
        db 2,2,256-13,13,2,2,256-7,7
strike_y:
        db 12,256-15,255,255,6,256-8,255,255
blade_dx:
        db 5,5,256-11,11
blade_dy:
        db 8,256-6,0,0
; By enemy kind (0, skeleton, bat): hits; points (BCD)
enemy_hp:
        db 0,3,1
enemy_points:
        dw #0100,#0050
; By image: the colour of its sprite
image_ink:
        db SKELETON_INK,SKELETON_INK,BAT_INK,BAT_INK
        db DUST_INK,BLADE_INK,BLADE_INK,BLADE_INK
        db BLADE_INK
;{}
