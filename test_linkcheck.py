import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import linkcheck
import make_sample


def run_on(text, extra_files=()):
    with tempfile.TemporaryDirectory() as d:
        for name in extra_files:
            Path(d, name).write_bytes(b"x")
        page = Path(d, "page.html")
        page.write_bytes(text.encode("utf-8"))
        return linkcheck.check(str(page))


class CheckTests(unittest.TestCase):
    def test_existing_file_is_found(self):
        r = run_on('<a href="a.html">x</a>', ["a.html"])
        self.assertEqual((r["links"], r["ok"], r["file_missing"]), (1, 1, []))

    def test_missing_file_is_reported_with_line(self):
        r = run_on('<p>\n<a href="gone.html">x</a>')
        self.assertEqual(r["file_missing"], [(2, "gone.html")])

    def test_percent_encoded_name(self):
        r = run_on('<a href="my%20page.html">x</a>', ["my page.html"])
        self.assertEqual(r["ok"], 1)

    def test_query_and_fragment_ignored_for_file_check(self):
        r = run_on('<a href="a.html?x=1#top">x</a>', ["a.html"])
        self.assertEqual(r["ok"], 1)

    def test_anchor_found_and_missing(self):
        r = run_on('<a href="#a">x</a><a href="#b">y</a><p id="a">')
        self.assertEqual((r["ok"], r["anchor_missing"]), (1, [(1, "#b")]))

    def test_bare_hash_is_fine(self):
        r = run_on('<a href="#">x</a>')
        self.assertEqual((r["ok"], r["anchor_missing"]), (1, []))

    def test_anchor_match_is_exact_case(self):
        r = run_on('<a href="#Top">x</a><p id="top">')
        self.assertEqual(len(r["anchor_missing"]), 1)

    def test_empty_and_valueless_href(self):
        r = run_on('<a href="">x</a><a href="  ">y</a><a href>z</a>')
        self.assertEqual(len(r["empty"]), 3)

    def test_anchor_tag_without_href_is_not_a_link(self):
        r = run_on('<a name="x">y</a>')
        self.assertEqual(r["links"], 0)

    def test_web_and_other_schemes_not_checked(self):
        r = run_on('<a href="http://a.test/">1</a><a href="https://a.test/">2</a>'
                   '<a href="mailto:a@b.test">3</a><a href="tel:123">4</a>')
        self.assertEqual((r["web"], r["other"], r["ok"]), (2, 2, 0))

    def test_rooted_and_scheme_relative_paths(self):
        r = run_on('<a href="/docs/a.html">x</a><a href="//cdn.test/a">y</a>')
        self.assertEqual((r["rooted"], r["other"], r["file_missing"]), (1, 1, []))

    def test_uppercase_tag_and_attribute(self):
        r = run_on('<A HREF="gone.html">x</A>')
        self.assertEqual(len(r["file_missing"]), 1)

    def test_link_inside_comment_is_ignored(self):
        r = run_on('<!-- <a href="gone.html">x</a> -->')
        self.assertEqual(r["links"], 0)

    def test_duplicate_ids_reported_with_lines(self):
        r = run_on('<p id="a">\n<p id="a">\n<p id="b">')
        self.assertEqual(r["duplicate_ids"], [("a", [1, 2])])

    def test_folder_link_counts_as_found(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "sub").mkdir()
            Path(d, "page.html").write_text('<a href="sub/">x</a>')
            self.assertEqual(linkcheck.check(str(Path(d, "page.html")))["ok"], 1)


class ReportTests(unittest.TestCase):
    def run_main(self, args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = linkcheck.main(["linkcheck.py"] + args)
        return rc, buf.getvalue()

    def test_clean_page_exit_zero(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "page.html").write_text("<p>hello</p>")
            rc, out = self.run_main([str(Path(d, "page.html"))])
        self.assertEqual(rc, 0)
        self.assertIn("No problems found by these checks.", out)

    def test_only_first_five_shown_with_total(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "page.html").write_text("".join(f'<a href="m{i}.html">x</a>' for i in range(8)))
            rc, out = self.run_main([str(Path(d, "page.html"))])
        self.assertEqual(rc, 1)
        self.assertIn("Links to a missing file: 8", out)
        self.assertIn("... and 3 more", out)

    def test_missing_page_exit_two(self):
        rc, out = self.run_main(["no-such-page.html"])
        self.assertEqual(rc, 2)

    def test_not_utf8_exit_two(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "page.html").write_bytes(b"<p>\xff\xfe</p>")
            rc, out = self.run_main([str(Path(d, "page.html"))])
        self.assertEqual(rc, 2)

    def test_wrong_arguments_exit_two(self):
        rc, out = self.run_main([])
        self.assertEqual(rc, 2)


class SampleTests(unittest.TestCase):
    def test_sample_files_report_as_described(self):
        with tempfile.TemporaryDirectory() as d:
            folder = make_sample.make(Path(d, "sample"))
            good = linkcheck.check(str(folder / "good.html"))
            bad = linkcheck.check(str(folder / "broken.html"))
        self.assertEqual((good["links"], good["ok"], good["web"]), (4, 3, 1))
        self.assertEqual(len(bad["file_missing"]), 1)
        self.assertEqual(len(bad["anchor_missing"]), 1)
        self.assertEqual(len(bad["empty"]), 1)
        self.assertEqual(len(bad["duplicate_ids"]), 1)

    def test_checking_does_not_change_the_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "page.html")
            p.write_bytes(b'<a href="x.html">x</a>')
            os.utime(p, (1_000_000_000, 1_000_000_000))
            before = (p.read_bytes(), p.stat().st_mtime)
            linkcheck.check(str(p))
            after = (p.read_bytes(), p.stat().st_mtime)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
