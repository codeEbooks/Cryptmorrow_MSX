; main.asm - the main loop: a frame at a time. It waits
; for the frame, then the torches.

main_loop:
        halt                    ; wait for the frame
        call animate_torches
frame_ready:                    ; the tests stop here
        jr main_loop
