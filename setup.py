#!/usr/bin/env python
from distutils.core import setup

setup(name='coccigrep',
      version='0.8',
      description='Semantic grep for C based on coccinelle',
      author='Eric Leblond',
      author_email='eric@regit.org',
      url='http://home.regit.org/software/coccigrep/',
      scripts=['coccigrep'],
      packages=['coccigrep'],
      package_dir={'coccigrep':'src'},
      package_data={'coccigrep': ['data/*.cocci', 'coccigrep.cfg']},
      )
