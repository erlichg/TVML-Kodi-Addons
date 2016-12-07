# -*- mode: python -*-

block_cipher = None
import os, fnmatch

matches = ['app.py']
for p in os.listdir('kodiplugins'):
    if os.path.isdir(os.path.join('kodiplugins', p)):
        for pp in fnmatch.filter(os.listdir(os.path.join('kodiplugins', p)), '*.py'):
            matches.append(os.path.join('kodiplugins', p, pp))
for p in os.listdir('plugins'):
    if os.path.isdir(os.path.join('plugins', p)):
        for pp in fnmatch.filter(os.listdir(os.path.join('plugins', p)), '*.py'):
            matches.append(os.path.join('plugins', p, pp))
for p in fnmatch.filter(os.listdir('scripts'), '*.py'):
    if not p.startswith('__init__'):
        matches.append(os.path.join('scripts', p))
for p in fnmatch.filter(os.listdir(os.path.join('scripts', 'kodi')), '*.py'):
    if not p.startswith('__init__'):
        matches.append(os.path.join('scripts', 'kodi', p))

a = Analysis(matches,
             pathex=['scripts/', 'scripts/kodi'],
             binaries=None,
             datas=[
                ('plugins', 'plugins'),
                ('kodiplugins', 'kodiplugins'),
                ('js', 'js'),
                ('templates', 'templates'),
                ('images', 'images'),
                ('scripts', 'scripts'),
                ('LICENSE', '.'),
             ],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
for d in a.datas:
    if 'pyconfig' in d[0]: 
        a.datas.remove(d)
for d in a.datas:
	if 'Makefile' in d[0]:
		a.datas.remove(d)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='TVMLServer',
          debug=False,
          strip=False,
          upx=True,
          console=True )
