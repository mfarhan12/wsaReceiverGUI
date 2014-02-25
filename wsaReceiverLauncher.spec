# -*- mode: python -*-
a = Analysis(['wsaReceiverLauncher.pyw'],
             pathex=['C:\\Users\\Mohammad\\Documents\\Python\\gageReceiverGUI'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='wsaReceiverLauncher.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False )
