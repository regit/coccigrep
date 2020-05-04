#!/usr/bin/env python
from setuptools import setup
from src.coccigrep import COCCIGREP_VERSION

import sys
from os import path

if (sys.version_info > (3, 0)):
    pygments_deps = 'pygments'
else:
    pygments_deps = 'pygments<2.6.0'

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()
setup(name='coccigrep',
      version=COCCIGREP_VERSION,
      description='Semantic grep for C based on coccinelle',
      author='Eric Leblond',
      author_email='eric@regit.org',
      long_description=long_description,
      long_description_content_type='text/x-rst',  # Optional (see note above)
      url='http://home.regit.org/software/coccigrep/',
      scripts=['coccigrep'],
      packages=['coccigrep'],
      package_dir={'coccigrep': 'src'},
      package_data={'coccigrep': ['data/*.cocci', 'coccigrep.cfg']},
      provides=['coccigrep'],
      install_requires=['argparse', 'configparser', pygments_deps],
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Topic :: Software Development',
                  ],
      )
