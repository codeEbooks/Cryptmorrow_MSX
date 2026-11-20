; interrupt.asm - the frame interrupt (IM 2): read the
; VDP's status, which ends the request, count frames and
; play a frame of the sound (player.asm). It keeps every
; register it uses: it can arrive in the middle of a
; change of room, which takes several frames.

isr:
        push af
        in a,(VDP_STAT)         ; clears the request
        ld (vdp_status),a
        push bc
        push de
        push hl
        push ix
        ld hl,(frames)
        inc hl
        ld (frames),hl
        call audio_frame        ; the PSG of this frame
isr_done:                       ; (the tests time it)
        pop ix
        pop hl
        pop de
        pop bc
        pop af
        ei
        reti
