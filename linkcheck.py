"""Reads one HTML file and reports its links. It does not change any file
and it does not use the network.

Run: python linkcheck.py PAGE.html
Exit code: 0 = no problems found by these checks, 1 = problems, 2 = could not read.
"""
import os
import sys
import stat
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

def safe_input(value, directory=False):
    path = Path(value).absolute()
    if '..' in path.parts:
        raise OSError('Parent-traversal paths are unsupported.')
    for part in [*reversed(path.parents), path]:
        info = part.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise OSError('Links/reparse points are unsupported.')
    info = path.lstat()
    if directory:
        if not stat.S_ISDIR(info.st_mode):
            raise NotADirectoryError('Expected an ordinary directory.')
    elif not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise OSError('Expected an ordinary singly linked file.')
    return path







SHOW = 5


class Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []   # (line, href or None)
        self.ids = []     # (line, id value)

    def handle_starttag(self, tag, attrs):
        line = self.getpos()[0]
        for name, value in attrs:
            if name == "id" and value:
                self.ids.append((line, value))
        if tag == "a":
            for name, value in attrs:
                if name == "href":
                    self.links.append((line, value))


def classify(href, folder):
    """Returns (kind, detail). Kinds: empty, top, anchor, web, other,
    rooted, file."""
    if href is None or href.strip() == "":
        return "empty", ""
    href = href.strip()
    if href == "#":
        return "top", ""
    if href.startswith("#"):
        return "anchor", unquote(href[1:])
    parts = urlsplit(href)
    if parts.scheme in ("http", "https"):
        return "web", href
    if parts.scheme or href.startswith("//"):
        return "other", href
    if href.startswith("/"):
        return "rooted", href
    path = unquote(parts.path)
    if path == "":
        return "top", ""
    return "file", os.path.join(folder, path)


def ordinary_target(value):
    # Existing ordinary directories keep their original found status; aliases refuse.
    path = Path(value).absolute()
    if '..' in path.parts:
        raise OSError('Parent-traversal targets are unsupported.')
    for part in [*reversed(path.parents), path]:
        info = part.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise OSError('Linked/reparse-point targets are unsupported.')
    if not stat.S_ISDIR(info.st_mode) and (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1):
        raise OSError('Expected an ordinary directory or singly linked file.')
    return True


def check(path):
    with open(safe_input(path), encoding="utf-8") as f:
        text = f.read()
    folder = os.path.dirname(os.path.abspath(path))
    parser = Collector()
    parser.feed(text)
    parser.close()
    ids = {}
    for line, value in parser.ids:
        ids.setdefault(value, []).append(line)
    result = {"links": len(parser.links), "web": 0, "other": 0, "rooted": 0,
              "ok": 0, "empty": [], "anchor_missing": [], "file_missing": [],
              "duplicate_ids": [(v, l) for v, l in ids.items() if len(l) > 1]}
    for line, href in parser.links:
        kind, detail = classify(href, folder)
        if kind == "empty":
            result["empty"].append(line)
        elif kind in ("web", "other", "rooted"):
            result[kind] += 1
        elif kind == "anchor" and detail not in ids:
            result["anchor_missing"].append((line, "#" + detail))
        elif kind == "file":
            try:
                ordinary_target(detail)
            except FileNotFoundError:
                result["file_missing"].append((line, os.path.relpath(detail, folder)))
            else:
                result["ok"] += 1
        else:
            result["ok"] += 1
    return result


def report(r):
    print("Links found:", r["links"])
    print("Checked and found:", r["ok"])
    print("Not checked (web addresses, no network used):", r["web"])
    print("Not checked (other schemes such as mailto:):", r["other"])
    print("Not checked (start with /, depends on the site root):", r["rooted"])
    problems = 0
    groups = [("Links with an empty address", [(l, "") for l in r["empty"]]),
              ("Links to a missing place on this page", r["anchor_missing"]),
              ("Links to a missing file", r["file_missing"]),
              ("Repeated id values", [(l[0], v + " (lines " + ", ".join(map(str, l)) + ")") for v, l in r["duplicate_ids"]])]
    for title, items in groups:
        if items:
            problems += len(items)
            print(f"{title}: {len(items)}")
            for line, what in items[:SHOW]:
                print(f"  line {line}: {what}".rstrip())
            if len(items) > SHOW:
                print(f"  ... and {len(items) - SHOW} more")
    if problems == 0:
        print("No problems found by these checks.")
    return 1 if problems else 0


def main(argv):
    if len(argv) != 2:
        print("Usage: python linkcheck.py PAGE.html")
        return 2
    try:
        result = check(argv[1])
    except (OSError, UnicodeDecodeError) as e:
        print("Could not read the file as UTF-8 text:", e)
        return 2
    return report(result)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
