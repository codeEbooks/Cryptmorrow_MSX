; msx.asm - the MSX1 hardware the game uses, by name.
; Our own names (no third-party header); the values
; are those of the MSX standard, checked in Phase 0.

; VDP (TMS9918A / TMS9929A)
VDP_DATA        equ #98         ; VRAM data, read and write
VDP_CTRL        equ #99         ; write: address, register
VDP_STAT        equ #99         ; read: status register

; PPI (8255)
PPI_SLOT        equ #A8         ; primary slot of each page

; Main ROM (BIOS): the only calls, at start-up
ENASLT          equ #0024       ; select a slot in a page
RSLREG          equ #0138       ; read the primary slots

; BIOS work area, read at start-up
EXPTBL          equ #FCC1       ; slot expanded? (bit 7)
SLTTBL          equ #FCC5       ; secondary slot registers
HTIMI           equ #FD9F       ; frame interrupt hook
