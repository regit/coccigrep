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
from sys import exit, stderr
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

class CocciException(Exception):
    """
    Generic class for coccigrep exception
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value

class CocciConfigException(CocciException):
    """
    Exception raised when configuration parameter are not correct.

    For example, it is returned if spatch command can not be found.
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value

class CocciRunException(CocciException):
    """
    Exception raised when running parameters are not correct.

    For example, it is returned if a required argument is missing.
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value

class CocciGrepConfig:
    """
    Configuration handling class

    This class parses configuration and can be used to access to
    configuration item via get operations. This is mainly a wrapper
    around configparser.
    """
    def __init__(self):
        self.configbasename = 'coccigrep'
        self.config = RawConfigParser()
        self.global_config = RawConfigParser()
        self.parse_config()
    def parse_config(self):
        """
        Parse the hierarchy of configuration files
        """
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
            raise CocciException('No package config file: %s' % (cpath))
    def get(self, section, value):
        """
        Get value for a configuration item

        :param section: name of the section in the ini file
        :type section: str
        :param value: name of the value under the section
        :type value: str
        :return: value of option as a str
        """
        try:
            return self.config.get(section, value)
        except:
            return self.global_config.get(section, value)
    def getint(self, section, value):
        """
        Get value for a configuration item returned as int

        :param section: name of the section in the ini file
        :type section: str
        :param value: name of the value under the section
        :type value: str
        :return: value of option as a int
        """
        try:
            return self.config.getint(section, value)
        except:
            return self.global_config.getint(section, value)
    def getboolean(self, section, value):
        """
        Get value for a configuration item returned as boolean

        :param section: name of the section in the ini file
        :type section: str
        :param value: name of the value under the section
        :type value: str
        :return: value of option as a boolean
        """
        try:
            return self.config.getboolean(section, value)
        except:
            return self.global_config.getboolean(section, value)

class CocciMatch:
    """
    Store a match and take care of its display
    """
    def __init__(self, mfile, mline, mcol, mlineend, mcolend):
        self.file = mfile
        self.line = int(mline)
        self.column = int(mcol)
        self.lineend = int(mlineend)
        self.columnend = int(mcolend)
    def display(self, stype, mode='raw', oformat='term', before=0, after=0):
        """
        Display output for a single match

        :param mode: display mode
        :type mode: str
        :param oformat: format of output for color (term, html)
        :type oformat: str
        :param before: number of lines to display before match
        :type before: int
        :param after: number of lines to display after match
        :type after: int
        """
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
    """
    Class used for running spatch command in the case of multiprocessing
    """
    def __init__(self, cmd, verbose):
        self.process = Process(target=self.execute, args=(self, ))
        self.output, self.input = Pipe()
        self.cmd = cmd
        self.verbose = verbose
    def execute(self, option=''):
        output = ""
        try:
            if self.verbose:
                stderr.write("Running: %s." % " ".join(self.cmd))
                output = Popen(self.cmd, stdout=PIPE).communicate()[0]
            else:
                output = Popen(self.cmd, stdout=PIPE, stderr=PIPE).communicate()[0]
        except Exception, err:
            import pickle
            output = pickle.dumps(err)
            pass
        self.input.send(output)
        self.input.close()
    def start(self):
        self.process.start()
    def join(self):
        self.process.join()
    def recv(self):
        return self.output.recv()

class CocciGrep:
    """
    Core class of the module: setup and run.

    This class is the core of the module. It is responsible
    of initialisation and running of the request.
    """
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
        """
        :param stype: structure name, used to replace '$type' in the cocci file
        :type stype: str
        :param attribut: basically attribut of the structure, used to replace '$attribut' in the cocci file
        :type attribut: str
        :param operation: search operation to do
        :type operation: str
        :raise: :class:`CocciRunException`
        """
        if stype == None:
            raise CocciRunException("Can't use coccigrep without type to search")
        self.type = stype
        self.attribut = attribut
        self.operation = operation
    def set_concurrency(self, ncpus):
        """
        Set concurrency level (number of spatch command to run in parallel)

        :param ncpus: number of process to launch in parallel
        :type ncpus: int
        """
        if have_multiprocessing:
            self.ncpus = ncpus
            return True
        else:
            return False
    def set_spatch_cmd(self, cmd):
        """
        Set path or command name for spatch

        :param cmd: Name of parth of the spatch command
        :type cmd: str
        """
        self.spatch = cmd
    def get_datadir(self):
        this_dir, this_filename = path.split(__file__)
        datadir = path.join(this_dir, "data")
        return datadir
    def get_operations(self):
        """
        Get list of available operations

        :return: list of operations in a list of str
        """
        return self.operations.keys()
    def get_operation_name(self, fname):
        return path.split(fname)[-1].replace('.cocci','')
    def add_operations(self, new_ops):
        """
        Add operation to the list of supported operations

        :param new_ops: list of filenames (ending by .cocci)
        :type new_ops: list of str
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
        """
        Activate verbose mode
        """
        self.verbose = True

    def run(self, files):
        """
        Run the search against the files given in argument

        This function is doing the main job. It will run spatch with
        the correct parameters by using subprocess or it will use
        multiprocessing if a concurrency level greater than 1 has been
        asked.

        :param files: list of filenames
        :type files: list of str
        :raise: :class:`CocciRunException` or :class:`CocciConfigException`
        """

        if len(files) == 0:
            raise CocciRunException("Can't use coccigrep without files to search")
        for cfile in files:
            if not path.isfile(cfile):
                raise CocciRunException("'%s' is not a file, can't continue" % cfile)
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
                if len(rfiles) >= 1:
                    fseq.append(rfiles)
            for sub_files in fseq:
                cmd = [self.spatch, "-sp_file", tmp_cocci_file.name] + sub_files
                sprocess = CocciProcess(cmd, self.verbose)
                sprocess.start()
                self.process.append(sprocess)
            for process in self.process:
                ret = process.recv()
                process.join()
                # CocciProcess return a serialized exception in case of exception
                if ret.startswith('cexceptions\n'):
                    import pickle
                    import errno
                    err = pickle.loads(ret)
                    unlink(tmp_cocci_file_name)
                    if err.errno in (errno.ENOENT, errno.ENOEXEC):
                        raise CocciConfigException("Unable to run spatch command '%s': %s." % (cmd[0], err.strerror))
                    else:
                        raise CocciRunException("Unable to run '%s': %s." % (" ".join(cmd), err.strerror))
                else:
                    output += ret
        else:
            cmd = [self.spatch, "-sp_file", tmp_cocci_file.name] + files
            try:
                if self.verbose:
                    stderr.write("Running: %s." % " ".join(cmd))
                    output = Popen(cmd, stdout=PIPE).communicate()[0]
                else:
                    output = Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()[0]
            except OSError, err:
                import errno
                unlink(tmp_cocci_file_name)
                if err.errno in (errno.ENOENT, errno.ENOEXEC):
                    raise CocciConfigException("Unable to run spatch command '%s': %s." % (cmd[0], err.strerror))
                else:
                    raise CocciRunException("Unable to run '%s': %s." % (" ".join(cmd), err.strerror))

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
        """
        Display output for complete request

        :param mode: display mode
        :type mode: str
        :param before: number of lines to display before match
        :type before: int
        :param after: number of lines to display after match
        :type after: int
        :param oformat: format of output for color (term, html)
        :type oformat: str
        :return: the result of the search as a str
        """
        output = ""
        for match in self.matches:
            output += match.display(self.type, mode=mode, oformat=oformat, before=before, after=after)
        return output.rstrip()


