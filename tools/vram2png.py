"""Draw the MSX1 screen from the VRAM and the VDP registers.

Graphics II (Screen 2) and Graphics I, the sprites with the limit of
4 per line, Y = 208 at the end of the list, the early clock bit; the
backdrop (register 7) in the border. The result is what openMSX 21.0
shows in a raw screenshot (screenshot -raw, 320 x 240): the geometry
(GEOMETRY) and the colours were measured on openMSX screenshots.
openMSX gives the two VDPs different colours: PALETTE_OPENMSX is the
TMS9929A's (C-BIOS_MSX1_EU, 50 Hz; Phase 0, checked by
tests/fase0_check.py), PALETTE_OPENMSX_9918 the TMS9918A's
(C-BIOS_MSX1, 60 Hz; measured in milestone 0.1 on the probe of Phase
0, checked by tests/verify_0_1.py). palette(hz) picks one.

  indices(vram, regs)      192 rows of 256 colour indices (0 = the
                           backdrop shows through)
  frame(vram, regs)        240 rows of 320 indices, border included
  png_bytes(rows, palette, scale)
                           a PNG (RGB), every pixel scale x scale,
                           without smoothing

Standard library only.
"""
import struct
import zlib

GEOMETRY = {'width': 320, 'height': 240, 'left': 32, 'top': 24}
# colours of openMSX 21.0 screenshots (default video settings),
# measured in Phase 0 on every index the probe shows
PALETTE_OPENMSX = (
    (0, 5, 0),           # 0: transparent; frame() shows the backdrop
    (0, 5, 0),           # 1
    (60, 197, 72),       # 2
    (115, 217, 124),     # 3
    (91, 96, 223),       # 4
    (130, 130, 238),     # 5
    (189, 105, 80),      # 6
    (98, 228, 235),      # 7
    (221, 112, 89),      # 8
    (254, 146, 124),     # 9
    (204, 204, 92),      # 10
    (221, 216, 134),     # 11
    (55, 175, 64),       # 12
    (185, 112, 181),     # 13
    (202, 211, 201),     # 14
    (249, 255, 248),     # 15
)
# the TMS9918A of C-BIOS_MSX1 (60 Hz): the same indices, other colours
PALETTE_OPENMSX_9918 = (
    (0, 10, 0),          # 0: transparent; frame() shows the backdrop
    (0, 10, 0),          # 1
    (0, 241, 4),         # 2
    (61, 251, 78),       # 3
    (74, 84, 255),       # 4
    (118, 118, 255),     # 5
    (239, 85, 38),       # 6
    (9, 255, 255),       # 7
    (255, 85, 40),       # 8
    (255, 121, 78),      # 9
    (214, 214, 0),       # 10
    (231, 222, 67),      # 11
    (0, 214, 1),         # 12
    (220, 86, 213),      # 13
    (197, 215, 196),     # 14
    (244, 255, 243),     # 15
)


def palette(hz):
    """openMSX's colours for the machine of 50 or 60 Hz."""
    return PALETTE_OPENMSX if hz == 50 else PALETTE_OPENMSX_9918


def indices(vram, regs, limit=True):
    mode = (regs[0] & 2) | (regs[1] & 0x18)
    rows = [[0] * 256 for _ in range(192)]
    if not regs[1] & 0x40:              # screen off: backdrop
        return rows
    names = (regs[2] & 0x0F) << 10
    if mode == 2:                       # Graphics II
        pbase = (regs[4] & 4) << 11
        pmask = ((regs[4] & 3) << 11) | 0x7FF
        cbase = (regs[3] & 0x80) << 6
        cmask = ((regs[3] & 0x7F) << 6) | 0x3F
    for y in range(192):
        row = rows[y]
        for col in range(32):
            name = vram[names + (y >> 3) * 32 + col]
            if mode == 2:
                n = ((y >> 6) << 8 | name) * 8 + (y & 7)
                pat = vram[pbase | (n & pmask)]
                colr = vram[cbase | (n & cmask)]
            else:                       # Graphics I
                pat = vram[((regs[4] & 7) << 11) + name * 8 + (y & 7)]
                colr = vram[((regs[3]) << 6) + (name >> 3)]
            fg, bg = colr >> 4, colr & 15
            for b in range(8):
                row[col * 8 + b] = fg if pat & (0x80 >> b) else bg
    draw_sprites(vram, regs, rows, limit)
    return rows


def draw_sprites(vram, regs, rows, limit=True):
    size = 16 if regs[1] & 2 else 8
    mag = 2 if regs[1] & 1 else 1
    sat = (regs[5] & 0x7F) << 7
    spg = (regs[6] & 7) << 11
    for y in range(192):
        visible = []
        for s in range(32):
            sy = vram[sat + 4 * s]
            if sy == 208:
                break
            line = (y - 1 - sy) & 0xFF
            if line >= size * mag:
                continue
            if limit and len(visible) == 4:
                break
            visible.append((s, line // mag))
        for s, line in reversed(visible):   # sprite 0 on top
            x = vram[sat + 4 * s + 1]
            attr = vram[sat + 4 * s + 3]
            colour = attr & 15
            if attr & 0x80:
                x -= 32
            if colour == 0:
                continue
            pat = vram[sat + 4 * s + 2]
            if size == 16:
                pat &= 0xFC
                bits = vram[spg + pat * 8 + line] << 8 | \
                    vram[spg + pat * 8 + 16 + line]
            else:
                bits = vram[spg + pat * 8 + line]
            for b in range(size):
                if bits & (1 << (size - 1 - b)):
                    for m in range(mag):
                        px = x + b * mag + m
                        if 0 <= px < 256:
                            rows[y][px] = colour


def frame(vram, regs, limit=True, geometry=GEOMETRY):
    g = geometry
    back = regs[7] & 15
    out = [[back] * g['width'] for _ in range(g['height'])]
    for y, row in enumerate(indices(vram, regs, limit)):
        out[g['top'] + y][g['left']:g['left'] + 256] = \
            [c if c else back for c in row]
    return out


def png_bytes(rows, palette, scale=1):
    h, w = len(rows), len(rows[0])
    raw = bytearray()
    for row in rows:
        line = bytearray()
        for c in row:
            line += bytes(palette[c]) * scale
        for _ in range(scale):
            raw += b'\0' + line
    def chunk(tag, data):
        c = struct.pack('>I', len(data)) + tag + data
        return c + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
    head = struct.pack('>IIBBBBB', w * scale, h * scale, 8, 2, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', head)
            + chunk(b'IDAT', zlib.compress(bytes(raw), 9))
            + chunk(b'IEND', b''))


def read_png_rgb(path):
    """Pixels of an 8-bit RGB or RGBA PNG (openMSX screenshots)."""
    data = open(path, 'rb').read()
    pos, idat, w = 8, b'', 0
    while pos < len(data):
        n, tag = struct.unpack('>I4s', data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        if tag == b'IHDR':
            w, h, depth, ctype = struct.unpack('>IIBB', body[:10])
            bpp = {2: 3, 6: 4}[ctype]
        elif tag == b'IDAT':
            idat += body
        pos += 12 + n
    raw = zlib.decompress(idat)
    stride = w * bpp
    rows, prev = [], bytearray(stride)
    p = 0
    for _ in range(h):
        f = raw[p]
        line = bytearray(raw[p + 1:p + 1 + stride])
        p += 1 + stride
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if f == 1:
                line[i] = (line[i] + a) & 255
            elif f == 2:
                line[i] = (line[i] + b) & 255
            elif f == 3:
                line[i] = (line[i] + (a + b) // 2) & 255
            elif f == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if pa <= pb and pa <= pc else b if pb <= pc else c
                line[i] = (line[i] + pr) & 255
        rows.append([tuple(line[i:i + 3]) for i in range(0, stride, bpp)])
        prev = line
    return rows
