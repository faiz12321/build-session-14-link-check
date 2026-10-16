# Check the links in a web page file

A small read-only Python tool built step by step. Give it one HTML file and it lists the links (`<a href>`) it finds and reports links with an empty address, links to a file that is not in the page's folder, links to a `#place` that has no matching `id` on the same page, and `id` values used more than once. It does not use the network and has no code that writes to a file.

## Run it

    python make_sample.py                    # makes made-up pages in sample/
    python linkcheck.py sample/broken.html   # report on one page
    python -m unittest -v                    # 26 temporary-fixture tests

On Windows, if `python` is not found, use `py`.

## Files

- `linkcheck.py` - the tool
- `make_sample.py` - makes four made-up pages
- `test_linkcheck.py` - tests

## Setup safety and evidence

Setup refuses existing sample paths and exclusively writes four fictional HTML files in a new sample folder. It never resets or replaces old data. Start in a new empty lesson folder. Four setup collision/repeat tests preserve nested unrelated bytes and modification times. The checker is unchanged. It reads the complete source file and can follow source links. Relative target paths can leave the page folder; existence probes can follow links and do not prove a target is a regular readable file or a working browser link. Reports expose names and paths. Keep private output private.

Two Windows and two Ubuntu recordings pass all 26 tests. Each platform pair differs only in unittest time. Displays use first Windows output. The recorder writes exact visible first/final file versions in a unique temporary folder and removes only that folder. Setup itself refuses a repeat run. These limited checks do not prove all filesystems or sites.

## Notes

- Web addresses (http and https), other schemes such as `mailto:`, and addresses starting with `/` are counted but not checked. The tool never opens a web address, so it cannot tell you whether one still works.
- Only `<a href>` is read. Images, scripts, stylesheets and links added by JavaScript are not checked. A `<base>` tag is ignored.
- A link to a file is checked by asking whether that path exists. The part after `?` or `#` is ignored for that check, so a `#place` inside another page is not checked. Whether capital letters matter in file names can depend on the computer, so a link can be found on one machine and not another.
- `#place` links are compared with `id` values exactly, capitals included.
- An `<a>` tag with no `href` is not counted as a link. An `href` that is empty or has no value is reported.
- Python's HTML parser accepts invalid markup (https://docs.python.org/3/library/html.parser.html), so a page with broken HTML is read without complaint and the tool does not say the HTML is valid.
- The page must be UTF-8 text. Otherwise the tool says it could not read it.
- The tool counts every problem but shows only the first five examples of each kind.
- "No problems found by these checks" only means those checks passed.
- Tested only on small made-up pages, not on large or real-world sites. Python 3.10 (Linux) and, by GitHub Actions, Python 3.12 on Windows and Ubuntu. Not tested on a Windows 10 or 11 desktop.
- Educational example, no warranty. Use at your own risk.
- Code is MIT licensed (see LICENSE). Python is a separate project with its own license; this repository does not include it.
