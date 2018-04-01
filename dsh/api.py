import six, shlex

UNEVALUATED = 'UNEVALUATED'


MATCH_NONE = 'NONE'             # No Match
MATCH_EMPTY = 'EMPTY'           # Matched against empty input
MATCH_FRAGMENT = 'FRAGMENT'     # Matched input as a fragment against current node
MATCH_FULL = 'FULL'             # Matched input fully against current node

# STATUS_INITIAL = 'INITIAL'
STATUS_UNSATISFIED = 'UNSATISFIED'
STATUS_SATISFIED = 'SATISFIED'
STATUS_COMPLETED = 'COMPLETED'
STATUS_EXCEEDED = 'EXCEEDED'

MODE_COMPLETE = 'MODE_COMPLETE'
MODE_EXECUTE = 'MODE_EXECUTE'

NODE_ANONYMOUS_PREFIX = '_ANON_'

CTX_VAR_PATH =      '_DSH_CTX_PATH'
CTX_VAR_SRC_DIR =   '_DSH_CTX_SRC_DIR'

#
#   Exceptions
#
class NodeUnsatisfiedError(Exception):
    pass

class NodeExecutionFailed(Exception):
    pass



class MatchResult(object):

    def __init__(self, status=MATCH_NONE, input=[], start=0, stop=0, completions=[]):
        self.status = status
        self.input = input
        self.start = start
        self.stop = stop
        self.completions = completions[:]

    def matched_input(self):
        return self.input[self.start:self.stop+1]

    def input_remainder(self):
        return self.input[self.stop+1:]

    @staticmethod
    def from_input(input, start=None, stop=None):
        if input and isinstance(input, six.string_types):
            input = shlex.split(input)
        else:
            input = []
        return MatchResult(
            MATCH_FULL,
            input,
            start if start else 0,
            stop if stop else len(input)-1)




DSH_VERBOSE = "__DSH_VERBOSE__"
def verbose(ctx):
    try:
        return ctx[DSH_VERBOSE]
    except:
        return False





#
#
#   Var substitutions
#
#
import re
VAR_FORMAT_PATTERN = re.compile(r'{{(\w*)}}')


def __format(target, sources=[]):

    # do the replacements of {{var}} style vars.
    #   m.group()  ->  {{var}}
    #   m.group(1) ->  var
    #
    while True:
        replacements = 0
        varmatches = re.finditer(VAR_FORMAT_PATTERN, target)
        if varmatches:
            for m in varmatches:
                for src in sources:
                    # If the matching key is found in the source, make the substitution
                    if src and m.group(1) in src:
                        # print 'replacing {} with {}'.format(m.group(), src[m.group(1)])
                        target = target.replace(m.group(), src[m.group(1)])
                        replacements += 1
        if replacements == 0:
            break

    return target


def __format_dict(env, argvars={}):
    subsenv = {}
    if env:
        for k in env:
            # for each env var, do recursive substitution
            try:
                subsenv[k] = __format(env[k], [argvars, env])
            except:
                pass
    return subsenv



