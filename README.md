# Check links in a fictional HTML file

Save three source files in a NEW empty lesson folder.

    python make_sample.py
    python linkcheck.py sample/broken.html
    python -m unittest -v

Two Windows and two Ubuntu full replays run exact visible source versions. Final 46 small fixture tests pass (two Unix-pipe checks skip on Windows); symlink creation can skip where unavailable. Displayed stdout is first Windows output, not normalized or mixed. Pair differences are unittest time.
Only link/error changes: final reader refuses input/ancestor symbolic links/reparse points, hardlinks, special files and traversal. Local href targets refuse these aliases and traversal too; metadata or unsupported-target errors return 2 instead of counting aliases found. Ordinary missing targets remain exit-1 reported problems, while existing ordinary directories retain their original found status. Target contents are not read. Setup refuses linked parents/traversal and existing sample paths, without reset or deletion. Naive first version remains fictional-sample-only.
Original HTML parsing, id matching, classifications, missing-file reports and ordinary-file/folder existence rules remain unchanged. Web, other-scheme and site-root links remain unverified. Exits remain 0 no reported problems, 1 reported problems, 2 read/metadata errors. A pass is not browser rendering, HTML validity, URL safety or website availability proof.
The checker has no write/move/delete/network code, but reads the whole input into memory. No size/time/resource limit, atomic snapshot or hostile-race defense. Stop editors/sync. Paths, hrefs and ids can be private. Small fictional fixtures are not proof on every filesystem. No desktop Windows/macOS recording. Recorder removes only its own temporary fixture folder. Decisions and feedback are teaching text, not recorded output.

MIT code. Python separately licensed/not included.

Reference: https://docs.python.org/3/library/os.html

Windows pair: https://github.com/faiz12321/lesson-lab/actions/runs/38973017224
Ubuntu pair: https://github.com/faiz12321/lesson-lab/actions/runs/38973096039
