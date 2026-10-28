# PyInstaller spec: standalone mutator (bundles installed crapper + tree-sitter).
# Build: scripts/build-standalone.ps1 (installs crapper from ../crapper first)

from pathlib import Path

from PyInstaller.utils.hooks import collect_all

root = Path(SPECPATH).resolve().parent
entry = root / "src" / "mutator" / "__main__.py"

hidden = [
    "mutator.cli",
    "mutator.crapper_link",
    "mutator.coverage",
    "mutator.discover",
    "mutator.engine",
    "mutator.functions",
    "mutator.runner",
    "mutator.sites",
    "mutator.workers",
    "crapper.cli",
    "crapper.coverage",
    "crapper.discover",
    "crapper.runners",
    "crapper.languages",
    "crapper.languages.treesitter",
    "crapper.languages.clojure",
    "crapper.languages.java",
    "crapper.languages.csharp",
    "crapper.languages.golang",
    "crapper.languages.typescript",
    "crapper.languages.rust",
    "crapper.languages.python",
]

datas: list = []
binaries: list = []
for pkg in ("tree_sitter", "tree_sitter_language_pack"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hidden += h

a = Analysis(
    [str(entry)],
    pathex=[str(root / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(root / "packaging" / "runtime_utf8.py")],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="mutator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
