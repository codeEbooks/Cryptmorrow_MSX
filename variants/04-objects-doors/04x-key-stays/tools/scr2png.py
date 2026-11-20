"""Turn the 6912 bytes of a Spectrum screen into a PNG, as Fuse shows it.

The picture is Fuse's canvas: 320 x 240 pixels, the 256 x 192 paper at
(32, 24) inside the border. Colours are Fuse's: 0 and 192 for the
normal colours, 0 and 255 with BRIGHT (the same table in screenshot.c,
in the SDL display and in the Windows display of Fuse 1.6.0). FLASH is
drawn in its first phase (ink as ink).

--scale N repeats every pixel N times (no interpolation): the copy for
print. At 300 dpi a scale of 4 (1280 pixels) fits 10.8 cm.

Usage: python tools/scr2png.py SCREEN.scr BORDER OUT.png [--scale N]
       (or import: png_bytes(screen, border, scale))
Standard library only.
"""
import struct
import sys
import zlib

PALETTE = ((0, 0, 0), (0, 0, 192), (192, 0, 0), (192, 0, 192),
           (0, 192, 0), (0, 192, 192), (192, 192, 0), (192, 192, 192),
           (0, 0, 0), (0, 0, 255), (255, 0, 0), (255, 0, 255),
           (0, 255, 0), (0, 255, 255), (255, 255, 0), (255, 255, 255))
WIDTH, HEIGHT = 320, 240
LEFT, TOP = 32, 24


def pixels(screen, border):
    """Rows of palette indices, 320 x 240."""
    rows = [[border & 7] * WIDTH for _ in range(HEIGHT)]
    for y in range(192):
        base = ((y & 0xC0) << 5) | ((y & 7) << 8) | ((y & 0x38) << 2)
        row = rows[TOP + y]
        for c in range(32):
            byte = screen[base + c]
            attr = screen[6144 + (y // 8) * 32 + c]
            bright = 8 if attr & 0x40 else 0
            ink = (attr & 7) + bright
            paper = ((attr >> 3) & 7) + bright
            for bit in range(8):
                on = byte & (0x80 >> bit)
                row[LEFT + c * 8 + bit] = ink if on else paper
    return rows


def png_bytes(screen, border, scale=1):
    rows = pixels(screen, border)
    raw = bytearray()
    plte = b''.join(bytes(c) for c in PALETTE)
    for row in rows:
        line = bytearray()
        for p in row:
            line.extend([p] * scale)
        for _ in range(scale):
            raw.append(0)
            raw.extend(line)

    def chunk(kind, data):
        body = kind + data
        return (struct.pack('>I', len(data)) + body
                + struct.pack('>I', zlib.crc32(body) & 0xFFFFFFFF))

    head = struct.pack('>IIBBBBB', WIDTH * scale, HEIGHT * scale,
                       8, 3, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', head)
            + chunk(b'PLTE', plte)
            + chunk(b'IDAT', zlib.compress(bytes(raw), 9))
            + chunk(b'IEND', b''))


def rgb_rows(screen, border):
    """Rows of (r, g, b) tuples: for comparisons with other images."""
    return [[PALETTE[p] for p in row] for row in pixels(screen, border)]


def main(argv):
    scale = 1
    if '--scale' in argv:
        i = argv.index('--scale')
        scale = int(argv[i + 1])
        del argv[i:i + 2]
    scr_file, border, out = argv
    screen = open(scr_file, 'rb').read()
    if len(screen) != 6912:
        raise SystemExit(f'{scr_file}: {len(screen)} bytes, not 6912')
    with open(out, 'wb') as f:
        f.write(png_bytes(screen, int(border), scale))


if __name__ == '__main__':
    main(sys.argv[1:])
