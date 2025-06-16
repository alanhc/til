---
title: python使用pyinstaller製作桌面應用程式
date: 2024-06-26
tags:
  - python
  - pyinstaller
updated: 2024-06-26
up:
  - "[[cross-platform]]"
---
- 先看 File structure:
![](https://i.imgur.com/HGlGJij.png)
```python
# app.py
import streamlit as st

st.title('Hello World')
```
```python
# hooks/hook-streamlit.py

from PyInstaller.utils.hooks import copy_metadata

datas = copy_metadata("streamlit")
```
```python
# run_app.py

import streamlit

import streamlit.web.cli as stcli

import os, sys

if __name__ == "__main__":

os.chdir(os.path.dirname(__file__))

sys.argv = [

"streamlit",

"run",

"./src/app.py",

"--global.developmentMode=false",

]

sys.exit(stcli.main())
```
### method 1: 第一次打包
`pyinstaller --onefile --additional-hooks-dir=./hooks run_app.py --clean`
第二次打包
### method 2:
`pyi-makespec run_app.py`
會產生run_app.spec
```python
# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import copy_metadata

datas = [("/Users/alantseng/.pyenv/versions/3.12.4/lib/python3.12/site-packages/streamlit/runtime", "./streamlit/runtime")]
datas += collect_data_files("streamlit")
datas += copy_metadata("streamlit")
datas += [('./src', './src')]



block_cipher = None


a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=['./hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='run_app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

- notes: `/Users/alantseng/.pyenv/versions/3.12.4/lib/python3.12/site-packages` 這個可以看 :
	- `python -c 'import site; print(site.getsitepackages())'`
- `pyinstaller run_app.spec --clean`

## 加上docx
```
# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import copy_metadata
import sys
from os import path
site_packages = next(p for p in sys.path if 'site-packages' in p)

datas = [("/Users/alantseng/.pyenv/versions/3.12.4/lib/python3.12/site-packages/streamlit/runtime", "./streamlit/runtime")]
datas += collect_data_files("streamlit")
datas += copy_metadata("streamlit")
datas += collect_data_files("python_docx")
datas += copy_metadata("python_docx")
datas += collect_data_files("docx")
datas += copy_metadata("docx")
datas += [('./src', './src')]
datas +=[(path.join(site_packages,"docx","templates"), "docx/templates")]

block_cipher = None


a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=["python_docx", "docx"],
    hookspath=['./hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='run_app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```
## Ref
