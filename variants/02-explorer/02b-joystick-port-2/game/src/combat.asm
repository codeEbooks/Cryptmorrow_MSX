; combat.asm - the sprites: the VDP draws them. Each
; pass prepares the explorer's two sprites in RAM
; (show_combat), put_sprites gives them to the VDP at
; the top of the next frame. The sword, the skeletons
; and the bats come in step 5.

; ---- show_combat --------------------------------------
; At the end of the pass: the sprites of the next frame.
; The explorer's two sprites.
show_combat:
        call hero_sprites
        ret

; ---- put_sprites --------------------------------------
; At the top of the frame, in the border: the list the
; last pass prepared, to the VDP: the explorer's two
; sprites.
put_sprites:
        ld de,SPRITES
        call vram_write_at
        ld hl,hero_sat
        ld b,8
        call ps_bytes
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
