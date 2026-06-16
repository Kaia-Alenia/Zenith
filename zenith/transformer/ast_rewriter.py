
import ast
import sys
from pathlib import Path

if hasattr(sys, "stdlib_module_names"):
    _STDLIB_ROOTS = frozenset(sys.stdlib_module_names)
else:
    _STDLIB_ROOTS = frozenset([
        "abc", "argparse", "ast", "asyncio", "atexit", "base64", "bisect", "builtins",
        "bz2", "calendar", "cgi", "cgitb", "chunk", "cmath", "cmd", "code", "codecs",
        "collections", "colorsys", "compileall", "concurrent", "configparser", "contextlib",
        "contextvars", "copy", "copyreg", "crypt", "csv", "ctypes", "curses", "dataclasses",
        "datetime", "dbm", "decimal", "difflib", "dis", "distutils", "doctest", "email",
        "encodings", "ensurepip", "enum", "errno", "faulthandler", "filecmp", "fileinput",
        "fnmatch", "fractions", "ftplib", "gc", "getopt", "getpass", "gettext", "glob",
        "graphlib", "grp", "gzip", "hashlib", "hmac", "html", "http", "imaplib", "imghdr",
        "imp", "importlib", "inspect", "io", "ipaddress", "json", "keyword", "lib2to3",
        "linecache", "locale", "logging", "lzma", "mailbox", "mailcap", "marshal", "math",
        "mimetypes", "mmap", "modulefinder", "multiprocessing", "netrc", "nis", "nntplib",
        "numbers", "operator", "optparse", "os", "ossaudiodev", "pathlib", "pdb", "pickle",
        "pickletools", "pipes", "pkgutil", "platform", "plistlib", "poplib", "posix",
        "pprint", "profile", "pstats", "pty", "pwd", "py_compile", "pyclbr", "pydoc",
        "queue", "quopri", "random", "re", "readline", "reprlib", "resource", "rlcompleter",
        "runpy", "sched", "secrets", "select", "selectors", "shelve", "shimport", "shlex",
        "shutil", "signal", "site", "smtpd", "smtplib", "sndhdr", "socket", "socketserver",
        "spwd", "sqlite3", "ssl", "stat", "statistics", "string", "stringprep", "struct",
        "subprocess", "sunau", "symtable", "sys", "sysconfig", "syslog", "tabnanny",
        "tarfile", "telnetlib", "tempfile", "termios", "test", "textwrap", "threading",
        "time", "timeit", "tkinter", "token", "tokenize", "trace", "traceback", "tracemalloc",
        "tty", "types", "typing", "unicodedata", "unittest", "urllib", "uu", "uuid",
        "warnings", "wave", "weakref", "webbrowser", "wsgiref", "xdg", "xml", "xmlrpc",
        "zipapp", "zipfile", "zipimport", "zlib", "_thread", "_io"
    ])


class ImportCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.detected = set()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.detected.add(alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self.detected.add(node.module)
            for alias in node.names:
                if alias.name != "*":
                    self.detected.add("{}.{}".format(node.module, alias.name))


def analyze_file(filepath: str) -> list[str]:
    try:
        content = Path(filepath).read_text(encoding="utf-8")
        tree = ast.parse(content, filename=filepath)
        collector = ImportCollector()
        collector.visit(tree)
        return sorted(collector.detected)
    except Exception:
        return []


def analyze_stdlib_only(filepath: str) -> list[str]:
    return [m for m in analyze_file(filepath) if m.split(".")[0] in _STDLIB_ROOTS]


def analyze_third_party(filepath: str) -> list[str]:
    return [m for m in analyze_file(filepath) if m.split(".")[0] not in _STDLIB_ROOTS]
