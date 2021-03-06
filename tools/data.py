from mstutil import compare_float, get_path_to_generated_inputs, get_path_to_project_root, get_path_to_tools_root
import os, re, sys

# whether to return pretty-printed input paths quickly or with more helpful info
FAST_INPUT_PATH_PRETTY_PRINT = False

class DataError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class DataSet:
    """A collection of Data objects"""
    def __init__(self, dataset):
        self.dataset = dataset

    def add_data(self, data):
        """Inserts or updates the dataset and returns true if anything changed."""
        key = data.mykey()
        if self.dataset.has_key(key):
            old = self.dataset[key]
            if old == data:
                return False
        self.dataset[key] = data
        return True

    def save_to_file(self, logfn):
        """Saves the dataset to the specified log file in sorted order"""
        sorted_data = sorted(self.dataset.values())
        try:
            fh = open(logfn, "w")
            if len(sorted_data) > 0:
                fh.write(sorted_data[0].header_row() + '\n')
            for d in sorted_data:
                fh.write('%s\n' % str(d))
            fh.close()
        except IOError, e:
            raise DataError("I/O error while writing to %s: %s" % (logfn, e))

    @classmethod
    def read_from_file(cls, cls_data, logfn, mustExist=False):
        """Factory method which populates a DataSet composed of cls_data
        type objects with the contents of a file."""
        dataset = {}
        if not mustExist and not os.path.exists(logfn):
            return cls(dataset)
        try:
            fh = open(logfn, "r")
            lines = fh.readlines()
            for line in lines:
                if line[0:1] != '#':
                    s = line.split()
                    t = cls_data.from_list(s)
                    dataset[t.mykey()] = t
            fh.close()
        except IOError, e:
            raise DataError("I/O error while reading in %s: %s" % (logfn, e))
        except ValueError, e:
            fh.close()
            raise DataError("Improper value encountered while reading in %s: %s" % (logfn, e))
        return cls(dataset)

    @classmethod
    def add_data_to_log_file(cls, data, logfn=None):
        """Adds data to the appropriate log file."""
        if logfn is None:
            logfn = data.get_path()
        ds = cls.read_from_file(data.__class__, logfn)
        if ds.add_data(data):
            ds.save_to_file(logfn)

class Input:
    """Data based on some input"""
    def __init__(self, prec, dims, min_val, max_val, num_verts, num_edges, seed):
        self.prec      = int(prec)
        self.dims      = int(dims)
        self.min       = float(min_val)
        self.max       = float(max_val)
        self.num_verts = int(num_verts)
        self.num_edges = int(num_edges)
        self.seed      = int(seed)

    def get_wtype(self):
        if self.prec!=15 or self.min!=0 or self.max!=1:
            return None
        if self.dims > 0:
            return 'loc%u' % self.dims
        else:
            return 'edge'

    def make_args_for_generate_input(self):
        """Returns a string which can  be used to make generate_input.py generate this input."""
        argstr = '-p %u -n %u %u -r %s' % (self.prec, self.num_edges, self.num_verts, str(self.seed))
        if self.dims == 0 and (self.min!=0 or self.max!=100000):
            argstr += ' -e %.1f,%.1f' % (self.min, self.max)
        elif self.dims > 0:
            argstr += ' -v %u,%.1f,%.1f' % (self.dims, self.min, self.max)
        return argstr

    def __cmp__(self, other):
        """Provides some ordering on Input"""
        if self.prec != other.prec:
            return self.prec - other.prec
        if self.dims != other.dims:
            return self.dims - other.dims
        if self.min < other.min:
            return -1
        if self.min > other.min:
            return 1
        if self.max < other.max:
            return -1
        if self.max > other.max:
            return 1
        if self.num_verts != other.num_verts:
            return self.num_verts - other.num_verts
        if self.num_edges != other.num_edges:
            return self.num_edges - other.num_edges
        if self.seed < other.seed:
            return -1
        if self.seed > other.seed:
            return 1
        return 0

    def __hash__(self):
        """Simple hash on vertices, edges, and the seed"""
        ret = self.num_verts
        ret = ret * 31 + self.num_edges
        return ret * 31 + self.seed

    def __str__(self):
        fmt = "%s\t%u\t%s\t%s\t%u\t%u\t%s"
        return fmt % (str(self.prec), self.dims, str(self.min), str(self.max),
                      self.num_verts, self.num_edges, str(self.seed))

    def header_row(self):
        max_sp_len = len(str(self.max)) - 3
        max_sp = ' ' * max_sp_len
        return "#Prec\tDim\tMin\tMax%s\t|V|\t|E|\tSeed               " % max_sp

class AbstractData:
    def __init__(self, prec, dims, min_val, max_val, num_verts, num_edges, seed):
        self.__input = Input(prec, dims, min_val, max_val, num_verts, num_edges, seed)

    def input(self):
        return self.__input

    def mykey(self):
        return self.__input

    def __cmp__(self, other):
        return self.input().__cmp__(other.input())

    def __hash__(self):
        return self.input().__hash__()

    def __str__(self):
        return self.input().__str__()

    def header_row(self):
        return Input.header_row(self.input())

class InputSolution(AbstractData):
    """Data about about how to generate an input and the MST weight of that input (if known)."""
    def __init__(self, prec, dims, min_val, max_val, num_verts, num_edges, seed, mst_weight='-1'):
        AbstractData.__init__(self, prec, dims, min_val, max_val, num_verts, num_edges, seed)
        self.mst_weight = float(mst_weight)

    def get_path(self):
        i = self.input()
        return InputSolution.get_path_to(i.prec, i.dims, i.min, i.max)

    def has_mst_weight(self):
        """Whether the MST weight is known for this input"""
        return self.mst_weight >= 0

    def update_mst_weight(self, w):
        """Updates the mst_weight field (returns True if any changes occur)"""
        if self.mst_weight != w:
            self.mst_weight = w
            return True
        else:
            return False

    def __cmp__(self, other):
        ret = AbstractData.__cmp__(self, other)
        if ret != 0:
            return ret
        else:
            return compare_float(self.mst_weight, other.mst_weight)

    def __str__(self):
        return AbstractData.__str__(self) + '\t' + str(self.mst_weight)

    def header_row(self):
        return AbstractData.header_row(self) + "\tCorrectMSTWeight"

    @staticmethod
    def key(prec, dims, min_val, max_val, num_verts, num_edges, seed):
        return Input(prec, dims, min_val, max_val, num_verts, num_edges, seed)

    @staticmethod
    def from_list(lst):
        if(len(lst) != 8):
            raise DataError('InputSolution expected 8 args, got %u: %s' % (len(lst), str(lst)))
        return InputSolution(lst[0], lst[1], lst[2], lst[3], lst[4], lst[5], lst[6], lst[7])

    @staticmethod
    def get_path_to(prec, dims, min_val, max_val):
        may_be_part2_input = (prec==15 and min_val==0 and max_val==1)
        if dims == 0:
            if prec==1 and min_val==0 and max_val==100000:
                logbasename = 'perf.inputs'
            elif may_be_part2_input:
                logbasename = 'p2-redge.inputs'
            else:
                logbasename = 'other-redge.inputs'
        else:
            if may_be_part2_input and dims>=2 and dims<=4:
                logbasename = 'p2-rvert-%ud.inputs' % dims
            else:
                logbasename = 'other-rvert.inputs'
        return get_path_to_project_root() + 'input/' + logbasename

class AbstractResult(AbstractData):
    """Data about an input and a revision on which we ran a test on it."""
    def __init__(self, prec, dims, min_val, max_val, num_verts, num_edges, seed, rev, run_num):
        AbstractData.__init__(self, prec, dims, min_val, max_val, num_verts, num_edges, seed)
        self.rev = str(rev)
        self.run_num = int(run_num)
        if len(self.rev) == 0:
            self.rev = 'n/a'

    def get_path(self):
        return self.get_path_to(self.rev)

    def mykey(self):
        return (self.input(), self.run_num)

    def __cmp__(self, other):
        ret = AbstractData.__cmp__(self, other)
        if ret != 0:
            return ret
        elif self.rev < other.rev:
            return -1
        elif self.rev > other.rev:
            return 1
        else:
            return self.run_num - other.run_num

    def __str__(self):
        return AbstractData.__str__(self) + ('\t%s\t%s' % (self.rev, str(self.run_num)))

    def header_row(self):
        rev_sp_len = len(str(self.rev)) - 3
        rev_sp = ' ' * rev_sp_len
        return AbstractData.header_row(self) + "\tRev%s\tRun#" % rev_sp

    @staticmethod
    def get_path_to(rev):
        raise DataError('get_path_to should be overriden in AbstractResult children')

CORRECT = int(True)
INCORRECT = int(False)
class CorrResult(AbstractResult):
    """Data about an input, a revision, and whether mst correctly found the MST."""
    def __init__(self, dims, min_val, max_val, num_verts, num_edges, seed, rev, run_num, corr, prec=1):
        AbstractResult.__init__(self, prec, dims, min_val, max_val, num_verts, num_edges, seed, rev, run_num)
        corr = int(corr)
        if corr!=CORRECT and corr!=INCORRECT:
            raise ValueError('invalid corr value: ' + str(corr))
        self.corr = corr
        if self.input().prec != 1:
            print >> sys.stderr, 'warning: correctness result with precision %u (expected 1)' % self.input().prec

    def is_correct(self):
        return self.corr == CORRECT

    def __cmp__(self, other):
        ret = AbstractResult.__cmp__(self, other)
        if ret != 0:
            return ret
        else:
            return (0 if self.corr==other.corr else (1 if self.corr else -1))

    def __str__(self):
        return AbstractResult.__str__(self) + ('\t%u' % self.corr)

    def header_row(self):
        return AbstractResult.header_row(self) + '\tCorrect?'

    @staticmethod
    def key(dims, min_val, max_val, num_verts, num_edges, seed, run_num, prec=1):
        return (Input(prec, dims, min_val, max_val, num_verts, num_edges, seed), run_num)

    @staticmethod
    def from_list(lst):
        if(len(lst) != 10):
            raise DataError('CorrResult expected 10 args, got %u: %s' % (len(lst), str(lst)))
        return CorrResult(prec=lst[0], dims=lst[1], min_val=lst[2], max_val=lst[3], num_verts=lst[4],
                          num_edges=lst[5], seed=lst[6], rev=lst[7], run_num=lst[8], corr=lst[9])

    @staticmethod
    def get_path_to(rev):
        path = get_path_to_project_root() + 'result/corr/'
        if not os.path.exists(path):
            os.makedirs(path)
        return path + rev

class PerfResult(AbstractResult):
    """Data about an input, a revision, and how quickly it found the MST."""
    def __init__(self, num_verts, num_edges, seed, rev, run_num, time_sec, mst_weight, prec=1, dims=0, min_val=0, max_val=100000):
        AbstractResult.__init__(self, prec, dims, min_val, max_val, num_verts, num_edges, seed, rev, run_num)
        self.time_sec = float(time_sec)
        self.mst_weight = float(mst_weight)
        i = self.input()
        if i.prec != 1:
            print >> sys.stderr, 'warning: performance result with precision %u (expected 1)' % i.prec
        if i.dims != 0:
            print >> sys.stderr, 'warning: performance result with dimensionality %u (expected 0)' % i.dims
        if i.min != 0:
            print >> sys.stderr, 'warning: performance result with min_val %s (expected 0)' % str(i.min)
        if i.max != 100000:
            print >> sys.stderr, 'warning: performance result with max_val %s (expected 100000)' % str(i.max)

    def __cmp__(self, other):
        ret = AbstractResult.__cmp__(self, other)
        if ret != 0:
            return ret
        else:
            return compare_float(self.time_sec, other.time_sec)

    def __str__(self):
        return AbstractResult.__str__(self) + ('\t%.2f' % self.time_sec) + ('\t%.1f' % self.mst_weight)

    def header_row(self):
        return AbstractResult.header_row(self) + '\tTime(sec)\tMSTWeight'

    @staticmethod
    def key(num_verts, num_edges, seed, run_num, prec=1, dims=0, min_val=0, max_val=100000):
        return (Input(prec, dims, min_val, max_val, num_verts, num_edges, seed), run_num)

    @staticmethod
    def from_list(lst):
        if(len(lst) != 11):
            raise DataError('PerfResult expected 11 args, got %u: %s' % (len(lst), str(lst)))
        return PerfResult(prec=lst[0], dims=lst[1], min_val=lst[2], max_val=lst[3], num_verts=lst[4],
                          num_edges=lst[5], seed=lst[6], rev=lst[7], run_num=lst[8], time_sec=lst[9], mst_weight=lst[10])

    @staticmethod
    def get_path_to(rev):
        path = get_path_to_project_root() + 'result/perf/'
        if not os.path.exists(path):
            os.makedirs(path)
        return path + rev

class WeightResult(AbstractResult):
    """Data about an input, a revision, and the weight of the MST."""
    def __init__(self, dims, num_verts, seed, rev, run_num, mst_weight, prec=15, min_val=0, max_val=1, num_edges=None):
        num_edges = num_edges if num_edges is not None else int(num_verts)*(int(num_verts)-1)/2
        AbstractResult.__init__(self, prec, dims, min_val, max_val, num_verts, num_edges, seed, rev, run_num)
        self.mst_weight = float(mst_weight)
        i = self.input()
        if i.prec != 15:
            print >> sys.stderr, 'warning: weight result with precision %u (expected 15)' % i.prec
        if i.min != 0:
            print >> sys.stderr, 'warning: weight result with min_val %s (expected 0)' % str(i.min)
        if i.max != 1:
            print >> sys.stderr, 'warning: weight result with max_val %s (expected 1)' % str(i.max)
        exp_edges = i.num_verts*(i.num_verts-1)/2
        if i.num_edges != exp_edges:
            print >> sys.stderr, 'warning: weight result with num_edges %u (expected complete graph, i.e., %u)' % (i.num_edges, exp_edges)

    def get_path(self):
        return self.get_path_to(self.input().get_wtype())

    def __cmp__(self, other):
        ret = AbstractResult.__cmp__(self, other)
        if ret != 0:
            return ret
        else:
            return compare_float(self.mst_weight, other.mst_weight)

    def __str__(self):
        return AbstractResult.__str__(self) + ('\t%.15f' % self.mst_weight)

    def header_row(self):
        return AbstractResult.header_row(self) + '\tMST Weight'

    @staticmethod
    def key(dims, num_verts, seed, run_num, prec=15, min_val=0, max_val=1, num_edges=None):
        return (Input(prec, dims, min_val, max_val, num_verts,
                      num_edges if num_edges is not None else num_verts*(num_verts-1)/2, seed), run_num)

    @staticmethod
    def from_list(lst):
        if(len(lst) != 10):
            raise DataError('WeightResult expected 10 args, got %u: %s' % (len(lst), str(lst)))
        return WeightResult(prec=lst[0], dims=lst[1], min_val=lst[2], max_val=lst[3], num_verts=lst[4],
                            num_edges=lst[5], seed=lst[6], rev=lst[7], run_num=lst[8], mst_weight=lst[9])

    @staticmethod
    def get_path_to(wtype):
        path = get_path_to_project_root() + 'result/weight/'
        if not os.path.exists(path):
            os.makedirs(path)
        return path + wtype

class ExtractInputFooterError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

def __re_get_group(pattern, haystack, group_num=0):
    """Returns the value associated with the requested group num in the result
    from re.search, or raises an ExtractInputFooterError if it does not match"""
    x = re.search(pattern, haystack)
    if x is None:
        raise ExtractInputFooterError('pattern match failed for ' + pattern + ' in ' + haystack)
    else:
        return x.groups()[group_num]

def extract_input_footer(input_graph):
    """Returns the Input object representing the footer info"""
    lines = os.popen('tail -n 1 "%s" 2> /dev/null' % input_graph).readlines()
    if len(lines) == 0:
        raise ExtractInputFooterError("Failed to extract the footer from " + input_graph)
    about = lines[0]

    try:
        num_dims = int(__re_get_group(r' d=(\d*)', about))
    except ExtractInputFooterError:
        num_dims = 0

    num_verts = int(__re_get_group(r' m=(\d*)', about))
    num_edges = int(__re_get_group(r' n=(\d*)', about))
    min_val = float(__re_get_group(r' min=(\d*.\d*)', about))
    max_val = float(__re_get_group(r' max=(\d*.\d*)', about))
    precision = int(__re_get_group(r' prec=(\d*)', about))
    seed = int(__re_get_group(r' seed=(\d*)', about))
    return Input(precision, num_dims, min_val, max_val, num_verts, num_edges, seed)

def ppinput_fast(path):
    """Returns the path to an input_graph in 'printy-printed' string."""
    root_path = get_path_to_generated_inputs()
    n = len(root_path)
    if path[:n] == root_path:
        return path[n:]
    else:
        return path

def ppinput(path):
    """Returns the path to an input_graph in 'printy-printed' string."""
    if FAST_INPUT_PATH_PRETTY_PRINT:
        return ppinput_fast(path)
    else:
        try:
            inpt = extract_input_footer(path)
            return 'I(%s)' % inpt.make_args_for_generate_input()
        except ExtractInputFooterError:
            return ppinput_fast(path)

def get_tracked_revs():
    """Returns revisions we are tracking as an array of SHA1 revision IDs"""
    ret = []
    try:
        fh = open(get_path_to_tools_root() + 'conf/tracked_revs', "r")
        lines = fh.readlines()
        for line in lines:
            if line[0:1] != '#':
                s = line.split('\t', 5)
                if len(s) != 5:
                    raise DataError('line should have five columns (has %d): %s' % (len(s), line))
                ret.append(s[2])
        fh.close()
        return ret
    except IOError, e:
        raise DataError('I/O error while reading tracked revisions: ' + e)

def get_tracked_algs_and_revs():
    """Returns dict mapping algorithms we are tracking to lists of SHA1 revision IDs in which they are tested."""
    # maps alg name to list of revisions
    ret = {}
    try:
        fh = open(get_path_to_tools_root() + 'conf/tracked_revs', "r")
        lines = fh.readlines()
        for line in lines:
            if line[0:1] != '#':
                s = line.split('\t', 5)
                if len(s) != 5:
                    raise DataError('line should have five columns (has %d): %s' % (len(s), line))
                rev = s[2]
                tag = s[3]
                if ret.has_key(tag):
                    ret[tag].append(rev)
                else:
                    ret[tag] = [rev]
        fh.close()
        return ret
    except IOError, e:
        raise DataError('I/O error while reading tracked revisions: ' + e)
