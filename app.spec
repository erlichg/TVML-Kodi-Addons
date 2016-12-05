# -*- mode: python -*-

block_cipher = None


a = Analysis(['app.py'],
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
             hiddenimports=['xml.etree.ElementTree', 'AdvancedHTMLParser', 'StringIO'],
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
          name='app',
          debug=False,
          strip=False,
          upx=True,
          console=True )
