"""Check the package of Cryptmorrow MSX byte for byte.

Usage: python verify.py [--sjasmplus PATH] [--pasmo PATH] [--keep]
                        [--files-only] [NAME ...]

1. Every file listed in SHA256SUMS.txt is present and unchanged. A file
   you have edited for an experiment is named here: that is expected.
2. Every cartridge of the package is built again in a temporary folder,
   by its own tools/build_game.py, as chapter 1 of the book builds it:
   game/assets/build_msx.py and game/assets/psg_music.py make the data
   again and the build checks it against game/assets/generated/B,
   tools/check_lines.py checks that no line is longer than 60
   characters, sjasmplus assembles game/src/cryptmorrow.asm (pasmo
   too, if it is given: it must give the same bytes). The cartridge
   must be the reference one, byte for byte:
       game                    releases/cryptmorrow-msx-1.0.rom
       chain/NN-name           reference/chain/NN-name.rom
       variants/NN-name/ID     reference/variants/ID.rom
   Where the build also makes the tests' cartridges and the cartridges
   of the 16 rooms (the complete game, steps 07 and 08: 20 in all),
   every one of them must be the one chain/chain.json records for the
   step (for game/, those of step 08). The report of a variant's test
   (variants/NN-name/ID/evidence/*.json) must name the same cartridge:
   what was tested is what is shipped.
3. The probe of fase0/ (the program the test of the palettes runs in
   openMSX), assembled again: fase0/build/probe.rom.
4. Every cartridge of the package: 32 768 bytes, starting with "AB" and
   the address of INIT in page 1 (#4010 to #7FFF), the other twelve
   bytes of the header 0; the release is the cartridge of step 08.

NAME limits the builds to the folders whose path contains it, for
example `chain/03` or `05b`. --files-only does 1 and 4 only, without
sjasmplus. Nothing in the package is changed; the temporary folder is
deleted at the end unless --keep is given.

Needs Python 3.10 or later, standard library only, and sjasmplus on
the PATH or given with --sjasmplus. The reference cartridges were made
with sjasmplus 1.24.0; another version may not give the same bytes.
Exit status 0 when everything matches, 1 when something does not.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
RELEASE = ROOT / "releases/cryptmorrow-msx-1.0.rom"
LAST_STEP = "08-complete"
ROM_SIZE = 32768
SKIP = shutil.ignore_patterns("build", "evidence", "__pycache__",
                              "*.pyc", "*.log")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def check_sums():
    """Files of SHA256SUMS.txt that are missing or changed."""
    problems, count = [], 0
    for line in (ROOT / "SHA256SUMS.txt").read_text(
            encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split(maxsplit=1)
        name = name.lstrip("*")
        count += 1
        path = ROOT / name
        if not path.is_file():
            problems.append(f"missing: {name}")
        elif sha256(path.read_bytes()) != digest:
            problems.append(f"changed: {name}")
    return count, problems


def chain_roms():
    """step folder name -> {cartridge: SHA-256} (chain/chain.json)."""
    steps = json.loads((ROOT / "chain/chain.json").read_text(
        encoding="utf-8"))["steps"]
    return {name: step["roms"] for name, step in steps.items()}


def programs():
    """(folder, reference cartridge, the cartridges of chain.json or
    None, reports folder) of every program of the package."""
    roms = chain_roms()
    found = [(ROOT / "game", RELEASE, roms[LAST_STEP], None)]
    for step in sorted((ROOT / "chain").glob("[0-9][0-9]-*")):
        found.append((step, ROOT / "reference/chain" / f"{step.name}.rom",
                      roms[step.name], None))
    for variant in sorted((ROOT / "variants").glob("[0-9][0-9]-*/*")):
        if variant.is_dir():
            found.append((variant,
                          ROOT / "reference/variants" / f"{variant.name}.rom",
                          None, variant / "evidence"))
    return found


def run(command, folder):
    result = subprocess.run(command, cwd=folder, capture_output=True,
                            text=True)
    return result.returncode, (result.stdout + result.stderr).strip()


def build(folder, work, tools):
    """Build one folder in `work`; returns ({name: bytes}, problems)."""
    if folder == ROOT / "game":
        # The master source: built by the tools of the root.
        shutil.copytree(folder, work / "game", ignore=SKIP)
        shutil.copytree(ROOT / "tools", work / "tools", ignore=SKIP)
    else:
        shutil.copytree(folder, work, ignore=SKIP)
    status, output = run([sys.executable, "tools/build_game.py"] + tools,
                         work)
    if status:
        last = output.splitlines()[-3:] if output else []
        return None, ["build failed: " + " / ".join(last)]
    made = work / "game/build"
    found = {p.relative_to(made).with_suffix("").as_posix(): p.read_bytes()
             for p in made.rglob("*.rom")}
    return found, []


def compare(made, reference, what):
    """None if the two are the same, or where they differ."""
    if made == reference:
        return None
    for offset, (x, y) in enumerate(zip(made, reference)):
        if x != y:
            return (f"{what}: byte {offset} differs (#{x:02X}, reference "
                    f"#{y:02X})")
    return f"{what}: {len(made)} bytes, reference {len(reference)}"


def tested(reports, rom):
    """Reports of a variant's tests that name another cartridge; and
    how many reports there are."""
    problems, count = [], 0
    if reports is None or not reports.is_dir():
        return problems, count
    for report in sorted(reports.glob("*.json")):
        count += 1
        facts = json.loads(report.read_text(encoding="utf-8")).get(
            "facts", {})
        named = facts.get("cartridge") if report.name == \
            "verify_step.json" else facts.get("build", {}).get(
                "cryptmorrow")
        if not isinstance(named, str) or not sha256(rom).startswith(named):
            problems.append(f"{report.relative_to(ROOT).as_posix()} "
                            f"tested another cartridge ({named})")
    return problems, count


def header(rom):
    """None if the cartridge is right, or what is wrong."""
    if len(rom) != ROM_SIZE:
        return f"{len(rom)} bytes, not {ROM_SIZE}"
    if rom[:2] != b"AB":
        return "it does not start with AB"
    init = rom[2] | rom[3] << 8
    if not 0x4010 <= init < 0x8000:
        return f"INIT #{init:04X} is not in page 1 after the header"
    if any(rom[4:16]):
        return "the other twelve bytes of the header are not 0"
    return None


def probe(sjasmplus, work):
    """fase0/src/probe.asm assembled again: None or what differs."""
    shutil.copytree(ROOT / "fase0/src", work / "src")
    status, output = run([sjasmplus, "--nologo", "--msg=war",
                          "-DBROKEN=0", "-DIRQMODE=0", "--raw=probe.rom",
                          "--sym=probe.sym", "src/probe.asm"], work)
    if status or output:
        return f"sjasmplus: {output.splitlines()[-1] if output else status}"
    return compare((work / "probe.rom").read_bytes(),
                   (ROOT / "fase0/build/probe.rom").read_bytes(), "rom")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("names", nargs="*")
    parser.add_argument("--sjasmplus", default=None,
                        help="sjasmplus, if it is not on the PATH")
    parser.add_argument("--pasmo", default=None,
                        help="pasmo, to compare its bytes as well")
    parser.add_argument("--keep", action="store_true",
                        help="keep the temporary folder")
    parser.add_argument("--files-only", action="store_true",
                        help="only the files and the cartridges, no builds")
    args = parser.parse_args()
    sjasmplus = None
    if not args.files_only:
        sjasmplus = args.sjasmplus or shutil.which("sjasmplus")
        if not sjasmplus:
            sys.exit("sjasmplus is not on the PATH: add its folder to the "
                     "PATH, give it with --sjasmplus, or use --files-only.")
        status, version = run([sjasmplus, "--version"], ROOT)
        version = next((line for line in version.splitlines()
                        if "sjasmplus" in line.lower()), sjasmplus)
        print(f"Python {sys.version.split()[0]}; {version.strip()}")
    failures = 0

    count, problems = check_sums()
    print(f"\nSHA256SUMS.txt: {count} files, "
          f"{'all unchanged' if not problems else f'{len(problems)} not'}")
    for line in problems:
        print("  " + line)
    failures += len(problems)

    selected = [entry for entry in programs()
                if not args.names or any(
                    n in entry[0].relative_to(ROOT).as_posix()
                    for n in args.names)]
    if not args.files_only:
        tools = [f"--sjasmplus={sjasmplus}"]
        if args.pasmo:
            tools.append(f"--pasmo={args.pasmo}")
        print(f"\nPrograms built again and compared: {len(selected)}")
        scratch = Path(tempfile.mkdtemp(prefix="cryptmorrow-msx-verify-"))
        names = [f.relative_to(ROOT).as_posix() for f, _, _, _ in selected]
        same, reports, cartridges = 0, 0, 0
        width = max([len(n) for n in names] + [4])
        try:
            for number, (folder, reference, roms, evidence) in enumerate(
                    selected):
                name = folder.relative_to(ROOT).as_posix()
                made, problems = build(folder, scratch / f"{number:02d}",
                                       tools)
                if made is not None:
                    rom = made.get("cryptmorrow", b"")
                    if not reference.is_file():
                        problems.append(
                            f"no reference {reference.relative_to(ROOT)}")
                    else:
                        difference = compare(rom, reference.read_bytes(),
                                             "cryptmorrow.rom")
                        if difference:
                            problems.append(difference)
                    if roms is not None:
                        if sorted(made) != sorted(roms):
                            problems.append(f"{len(made)} cartridges made, "
                                            f"chain.json has {len(roms)}")
                        problems += [f"{k}.rom differs from chain.json"
                                     for k in sorted(roms)
                                     if k in made and
                                     sha256(made[k]) != roms[k]]
                    wrong, counted = tested(evidence, rom)
                    problems += wrong
                    reports += counted
                    cartridges += len(made)
                if made is not None and not problems:
                    same += 1
                    extra = f"  + {len(made) - 1} more" if len(made) > 1 \
                        else ""
                    print(f"  {name:{width}}  {sha256(rom)[:16]}  same"
                          f"{extra}", flush=True)
                else:
                    print(f"  {name:{width}}  DIFFERENT", flush=True)
                    for line in problems:
                        print("      " + line)
                    failures += 1
            if not args.names:
                difference = probe(sjasmplus, scratch / "probe")
                print(f"  fase0/build/probe.rom: "
                      f"{'same' if not difference else difference}")
                failures += bool(difference)
        finally:
            if args.keep:
                print(f"\nThe builds are in {scratch}")
            else:
                shutil.rmtree(scratch, ignore_errors=True)
        print(f"  {same} of {len(selected)} identical to their reference "
              f"({cartridges} cartridges built); test reports checked: "
              f"{reports}")

    print("\nCartridges of the package:")
    roms = sorted((ROOT / "reference").rglob("*.rom")) + [RELEASE]
    wrong = 0
    for path in roms:
        problem = header(path.read_bytes())
        if problem:
            wrong += 1
            print(f"  {path.relative_to(ROOT).as_posix()}: {problem}")
    last = ROOT / "reference/chain" / f"{LAST_STEP}.rom"
    same = last.read_bytes() == RELEASE.read_bytes()
    if not same:
        wrong += 1
    print(f"  {len(roms) - wrong} of {len(roms)} right; the release is the "
          f"cartridge of step 08: {'yes' if same else 'NO'}")
    failures += wrong

    print("\nResult:", "PASS" if not failures else f"FAIL ({failures})")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
