#!/usr/bin/env python
from setuptools import setup
from src.coccigrep import COCCIGREP_VERSION

setup(name='coccigrep',
      version=COCCIGREP_VERSION,
      description='Semantic grep for C based on coccinelle',
      author='Eric Leblond',
      author_email='eric@regit.org',
      url='http://home.regit.org/software/coccigrep/',
      scripts=['coccigrep'],
      packages=['coccigrep'],
      package_dir={'coccigrep':'src'},
      package_data={'coccigrep': ['data/*.cocci', 'coccigrep.cfg']},
      provides=['coccigrep'],
      requires=['argparse'],
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
