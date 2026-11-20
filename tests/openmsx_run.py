"""openMSX driven by a Tcl script: the reader's emulator in the tests.

run(rom, machine, sym, ...) starts openMSX (-machine, -cart, -script)
with a script written here, and returns what it saw:

  at INIT       (the first instruction of the cartridge) the BIOS state
                the bench starts from: RAM of page 3, VRAM, VDP, PSG,
                PPI and CPU registers, slots, EmuTime; with a seed, RAM
                #C000-#F37F and VRAM are then filled with the bytes of
                msxsim.random_fill(seed), as the bench does;
  frame_ready   every time the program gets there: RAM #C000-#F37F,
                VRAM, VDP and PSG registers, the time (T-states from
                INIT); a screenshot (-raw, 320 x 240) at the frames
                asked for, taken two frames later as well; for a long
                run (milestone 0.4: 29 KB a frame, 270 MB for the
                whole game) read_run can hand the frames back one at a
                time from the file (lazy=True);
  interrupts    the time of every rise of the VDP's interrupt line
                (probe VDP.IRQvertical) and of every interrupt taken
                (probe z80.acceptIRQ);
  marks         the time of chosen labels (to count T-states between
                two of them);
  too fast      every VRAM access openMSX dropped (callback of the
                setting too_fast_vram_access = real);
  PSG port      every write of register 7 with port A as an output
                (invalid_psg_directions_callback): the C-BIOS machines
                of openMSX ignore it (ignorePortDirections), some real
                MSX do not;
  PSG writes    (milestone 0.6, psg_log=True) every write to the PSG:
                time, register, value (watchpoints on ports #A0 and
                #A1);
  sound         (milestone 0.6, wav=(file, k)) what openMSX plays,
                recorded from frame_ready k (0: from INIT) to the end
                of the run (record -audioonly: 44 100 Hz, mono).

The input: keys of keyboard row 8 by keymatrixdown/keymatrixup, given
at frame_ready of the frame before (as the bench does); so are the
pokes (milestone 0.4: a byte of RAM put there by the test, as the
bench does, for what the game cannot do yet). The joystick
has no command in openMSX 21.0: the test gives it where the program
reads it, setting bits 0-5 of A right after IN A,(#A2) when register
15 selects port 1 and register 7 makes port A an input (an aid of the
test, declared in the report). Without a joystick the port reads as
an empty one.

Screenshots need a renderer: throttle on (real time) and a display
(Xvfb in the workspace). Without screenshots the run is headless
(renderer none, throttle off).
"""
import json
import os
import struct
import subprocess
import tempfile
from pathlib import Path

CLOCK = 3579545
RAM_LO, RAM_N = 0xC000, 0x3380          # #C000-#F37F
FRAME_REC = RAM_N + 0x4000 + 8 + 16 + 1 + 1 + 8

TCL = r'''
set renderer {renderer}
set throttle {throttle}
set minframeskip 0
set maxframeskip 0
set limitsprites on
set too_fast_vram_access real
set ::out {out}
after time {max_seconds} {{ puts $::ev "timeout"; {stop}close $::fr; close $::ev; exit }}
set ::n 0
set ::t0 0
set ::fr [open [file join $::out frames.bin] wb]
fconfigure $::fr -translation binary
set ::ev [open [file join $::out events.txt] w]
proc T {{}} {{ return [expr {{round(([machine_info time] - $::t0) * {clock})}}] }}
proc wbin {{name data}} {{
  set f [open [file join $::out $name] wb]
  fconfigure $f -translation binary
  puts -nonewline $f $data
  close $f
}}
proc rbin {{name}} {{
  set f [open $name rb]
  fconfigure $f -translation binary
  set d [read $f]
  close $f
  return $d
}}
proc regs8 {{deb n}} {{
  set s ""
  for {{set i 0}} {{$i < $n}} {{incr i}} {{
    append s [binary format c [debug read $deb $i]]
  }}
  return $s
}}
set VDP.too_fast_vram_access_callback too_fast
proc too_fast {{args}} {{ puts $::ev "toofast [T] [reg PC]" }}
set invalid_psg_directions_callback psg_dir
proc psg_dir {{args}} {{ puts $::ev "psgdir [T] [reg PC]" }}
debug set_bp {init} {{$::n == 0}} {{
  set ::t0 [machine_info time]
  wbin init_ram.bin [debug read_block memory 0xC000 0x4000]
  wbin init_vram.bin [debug read_block VRAM 0 0x4000]
  wbin init_vdp.bin [regs8 {{VDP regs}} 8]
  wbin init_psg.bin [regs8 {{PSG regs}} 16]
  set rr ""
  foreach r {{AF BC DE HL IX IY AF2 BC2 DE2 HL2 I R}} {{ append rr " $r=[reg $r]" }}
  puts $::ev "regs$rr"
  puts $::ev "init a8=[debug read ioports 0xA8] aa=[debug read ioports 0xAA] sp=[reg SP] im=[reg IM] iff=[reg IFF] status=[debug read {{VDP status regs}} 0] latch=[debug read {{VDP register latch status}} 0] pointer=[debug read {{VRAM pointer}} 0] [debug read {{VRAM pointer}} 1]"
  {fill}
  {record0}
  set ::n 1
}}
debug probe set_bp VDP.IRQvertical {{[debug probe read VDP.IRQvertical] == 1}} {{
  if {{$::n > 0}} {{ puts $::ev "vbl [T]" }}
}}
debug probe set_bp z80.acceptIRQ {{}} {{
  if {{$::n > 0}} {{ puts $::ev "irq [T]" }}
}}
{marks}
{joy}
{psg}
debug set_bp {frame_ready} {{$::n > 0}} {{
  set k $::n
  puts -nonewline $::fr [debug read_block memory 0xC000 {ram_n}]
  puts -nonewline $::fr [debug read_block VRAM 0 0x4000]
  puts -nonewline $::fr [regs8 {{VDP regs}} 8]
  puts -nonewline $::fr [regs8 {{PSG regs}} 16]
  puts -nonewline $::fr [binary format c [debug read {{VDP status regs}} 0]]
  puts -nonewline $::fr [binary format c [debug read ioports 0xA8]]
  puts -nonewline $::fr [binary format w [T]]
  {shots}
  {inputs}
  {record}
  incr ::n
  if {{$k >= {frames}}} {{ {stop}close $::fr; close $::ev; exit }}
}}
'''


def tcl_quote(path):
    return '{' + str(path).replace('\\', '/') + '}'


def find_in(rom, org, start, pattern, span=256):
    """Address of the first `pattern` (bytes) at or after `start`."""
    off = start - org
    i = rom.find(bytes(pattern), off, off + span)
    if i < 0:
        raise ValueError(f'{bytes(pattern).hex()} not found after '
                         f'${start:04X}')
    return org + i


def run(openmsx, rom_path, machine, sym, frames, out, seed=None,
        inputs=None, shots=(), marks=(), joy_read=None, timeout=600,
        env=None, max_seconds=None, pokes=None, lazy=False,
        psg_log=False, wav=None, joy_port=1):
    """Run the cartridge to frame_ready number `frames`.

    inputs   {frame: (keys, joy)}: from frame_ready k on (keys of
             msxsim.ROW8, joystick directions of msxsim.JOY)
    shots    frames at whose frame_ready a screenshot is taken
             (shot_K.png and, two frames later, shot_K+2.png)
    marks    labels whose times are written (mark NAME T)
    joy_read address right after IN A,(#A2), for the joystick
    joy_port the port the joystick is given in (1, or 2: register 15
             bit 6 set)
    pokes    {frame: [(address, value)]}: written in RAM before
             frame k (at frame_ready k - 1)
    lazy     the frames read from the file one at a time (a
             generator), not all at once
    psg_log  every write to the PSG (res['psg_writes'])
    wav      (file, k): the sound from frame_ready k (0: from INIT)
             to the end (res['wav_from']: the time it starts)
    """
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob('*'):
        if f.is_file():
            f.unlink()
    fill = ''
    if seed is not None:
        import msxsim
        rnd = msxsim.random_fill(seed)
        (out / 'fill_ram.bin').write_bytes(rnd['ram'])
        (out / 'fill_vram.bin').write_bytes(rnd['vram'])
        fill = ('debug write_block memory 0xC000 [rbin '
                + tcl_quote(out / 'fill_ram.bin') + ']\n  '
                'debug write_block VRAM 0 [rbin '
                + tcl_quote(out / 'fill_vram.bin') + ']')
    mark_tcl = '\n'.join(
        f'debug set_bp {sym[m]} {{$::n > 0}} '
        f'{{ puts $::ev "mark {m} [T]" }}' for m in marks)
    joy_tcl = ''
    inputs = inputs or {}
    if joy_read is not None:
        joy_tcl = (f'set ::joy 63\n'
                   f'debug set_bp {joy_read} {{$::n > 0}} {{\n'
                   '  if {([debug read {PSG regs} 15] & 0x40) == '
                   f'{0x40 if joy_port == 2 else 0} && '
                   '([debug read {PSG regs} 7] & 0x40) == 0} {\n'
                   '    reg A [expr {([reg A] & 0xC0) | $::joy}]\n'
                   '  }\n}')
    shot_tcl = ''
    for k in sorted(shots):
        for kk in (k, k + 2):
            name = tcl_quote(out / f'shot_{kk}.png')
            vr = f'shotvram_{kk}.bin'
            shot_tcl += (f'if {{$k == {kk}}} {{ screenshot -raw {name}; '
                         f'wbin {vr} [debug read_block VRAM 0 0x4000]; '
                         f'wbin shotregs_{kk}.bin [regs8 {{VDP regs}} 8] }}\n  ')
    in_tcl = ''
    import msxsim
    prev_keys = 0
    for k in sorted(inputs):
        keys, joy = inputs[k]
        mask = 0
        for key in keys:
            mask |= 1 << msxsim.ROW8[key]
        jbits = 0x3F
        for j in joy:
            jbits &= ~(1 << msxsim.JOY[j])
        cmds = []
        down, up = mask & ~prev_keys, prev_keys & ~mask
        if down:
            cmds.append(f'keymatrixdown 8 {down}')
        if up:
            cmds.append(f'keymatrixup 8 {up}')
        cmds.append(f'set ::joy {jbits}')
        in_tcl += f'if {{$k == {k - 1}}} {{ {"; ".join(cmds)} }}\n  '
        prev_keys = mask
    for k in sorted(pokes or {}):
        cmds = [f'debug write memory {a} {v}' for a, v in pokes[k]]
        in_tcl += f'if {{$k == {k - 1}}} {{ {"; ".join(cmds)} }}\n  '
    psg_tcl = ''
    if psg_log:
        psg_tcl = ('set ::psgr 0\n'
                   'debug set_watchpoint write_io 0xA0 {$::n > 0} '
                   '{ set ::psgr $::wp_last_value }\n'
                   'debug set_watchpoint write_io 0xA1 {$::n > 0} '
                   '{ puts $::ev "pw [T] $::psgr $::wp_last_value" }')
    rec0 = rec = stop = ''
    if wav is not None:
        start = (f'record start -audioonly {tcl_quote(wav[0])}; '
                 'puts $::ev "wav [T]"')
        if wav[1] == 0:
            rec0 = start
        else:
            rec = f'if {{$k == {wav[1]}}} {{ {start} }}'
        stop = 'catch {record stop}; '
    script = TCL.format(
        renderer='SDLGL-PP' if shots else 'none',
        throttle='on' if shots else 'off',
        out=tcl_quote(out), clock=CLOCK, init=sym['init'],
        fill=fill, marks=mark_tcl, joy=joy_tcl,
        frame_ready=sym['frame_ready'], ram_n=RAM_N, shots=shot_tcl,
        inputs=in_tcl, frames=frames, psg=psg_tcl, record0=rec0,
        record=rec, stop=stop,
        max_seconds=max_seconds or round(4 + frames * 0.03, 2))
    (out / 'run.tcl').write_text(script, encoding='utf-8')
    cmd = [openmsx, '-machine', machine, '-cart', str(rom_path),
           '-script', str(out / 'run.tcl')]
    if shots and os.name != 'nt' and not os.environ.get('DISPLAY'):
        cmd = ['xvfb-run', '-a', '-s', '-screen 0 1024x768x24'] + cmd
    e = dict(os.environ, **(env or {}))
    p = subprocess.run(cmd, capture_output=True, text=True,
                       timeout=timeout, env=e)
    (out / 'openmsx.log').write_text(p.stdout + p.stderr,
                                     encoding='utf-8')
    return read_run(out, lazy)


def frame_records(path):
    """The records of frames.bin, one at a time."""
    with open(path, 'rb') as f:
        while True:
            r = f.read(FRAME_REC)
            if len(r) < FRAME_REC:
                return
            p = 0
            ram = r[p:p + RAM_N]; p += RAM_N
            vram = r[p:p + 0x4000]; p += 0x4000
            vdp = list(r[p:p + 8]); p += 8
            psg = list(r[p:p + 16]); p += 16
            status = r[p]; p += 1
            a8 = r[p]; p += 1
            t = struct.unpack('<q', r[p:p + 8])[0]
            yield {'ram': ram, 'vram': vram, 'vdp': vdp, 'psg': psg,
                   'status': status, 'a8': a8, 't': t}


def read_run(out, lazy=False):
    out = Path(out)
    res = {'frames': [], 'vbl': [], 'irq': [], 'marks': [],
           'too_fast': [], 'init': {}, 'psg_directions': [],
           'psg_writes': [], 'wav_from': None}
    frames = frame_records(out / 'frames.bin')
    res['frames'] = frames if lazy else list(frames)
    for line in (out / 'events.txt').read_text().splitlines():
        w = line.split()
        if w[0] == 'vbl':
            res['vbl'].append(int(w[1]))
        elif w[0] == 'irq':
            res['irq'].append(int(w[1]))
        elif w[0] == 'pw':
            res['psg_writes'].append((int(w[1]), int(w[2]),
                                      int(w[3])))
        elif w[0] == 'wav':
            res['wav_from'] = int(w[1])
        elif w[0] == 'mark':
            res['marks'].append((w[1], int(w[2])))
        elif w[0] == 'regs':
            res['init']['regs'] = {kv.split('=')[0]: int(kv.split('=')[1])
                                   for kv in w[1:]}
        elif w[0] == 'psgdir':
            res.setdefault('psg_directions', []).append(
                (int(w[1]), int(w[2])))
        elif w[0] == 'timeout':
            res['timeout'] = True
        elif w[0] == 'toofast':
            res['too_fast'].append((int(w[1]), int(w[2])))
        elif w[0] == 'init':
            for kv in w[1:]:
                if '=' in kv:
                    k, v = kv.split('=')
                    res['init'][k] = int(v)
            res['init']['pointer_hi'] = int(w[-1])
    return res


def cbios_state(run_dir, rom_init, hz, frame_t):
    """The state the bench starts from, from a run without a seed."""
    out = Path(run_dir)
    r = read_run(out)
    ini = r['init']
    # The probe of the IRQ line is seen at an instruction boundary,
    # up to one HALT cycle (5 T-states) late: the line rose at the
    # earliest of the times brought back into one frame.
    vbl = [v for v in r['vbl'] if v > 0]
    first = min(v % frame_t for v in vbl[1:]) if len(vbl) > 2 \
        else None
    return {
        'hz': hz, 'init': rom_init,
        'ram_c000': (out / 'init_ram.bin').read_bytes().hex(),
        'vram': (out / 'init_vram.bin').read_bytes().hex(),
        'vdp_regs': list((out / 'init_vdp.bin').read_bytes()),
        'vdp_status': ini['status'],
        'psg': list((out / 'init_psg.bin').read_bytes()),
        'a8': ini['a8'], 'ppi_c': ini['aa'], 'sp': ini['sp'],
        'im': ini['im'], 'iff': ini['iff'], 'regs': ini['regs'],
        'vbl_after_init': first,
        'vbl_seen': vbl[:4],
    }
