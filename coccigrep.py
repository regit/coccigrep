#!/usr/bin/python
# Copyright (C) 2011 Eric Leblond <eric@regit.org>
#
# You can copy, redistribute or modify this Program under the terms of
# the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# version 3 along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.


from subprocess import call, Popen, PIPE
from tempfile import NamedTemporaryFile
from os import unlink
import argparse
from sys import exit

SPATCH="spatch"

cocci_grep_struct_attribute_used="""@init@
typedef %s;
%s *p;
position p1;
@@

p->%s@p1
"""

cocci_grep_struct_attribute_set="""@init@
typedef %s;
%s *p;
expression E;
position p1;
@@

(
p->%s@p1 |= E
|
p->%s@p1 = E
)
"""

cocci_grep_struct_attribute_test="""@init@
typedef %s;
%s *p;
expression E;
position p1;
@@

(
p->%s@p1 == E
|
p->%s@p1 != E
|
p->%s@p1 & E
)
"""

cocci_python="""

@ script:python @
p1 << init.p1;
@@

for p in p1:
    print "%s:%s:%s" % (p.file,p.line,p.column)
"""

parser = argparse.ArgumentParser(prog='coccigrep', description='Semantic grep based on coccinelle')
parser.add_argument('-t', '--type', default='Signature', help='C type where looking for')
parser.add_argument('-a', '--attribut', default='flags', help='C attribut that is set')
parser.add_argument('-o', '--operation', default='used', help='Operation on structure (used, set, test)')
parser.add_argument('-A', '--after-context', dest='after', type=int, default=0, help='Number of line after context')
parser.add_argument('-B', '--before-context', dest='before', type=int, default=0, help='Number of line before context')
parser.add_argument('file', metavar='file', nargs='+', help='List of files')
parser.add_argument('--version', action='version', version='%(prog)s 0.1')

args = parser.parse_args()

# create tmp cocci file:
tmp_cocci_file = NamedTemporaryFile(suffix=".cocci", delete=False)
tmp_cocci_file_name = tmp_cocci_file.name


if args.operation == 'set':
    cocci_grep = cocci_grep_struct_attribute_set % (args.type, args.type, args.attribut, args.attribut) + cocci_python
elif args.operation == 'test':
    cocci_grep = cocci_grep_struct_attribute_test % (args.type, args.type, args.attribut, args.attribut, args.attribut) + cocci_python
elif args.operation == 'used':
    cocci_grep = cocci_grep_struct_attribute_used % (args.type, args.type, args.attribut) + cocci_python
else:
    print "unkown method"
    exit(1)

tmp_cocci_file.write(cocci_grep)
tmp_cocci_file.close()

# launch spatch
cmd = [SPATCH, "-sp_file", tmp_cocci_file.name] + args.file
#print "running: %s." % " ".join(cmd)

output = Popen(cmd, stdout=PIPE).communicate()[0]
unlink(tmp_cocci_file_name)


# TODO need to suppress the doublon here
for ematch in output.split("\n"):
     try:
         (efile, eline, ecol) = ematch.split(":")
         f = open(efile, 'r')
         lines = f.readlines()
         for i in range(int(eline) - 1 - args.before, int(eline) + args.after):
             print "%s:%s: %s" % (efile, eline, lines[i].rstrip())
         f.close()
     except ValueError:
        pass
