#!/usr/bin/python

from subprocess import call, Popen, PIPE
from tempfile import NamedTemporaryFile
from os import unlink
import argparse

cocci_grep="""@init@
typedef %s;
%s *p;
expression E;
position p1;
@@

(
p->%s@p1 |= E;
|
p->%s@p1 = E;
)

@ script:python @
p1 << init.p1;
@@
"""

cocci_python="""
for p in p1:
    print "%s:%s:" % (p.file,p.line)
    f = open(p.file, 'r')
    lines = f.readlines()
    frame=4
    for i in range(int(p.line) - 1 - frame, int(p.line) - 1 + frame):
        print lines[i].rstrip()
    f.close()
"""

parser = argparse.ArgumentParser(description='Semantic grep based on coccinelle')
parser.add_argument('-t', '--type', default='Signature', help='C type where looking for')
parser.add_argument('-a', '--attribut', default='flags', help='C attribut that is set')
parser.add_argument('file', metavar='file', nargs='+', help='List of files')
args = parser.parse_args()

# create tmp cocci file:
tmp_cocci_file = NamedTemporaryFile(suffix=".cocci", delete=False)
tmp_cocci_file_name = tmp_cocci_file.name
tmp_cocci_file.write(cocci_grep % (args.type, args.type, args.attribut, args.attribut) + cocci_python)

# launch spatch
cmd = ["spatch", "-sp_file", tmp_cocci_file.name] + args.file
print "running: %s." % " ".join(cmd)

output = Popen(cmd)

#print output
tmp_cocci_file.close()
#unlink(tmp_cocci_file_name)
