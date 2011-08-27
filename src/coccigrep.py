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

from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile
from os import unlink, path, listdir, getcwd
from sys import exit
from string import Template
from ConfigParser import RawConfigParser
import re

have_multiprocessing  = True
try:
    from multiprocessing import Process, Pipe
except:
    have_multiprocessing = False

have_pygments = True
try:
    from pygments import highlight
    from pygments.lexers import CLexer
    from pygments.filters import NameHighlightFilter
    from pygments.formatters import Terminal256Formatter, HtmlFormatter
except:
    have_pygments = False

class CocciGrepConfig:
    def __init__(self):
        self.configbasename = 'coccigrep'
        self.config = RawConfigParser()
        self.global_config = RawConfigParser()
        self.parse_config()
    def parse_config(self):
        paths = [
            path.join('/etc', self.configbasename),
            path.join(path.expanduser('~'), '.%s' % self.configbasename),
            path.join(getcwd(), '.%s' %  self.configbasename),
        ]
        for cpath in paths:
            if path.isfile(cpath):
                self.config.read(cpath)

        # Parse global configuration to have sane default
        cpath = path.join(path.dirname(__file__), '%s.cfg' % self.configbasename)
        if path.isfile(cpath):
            self.global_config.read(cpath)
        else:
            raise Exception('No package config file: %s' % (cpath))
    def get(self, section, value):
        try:
            return self.config.get(section, value)
        except:
            return self.global_config.get(section, value)
    def getint(self, section, value):
        try:
            return self.config.getint(section, value)
        except:
            return self.global_config.getint(section, value)
    def getboolean(self, section, value):
        try:
            return self.config.getboolean(section, value)
        except:
            return self.global_config.getboolean(section, value)

class CocciMatch:
    def __init__(self, mfile, mline, mcol, mlineend, mcolend):
        self.file = mfile
        self.line = int(mline)
        self.column = int(mcol)
        self.lineend = int(mlineend)
        self.columnend = int(mcolend)
    def display(self, stype, mode='raw', oformat='term', before=0, after=0):
        f = open(self.file, 'r')
        lines = f.readlines()
        pmatch = lines[self.line -1][self.column:self.columnend]
        output = ""
        if mode == 'color':
            output += "%s: l.%s -%d, l.%s +%d, %s *%s\n" % (self.file, self.line, before, self.line, after, stype, pmatch)
        for i in range(int(self.line) - 1 - before, int(self.line) + after):
            if mode == 'color':
                output += lines[i]
            elif mode == 'vim':
                output += "%s|%s| (%s *%s): %s" % (self.file, self.line, stype, pmatch, lines[i])
            elif mode == 'emacs':
                output += "%s:%s: (%s *%s): %s" % (self.file, self.line, stype, pmatch, lines[i])
            else:
                output += "%s:%s (%s *%s): %s" % (self.file, self.line, stype, pmatch, lines[i])
        f.close()
        if mode == 'color':
            if have_pygments:
                lexer = CLexer()
                lfilter = NameHighlightFilter(names=[pmatch])
                lexer.add_filter(lfilter)
                if oformat == "term":
                    return highlight(output, lexer, Terminal256Formatter())
                elif oformat == "html":
                    return highlight(output, lexer, HtmlFormatter(noclasses=True))
                else:
                    return output
        return output

class CocciProcess:
    def __init__(self, cmd, verbose):
        self.process = Process(target=self.execute, args=(self, ))
        self.output, self.input = Pipe()
        self.cmd = cmd
        self.verbose = verbose
    def execute(self, option=''):
        output = ""
        if self.verbose:
            print "Running: %s." % " ".join(self.cmd)
            output = Popen(self.cmd, stdout=PIPE).communicate()[0]
        else:
            output = Popen(self.cmd, stdout=PIPE, stderr=PIPE).communicate()[0]
        self.input.send(output)
        self.input.close()
    def start(self):
        self.process.start()
    def join(self):
        self.process.join()
    def recv(self):
        return self.output.recv()

class CocciGrep:
    spatch="spatch"
    cocci_python="""

@ script:python @
p1 << init.p1;
@@

for p in p1:
    print "%s:%s:%s:%s:%s" % (p.file,p.line,p.column,p.line_end,p.column_end)
"""

    def __init__(self):
        self.verbose = False
        self.spatch = CocciGrep.spatch
        self.ncpus = 1
        self.operations = {}
        self.process = []
        dirList = listdir(self.get_datadir())
        for fname in dirList:
            op = path.split(fname)[-1].replace('.cocci','')
            self.operations[op] = path.join(self.get_datadir(), fname)

    def setup(self, stype, attribut, operation):
        self.type = stype
        self.attribut = attribut
        self.operation = operation
    def set_concurrency(self, ncpus):
        if have_multiprocessing:
            self.ncpus = ncpus
            return True
        else:
            return False
    def set_spatch_cmd(self, cmd):
        self.spatch = cmd
    def get_datadir(self):
        this_dir, this_filename = path.split(__file__)
        datadir = path.join(this_dir, "data")
        return datadir
    def get_operations(self):
        return self.operations.keys()
    def get_operation_name(self, fname):
        return path.split(fname)[-1].replace('.cocci','')
    def add_operations(self, new_ops):
        """
        Take a list of filename as argument
        """
        if len(new_ops) == 0:
            return
        file_filter = re.compile('^[^\.].*\.cocci$')
        for fname in new_ops:
            # file need to end with cocci
            if file_filter.match(fname):
                op = path.split(fname)[-1].replace('.cocci','')
                self.operations[op] = fname
    def set_verbose(self):
        self.verbose = True

    def run(self, files):
        # create tmp cocci file:
        tmp_cocci_file = NamedTemporaryFile(suffix=".cocci", delete=False)
        tmp_cocci_file_name = tmp_cocci_file.name
        # open file with name matching operation
        cocci_file = open(self.operations[self.operation], 'r')
        # get the string and build template
        cocci_tmpl = cocci_file.read()
        cocci_smpl_tmpl = Template(cocci_tmpl)
        cocci_file.close()
        cocci_smpl = cocci_smpl_tmpl.substitute(type=self.type, attribut=self.attribut)
        cocci_grep = cocci_smpl + CocciGrep.cocci_python

        tmp_cocci_file.write(cocci_grep)
        tmp_cocci_file.close()

        # launch spatch
        output = ""
        if self.ncpus > 1 and len(files) > 1:
            fseq = []
            splitsize = 1.0/self.ncpus*len(files)
            for i in range(self.ncpus):
                rfiles = files[int(round(i*splitsize)):int(round((i+1)*splitsize))]
                if len(rfiles) > 1:
                    fseq.append(rfiles)
            for sub_files in fseq:
                cmd = [self.spatch, "-sp_file", tmp_cocci_file.name] + sub_files
                sprocess = CocciProcess(cmd, self.verbose)
                sprocess.start()
                self.process.append(sprocess)
            for process in self.process:
                ret = process.recv()
                if ret:
                    output += ret
                process.join()
        else:
            cmd = [self.spatch, "-sp_file", tmp_cocci_file.name] + files
            if self.verbose:
                print "Running: %s." % " ".join(cmd)
                output = Popen(cmd, stdout=PIPE).communicate()[0]
            else:
                output = Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()[0]

        unlink(tmp_cocci_file_name)

        prevfile = None
        prevline = None
        self.matches = []
        for ematch in output.split("\n"):
            try:
                (efile, eline, ecol,elinend, ecolend) = ematch.split(":")
                nmatch = CocciMatch(efile, eline, ecol,elinend, ecolend)
                # if there is equality then we will already display the line
                if (efile == prevfile) and (eline == prevline):
                    continue
                else:
                    prevfile = efile
                    prevline = eline
                    self.matches.append(nmatch)
            except ValueError:
                pass

    def display(self, mode='raw', before=0, after=0, oformat='term'):
        output = ""
        for match in self.matches:
            output += match.display(self.type, mode=mode, oformat=oformat, before=before, after=after)
        return output.rstrip()


