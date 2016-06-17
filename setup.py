from distutils.core import setup
setup(name='zramcfg',
      version='1.0',
      py_modules=['zramcfg'],
      description='ZRAM configuration',
      author='Hannes Reinecke',
      author_email='hare@suse.com',
      url='https://github.com/hreinecke/zramcfg',
      data_files=[('/usr/lib/systemd/system', ['zramcfg.service']),
                  ('/usr/share/man/man8', ['zramcfg.8'])]
      )
