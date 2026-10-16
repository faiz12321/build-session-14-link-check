"""Makes a small folder of made-up web pages to practise on.

Run: python make_sample.py
"""
import sys
from pathlib import Path

FILES = {
    "good.html": '<h1>Home</h1>\n<a href="about.html">About</a>\n'
                 '<a href="my%20notes.html">Notes</a>\n'
                 '<a href="#contact">Contact</a>\n'
                 '<a href="https://www.python.org/">Python</a>\n'
                 '<h2 id="contact">Contact</h2>\n',
    "broken.html": '<h1>Shop</h1>\n<a href="about.html">About</a>\n'
                   '<a href="prices.html">Prices</a>\n'
                   '<a href="#pricing">Pricing</a>\n'
                   '<a href="">Empty</a>\n'
                   '<h2 id="help">Help</h2>\n<h2 id="help">More help</h2>\n',
    "about.html": '<h1>About</h1>\n',
    "my notes.html": '<h1>Notes</h1>\n',
}


def make(folder):
    folder = Path(folder)
    folder.mkdir()
    for name, data in FILES.items():
        with (folder / name).open("xb") as handle:
            handle.write(data.encode("utf-8"))
    return folder


if __name__ == "__main__":
    try:
        make("sample")
    except FileExistsError:
        raise SystemExit("Stopped: sample already exists. Nothing was replaced or deleted.")
    print("Made sample/good.html, broken.html, about.html and my notes.html")
    sys.exit(0)
