; interrupt.asm - the frame interrupt (IM 2): read the
; VDP's status, which ends the request, and count the
; frames. It keeps every register it uses.

isr:
        push af
        in a,(VDP_STAT)         ; clears the request
        push hl
        ld hl,(frames)
        inc hl
        ld (frames),hl
isr_done:                       ; (the tests time it)
        pop hl
        pop af
        ei
        reti
