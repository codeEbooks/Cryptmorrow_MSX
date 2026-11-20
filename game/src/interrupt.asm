; interrupt.asm - the frame interrupt (IM 2): read the
; VDP's status, which ends the request, count frames and {6}
; play a frame of the sound (player.asm). It keeps every {6}
; register it uses: it can arrive in the middle of a {6}
; change of room, which takes several frames. {6}
;|; VDP's status, which ends the request, and count the {-5}
;|; frames. It keeps every register it uses. {-5}

isr:
        push af
        in a,(VDP_STAT)         ; clears the request
        ld (vdp_status),a       ; {5}
        push bc                 ; {6}
        push de                 ; {6}
        push hl
        push ix                 ; {6}
        ld hl,(frames)
        inc hl
        ld (frames),hl
        call audio_frame        ; the PSG of this frame {6}
isr_done:                       ; (the tests time it)
        pop ix                  ; {6}
        pop hl
        pop de                  ; {6}
        pop bc                  ; {6}
        pop af
        ei
        reti
