# Copyright (C) 2011-2018 Eric Leblond <eric@regit.org>
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

try:
    from configparser import SafeConfigParser
except Exception:
    from ConfigParser import SafeConfigParser
from os import unlink, path, listdir, getcwd
from string import Template
from subprocess import Popen, PIPE, STDOUT
from sys import stderr, stdout
from tempfile import NamedTemporaryFile
import errno
import re
import sys

COCCIGREP_VERSION = "1.19"

have_multiprocessing = True
try:
    from multiprocessing import Process, Pipe
except ImportError:
    have_multiprocessing = False


have_pygments = True
try:
    from pygments import highlight
    from pygments.lexers import CLexer
    from pygments.filters import NameHighlightFilter
    from pygments.formatters import Terminal256Formatter, HtmlFormatter
except ImportError:
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
    pass


class CocciRunException(CocciException):
    """
    Exception raised when running parameters are not correct.

    For example, it is returned if a required argument is missing.
    """
    pass


# produces conf file paths in reverse specificity order, ie
# - package conf
# - system wide
# - user
# - current dir
_CONF_FILES = tuple((path.join(dirname, name_format % 'coccigrep')
    for dirname, name_format in
    ((path.dirname(__file__), '%s.cfg'),
    ('/etc', '%s'),
    (path.expanduser('~'), '.%s'),
    (getcwd(), '.%s'))))


class CocciGrepConfig(SafeConfigParser):
    """
    Configuration handling class

    This class parses configuration and can be used to access to
    configuration item via get operations. CocciGrepConfig is derived
    from SafeConfigParser
    """
    def __init__(self):
        SafeConfigParser.__init__(self)
        self._load_config()

    def _load_config(self):
        """
        loads configuration from files given in _conf_FILES,
        overwriting the less specific by the most specific (given last)
        """
        for index, filename in enumerate(_CONF_FILES):
            if path.isfile(filename):
                self.read(filename)
            elif index == 0:
                raise CocciException('No package config file: %s' % (filename))


class CocciMatch:
    """
    Store a match and take care of its display
    """

    ptype_regexp = re.compile("^[ )]*\.")

    def __init__(self, mfile, mline, mcol, mlineend, mcolend, search):
        self.file = mfile
        self.line = int(mline)
        self.column = int(mcol)
        self.lineend = int(mlineend)
        self.columnend = int(mcolend)
        self.search = search
        self.start_at = self.line
        self.stop_at = int(mlineend)
        self.trailer = ""

    def display(self, stype, mode='raw', oformat='term'):
        """
        Display output for a single match

        :param stype: name of the matched type
        :type stype: str
        :param mode: display mode
        :type mode: str
        :param oformat: format of output for color (term, html)
        :type oformat: str
        :return: a human readable string containing the result of the search
                 (matched line, context, file name, etc.)
        """
        f = open(self.file, 'r')
        lines = f.readlines()
        pmatch = lines[self.line - 1][self.column:self.columnend]
        ptype = "*"  # match is a pointer to struct
        if (CocciMatch.ptype_regexp.search(lines[self.line - 1][self.columnend:])):
            ptype = ""
        output = ""
        if mode == 'color':
            output += "%s: l.%s -%d, l.%s +%d, %s %s%s\n" % (self.file,
                 self.line, self.line - self.start_at, self.line,
                 self.stop_at - self.line, stype, ptype, pmatch)
        for i in range(self.start_at - 1, min(self.stop_at, len(lines))):
            if mode == 'color':
                output += lines[i]
            elif mode == 'vim':
                output += "%s|%s| (%s %s%s): %s" % (self.file, i + 1,
                stype, ptype, pmatch, lines[i])
            elif mode == 'emacs':
                output += "%s:%s: (%s %s%s): %s" % (self.file, i + 1,
                stype, ptype, pmatch, lines[i])
            elif mode == 'grep' and stdout.isatty():
                lineend = lines[i][self.columnend:]
                if self.search.attribute:
                    lineend = lineend.replace(self.search.attribute, "\033[0;31m" + self.search.attribute + "\033[0m", 1)
                content = lines[i][:self.column] + \
                    "\033[0;32m" + lines[i][self.column:self.columnend] + "\033[0m" \
                    + lineend
                output += "%s:%s:\t%s" % (self.file, i + 1, content)
            elif i == self.line - 1:
                content = lines[i]
                output += "%s:%s (%s %s%s):\t%s" % (self.file, i + 1,
                    stype, ptype, pmatch, content)
            else:
                output += "%s-%s %s - %s" % (self.file, i + 1,
                ' ' * (2 + len(stype + ptype + pmatch)), lines[i])
        f.close()
        if mode == 'color':
            if have_pygments:
                lexer = CLexer()
                lfilter = NameHighlightFilter(names=[pmatch])
                lexer.add_filter(lfilter)
                if oformat == "term":
                    return highlight(output, lexer, Terminal256Formatter())
                elif oformat == "html":
                    return highlight(output, lexer,
                        HtmlFormatter(noclasses=True))
                else:
                    return output
        return output + self.trailer


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
                stderr.write("Running: %s.\n" % " ".join(self.cmd))
                output = Popen(self.cmd, stdout=PIPE).communicate()[0]
            else:
                output = Popen(self.cmd, stdout=PIPE,
                    stderr=PIPE).communicate()[0]
        except Exception as err:
            import json
            output = json.dumps(err)

        self.input.send(output)
        self.input.close()

    def start(self):
        self.process.start()

    def join(self):
        self.process.join()

    def recv(self):
        return self.output.recv()


def _operation_name(fname):
    return path.split(fname)[-1].replace('.cocci', '')


def _raise_run_err(err, cmd):
    if err.errno in (errno.ENOENT, errno.ENOEXEC):
        raise CocciConfigException("Unable to run spatch command "
            "'%s': %s." % (cmd[0], err.strerror))
    raise CocciRunException("Unable to run '%s': %s." % (" ".join(cmd),
        err.strerror))


class CocciPatch:
    """
    Class used to store information about a patch.

    This class is iterable and can be used as a dictionnary.
    """

    keywords = ["Name", "Author", "Desc", "Confidence", "File", "Revision", "Arguments"]
    comment = re.compile("^ *// *(%s): (.*)" % ("|".join(keywords)))

    def __init__(self, filename):
        # open file
        self.__dict__["File"] = filename
        self.__dict__["Name"] = _operation_name(filename)
        # read file
        f = open(filename, 'r')
        lines = f.readlines()
        # match
        for line in lines:
            mm = CocciPatch.comment.match(line)
            if mm:
                self.__dict__[mm.group(1)] = mm.group(2)

    def __iter__(self):
        """ return iterator over keys """
        return self.__dict__.__iter__()

    def __getitem__(self, key):
        # name ok?
        if key not in CocciPatch.keywords:
            raise KeyError("Trying to get invalid name '%s'." % key)
        return self.__dict__[key]

    def __setitem__(self, key, value):
        # name ok?
        if key not in CocciPatch.keywords:
            raise KeyError("Trying to set invalid name '%s'." % key)
        # set
        self.__dict__[key] = value

    def __str__(self):
        out = self["Name"] + ": "
        try:
            out += self["Desc"] + "\n"
        except KeyError:
            return out + ": No info available\n"
        for key in self:
            if key not in ["Name", "Desc", "File"]:
                out += " * %s: %s\n" % (key, self[key])
        return out


class CocciGrep:
    """
    Core class of the module: setup and run.

    This class is the core of the module. It is responsible
    of initialisation and running of the request.
    """
    spatch = "spatch"
    cocci_python_hdr_std = """
@ script:python @
"""
    cocci_python_hdr_filter = """
@ script:python depends on filter @
"""

    cocci_python = """

p1 << init.p1;
@@

for p in p1:
    print("%s:%s:%s:%s:%s" % (p.file,p.line,p.column,p.line_end,p.column_end))
"""

    def __init__(self):
        self.verbose = False
        self.spatch = CocciGrep.spatch
        self.ncpus = 1
        self.operations = {}
        self.process = []
        self.matches = []
        self.options = ["--recursive-includes"]
        dirList = listdir(self.get_datadir())
        for fname in dirList:
            op = _operation_name(fname)
            self.operations[op] = path.join(self.get_datadir(), fname)

    def setup(self, stype, attribute, operation):
        """
        :param stype: structure name, used to replace '$type' in the cocci file
        :type stype: str
        :param attribute: basically attribute of the structure, used to replace
            '$attribute' in the cocci file
        :type attribute: str
        :param operation: search operation to do
        :type operation: str
        :raise: :class:`CocciRunException`
        """
        self.type = stype
        self.attribute = attribute
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
        return False

    def add_options(self, olist):
        """
        Add option to spatch command

        :param olist: List of options
        :type olist: list of str
        """
        self.options += olist

    def set_cpp(self):
        """
        Activate coccinelle C++ support
        """
        self.add_options(["-c++"])

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
        return list(self.operations.keys())

    def get_operation_name(self, fname):
        return _operation_name(fname)

    def get_operation_info(self, op):
        return CocciPatch(self.operations[op])

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
                op = _operation_name(fname)
                self.operations[op] = fname

    def set_verbose(self):
        """
        Activate verbose mode
        """
        self.verbose = True

    def get_spatch_version(self):
        cmd = [self.spatch] + ['-version']
        try:
            output = Popen(cmd, stdout=PIPE, stderr=STDOUT).communicate()[0]
        except OSError as err:
            _raise_run_err(err, cmd)
        reg = r"version (.*?) with"
        m = re.search(reg, output.decode('utf8'))
        return m.group(1)

    def spatch_newer_than(self, version):
        from distutils.version import LooseVersion
        sversion = self.get_spatch_version()
        return LooseVersion(sversion) > LooseVersion(version)

    def run(self, files):
        """
        Run the search against the files and directories given in argument

        This function is doing the main job. It will run spatch with
        the correct parameters by using subprocess or it will use
        multiprocessing if a concurrency level greater than 1 has been
        asked.

        :param args: list of filenames and directory names
        :type args: list of str
        :raise: :class:`CocciRunException` or :class:`CocciConfigException`
        """

        if len(files) == 0:
            raise CocciRunException("Can't use coccigrep without files "
                "to search")

        # get version of spatch
        if self.spatch_newer_than("1.0.0-rc6"):
            cocci_op = "=~"
        else:
            cocci_op = "~="
        # create tmp cocci file:
        tmp_cocci_file = NamedTemporaryFile(suffix=".cocci", delete=not self.verbose)
        tmp_cocci_file_name = tmp_cocci_file.name
        # open file with name matching operation
        cocci_file = open(self.operations[self.operation], 'r')
        # get the string and build template
        cocci_tmpl = cocci_file.read()
        cocci_smpl_tmpl = Template(cocci_tmpl)
        cocci_file.close()
        # do substitution
        cocci_smpl = cocci_smpl_tmpl.substitute(type=self.type,
            attribute=self.attribute, cocci_regexp_equal=cocci_op)
        if '@filter@' in cocci_smpl:
            cocci_grep = cocci_smpl + CocciGrep.cocci_python_hdr_filter + CocciGrep.cocci_python
        else:
            cocci_grep = cocci_smpl + CocciGrep.cocci_python_hdr_std + CocciGrep.cocci_python

        if sys.version < '3':
            tmp_cocci_file.write(cocci_grep)
        else:
            tmp_cocci_file.write(bytes(cocci_grep, 'UTF-8'))
        tmp_cocci_file.flush()

        # launch spatch
        output = "".encode('utf8')
        # Launch parallel spatch
        if self.ncpus > 1 and len(files) > 1:
            fseq = []
            splitsize = 1.0 / self.ncpus * len(files)
            for i in range(self.ncpus):
                start = int(round(i * splitsize))
                end = int(round((i + 1) * splitsize))
                rfiles = files[start:end]
                if len(rfiles) >= 1:
                    fseq.append(rfiles)
            for sub_files in fseq:
                cmd = [self.spatch]
                cmd += self.options
                cmd += ["-sp_file", tmp_cocci_file.name]
                for cfile in sub_files:
                    include_dir = path.dirname(cfile)
                    if len(include_dir):
                        cmd += ["-I", include_dir]
                        break
                cmd += sub_files
                sprocess = CocciProcess(cmd, self.verbose)
                sprocess.start()
                self.process.append(sprocess)
            for process in self.process:
                ret = process.recv().decode('utf8')
                process.join()
                if not ret.startswith('cexceptions\n'):
                    # CocciProcess return a serialized exception
                    # in case of exception
                    output += ret.encode('utf8')
                    continue
                import json
                err = json.loads(ret)
                _raise_run_err(err, cmd)
            tmp_cocci_file.close()
        # Fallback to one spatch
        else:
            cmd = [self.spatch]
            cmd += self.options
            cmd += ["-sp_file", tmp_cocci_file.name]
            cmd += files
            include_dir = path.dirname(files[0])
            if len(include_dir):
                cmd += ["-I", include_dir]
            try:
                if self.verbose:
                    stderr.write("Running: %s.\n" % " ".join(cmd))
                    output = Popen(cmd, stdout=PIPE).communicate()[0]
                else:
                    output = Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()[0]
            except OSError as err:
                unlink(tmp_cocci_file_name)
                _raise_run_err(err, cmd)

            tmp_cocci_file.close()

        self.matches = []
        for ematch in output.decode('utf8').split("\n"):
            try:
                (efile, eline, ecol, elinend, ecolend) = ematch.split(":")
                nmatch = CocciMatch(efile, eline, ecol, elinend, ecolend, self)
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
        if before != 0 or after != 0:
            prev_match = None
            for index in range(len(self.matches)):
                cur_match = self.matches[index]
                cur_match.start_at = cur_match.line - before
                cur_match.stop_at = cur_match.line + after
                if cur_match.start_at < 1:
                    cur_match.start_at = 1

                if prev_match is not None:
                    prev_match.trailer = "--\n"
                    if prev_match.file == cur_match.file:
                        if prev_match.stop_at >= cur_match.line:
                            prev_match.stop_at = cur_match.line - 1
                        if prev_match.stop_at >= cur_match.start_at:
                            cur_match.start_at = prev_match.stop_at + 1

                        if prev_match.stop_at + 1 == cur_match.start_at:
                            # No separator if groups are contiguous
                            prev_match.trailer = ""

                prev_match = cur_match

        output = ''.join(match.display(self.type, mode=mode, oformat=oformat)
            for match in self.matches)

        return output.rstrip()
