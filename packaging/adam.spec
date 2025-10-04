# PyInstaller spec for Adam v1 (offline-first)
# Build:
#   pyinstaller --clean -y packaging/adam.spec

import os
from PyInstaller.utils.hooks import collect_submodules

project_root = os.path.abspath(os.getenv("ADAM_PROJECT_ROOT", os.getcwd()))
src_dir = os.path.join(project_root, "src")

hidden = []
hidden += collect_submodules("adam")

# Use absolute path to the repo-root entry script so PyInstaller doesn't look under packaging/
entry_script = os.path.join(project_root, "run_adam.py")

a = Analysis(
    [entry_script],
    pathex=[project_root, src_dir],
    binaries=[],
    datas=[
        (os.path.join(project_root, "config"), "config"),
        (os.path.join(project_root, "plugins"), "plugins"),
        (os.path.join(project_root, "src", "ui", "assets"), os.path.join("src", "ui", "assets")),
        (os.path.join(project_root, "models", "light-condenser.gguf"), os.path.join("models", "light-condenser.gguf")),
    ],
    hiddenimports=hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    name="adam",
    console=True,   # set False if you want a windowed app on Windows
    disable_windowed_traceback=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="adam",
)
