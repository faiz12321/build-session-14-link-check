from unittest import mock
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
                   '<a href="mailto:help">3</a><a href="tel:123">4</a>')
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


class SetupSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.sample = self.root / 'sample'

    def test_existing_folder_preserves_nested_bytes_and_metadata(self):
        (self.sample / 'nested').mkdir(parents=True)
        keep = self.sample / 'nested' / 'keep.bin'
        keep.write_bytes(b'KEEP')
        before = (keep.read_bytes(), keep.stat().st_mtime_ns)
        with self.assertRaises(FileExistsError):
            make_sample.make(self.sample)
        self.assertEqual(before, (keep.read_bytes(), keep.stat().st_mtime_ns))
        self.assertEqual(sorted(p.relative_to(self.sample).as_posix() for p in self.sample.rglob('*')), ['nested','nested/keep.bin'])

    def test_existing_file_preserved(self):
        self.sample.write_bytes(b'KEEP')
        before = (self.sample.read_bytes(), self.sample.stat().st_mtime_ns)
        with self.assertRaises(FileExistsError):
            make_sample.make(self.sample)
        self.assertEqual(before, (self.sample.read_bytes(), self.sample.stat().st_mtime_ns))

    def test_repeat_setup_preserves_generated_bytes_and_metadata(self):
        make_sample.make(self.sample)
        before = {p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in self.sample.iterdir()}
        with self.assertRaises(FileExistsError):
            make_sample.make(self.sample)
        self.assertEqual(before, {p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in self.sample.iterdir()})

    def test_cli_refuses_without_replacing(self):
        import shutil, subprocess, sys
        script = self.root / 'make_sample.py'
        shutil.copyfile(Path(__file__).resolve().parent / 'make_sample.py', script)
        self.sample.mkdir()
        keep = self.sample / 'keep'
        keep.write_bytes(b'KEEP')
        result = subprocess.run([sys.executable,str(script)],capture_output=True,text=True,cwd=self.root)
        self.assertEqual(result.returncode,1)
        self.assertIn('Nothing was replaced or deleted',result.stderr)
        self.assertEqual(keep.read_bytes(),b'KEEP')




class PathSafety(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.root=self.base/'sample'
        make_sample.make(self.root);self.file=self.root/'good.html'
    def link(self,path,target,directory=False):
        try:path.symlink_to(target,target_is_directory=directory)
        except OSError:self.skipTest('Symlink creation unavailable')
    def code(self,path):
        with redirect_stdout(io.StringIO()) as out:code=linkcheck.main(['linkcheck.py',str(path)])
        return code,out.getvalue()
    def test_file_link_refuses(self):
        p=self.base/'linked';self.link(p,self.file)
        with self.assertRaises(OSError):linkcheck.safe_input(p)
        self.assertEqual(self.code(p)[0],2)
    def test_linked_ancestor_refuses(self):
        p=self.base/'linked';self.link(p,self.root,True)
        self.assertEqual(self.code(p/'good.html')[0],2)
    def test_dangling_link_refuses(self):
        p=self.base/'linked';self.link(p,self.base/'missing')
        self.assertEqual(self.code(p)[0],2)
    def test_self_loop_refuses(self):
        p=self.base/'linked';self.link(p,p)
        self.assertEqual(self.code(p)[0],2)
    def test_hardlink_refuses(self):
        p=self.base/'hard';os.link(self.file,p)
        self.assertEqual(self.code(p)[0],2)
    def test_pipe_refuses_without_blocking(self):
        if not hasattr(os,'mkfifo'):self.skipTest('Unix pipe unavailable')
        p=self.base/'pipe';os.mkfifo(p)
        self.assertEqual(self.code(p)[0],2)
    def test_directory_refuses(self):self.assertEqual(self.code(self.root)[0],2)
    def test_traversal_refuses(self):self.assertEqual(self.code(self.root/'..'/'sample'/'good.html')[0],2)
    def test_reparse_attribute_refuses(self):
        real=Path.lstat;target=self.file
        def fake(path,*args,**kwargs):
            value=real(path,*args,**kwargs)
            if path==target:return type('Reparse',(),{'st_mode':value.st_mode,'st_file_attributes':0x400})()
            return value
        with mock.patch.object(Path,'lstat',fake):self.assertEqual(self.code(self.file)[0],2)
    def test_metadata_failure_nonzero(self):
        with mock.patch.object(Path,'lstat',side_effect=OSError('forced metadata error')):
            code,text=self.code(self.file);self.assertEqual(code,2);self.assertIn('forced metadata error',text)
    def test_setup_linked_parent_refuses(self):
        p=self.base/'linked';self.link(p,self.root,True)
        with self.assertRaises(OSError):make_sample.make(p/'new')
        self.assertFalse((self.root/'new').exists())
    def test_setup_traversal_refuses(self):
        with self.assertRaises(OSError):make_sample.make(self.root/'..'/'new')



class TargetSafety(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.page=self.root/'page.html';self.target=self.root/'target'
    def code(self,href):
        self.page.write_text('<a href="'+href+'">x</a>')
        with redirect_stdout(io.StringIO()):return linkcheck.main(['p',str(self.page)])
    def test_target_symlink_refuses(self):
        self.target.write_text('x');p=self.root/'link'
        try:p.symlink_to(self.target)
        except OSError:self.skipTest('Symlinks unavailable')
        self.assertEqual(self.code('link'),2)
    def test_target_dangling_refuses(self):
        p=self.root/'link'
        try:p.symlink_to(self.target)
        except OSError:self.skipTest('Symlinks unavailable')
        self.assertEqual(self.code('link'),2)
    def test_target_self_loop_refuses(self):
        p=self.root/'link'
        try:p.symlink_to(p)
        except OSError:self.skipTest('Symlinks unavailable')
        self.assertEqual(self.code('link'),2)
    def test_target_ancestor_alias_refuses(self):
        self.target.mkdir();p=self.root/'alias'
        try:p.symlink_to(self.target,target_is_directory=True)
        except OSError:self.skipTest('Symlinks unavailable')
        self.assertEqual(self.code('alias/'),2)
    def test_target_hardlink_refuses(self):
        self.target.write_text('x');os.link(self.target,self.root/'hard')
        self.assertEqual(self.code('hard'),2)
    def test_target_pipe_refuses(self):
        if not hasattr(os,'mkfifo'):self.skipTest('Unix pipe unavailable')
        os.mkfifo(self.target);self.assertEqual(self.code('target'),2)
    def test_target_traversal_refuses(self):self.assertEqual(self.code('../target'),2)
    def test_target_metadata_error_refuses(self):
        real=Path.lstat
        def fake(p,*a,**kw):
            if p==self.target:raise OSError('forced')
            return real(p,*a,**kw)
        with mock.patch.object(Path,'lstat',fake):self.assertEqual(self.code('target'),2)


if __name__ == "__main__":
    unittest.main()
