"""Check that assembly lines fit the book: at most 60 characters.

A tab counts up to the next multiple of 8, as in the listings. Prints
every long line and exits with 1 if there is one. The tags of the
chain of the book (tools/make_chain.py, Phase D) do not count: a line
is measured as the complete game shows it.

Usage: python tools/check_lines.py FILE [FILE...]
"""
import re
import sys

LIMIT = 60
TAG = re.compile(r'\s*\{\d*-?\d*\}$')
BLOCK = re.compile(r'^;\{\d*-?\d*\}$')


def width(line):
    col = 0
    for ch in line:
        col = (col // 8 + 1) * 8 if ch == '\t' else col + 1
    return col


def shown(line):
    """The line as the complete game shows it, or None for a line of
    earlier steps only (;|) or a block mark (;{3} ... ;{})."""
    if line.startswith(';|') or line == ';{}' or BLOCK.match(line):
        return None
    tag = TAG.search(line)
    if tag:
        line = line[:tag.start()].rstrip()
        if line.endswith(';') and line.strip() != ';':
            line = line[:-1].rstrip()
    return line


def long_lines(path):
    out = []
    with open(path, encoding='ascii') as f:
        for n, line in enumerate(f, 1):
            line = shown(line.rstrip('\r\n'))
            w = width(line) if line is not None else 0
            if w > LIMIT:
                out.append((str(path), n, w))
    return out


def main(paths):
    bad = []
    for p in paths:
        bad += long_lines(p)
    for p, n, w in bad:
        print(f'{p}:{n}: {w} characters (limit {LIMIT})')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
