
from distutils.core import setup

setup(name='coccigrep',
      version='0.5',
      description='Semantic grep for C based on coccinelle',
      author='Eric Leblond',
      author_email='eric@regit.org',
      url='http://home.regit.org/software/coccigrep/',
      scripts=['coccigrep'],
      py_modules=['coccigrep']
      )
