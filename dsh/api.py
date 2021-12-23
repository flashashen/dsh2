import shlex
import dpath.util

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
CTX_VAR_WORK_DIR =   '_DSH_CTX_WORK_DIR'
CTX_VAR_FLANGE =   '_DSH_CTX_FLANGE'

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
        if input and isinstance(input, str):
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
# import re
# VAR_FORMAT_PATTERN = re.compile(r'{{(\w+(.\w*)*)}}')


def __get_sub(target, sources):
    # print('get sub on {}'.format(target))
    for src in sources:
        if not src or not isinstance(src, dict):
            continue

        val = None
        try:
            val = dpath.util.get(src, target.replace('.', '/'))
        except KeyError:
            pass

        if val:
            # print 'format group: {}, src: {}'.format(m.group(), src)
            if not isinstance(val, str):
                raise ValueError("Substitution target is not a string type: '{}' is a {}".format(target, type(val)))

            return val



def __find_vars(s):

    state = 0
    vars = []
    pos_start = 0
    counter = 0


    STATE_WAIT_OPEN = 0
    STATE_OPENING = 1
    STATE_CLOSING = 2

    for i in range(len(s)):
        c = s[i]

        # print 'state: {}. pos: {}. char: {}'.format(state, i, c)
        if state == STATE_WAIT_OPEN:
            # waiting for first opening bracket
            if c == '{':
                pos_start = i
                # count open brackets
                counter = 1
                state = STATE_OPENING

        elif state == STATE_OPENING:
            if c == '{':
                counter += 1
                pos_start = i-1
            else:
                if counter >= 2:
                    state = STATE_CLOSING
                    counter = 1 if c == "}" else 0
                else:
                    state = STATE_WAIT_OPEN

        elif state == STATE_CLOSING:
            if c == '{' and s[i-1] == '{':
                # a nested var has been found
                state == STATE_OPENING
                counter = 2
                pos_start = i-1
            elif c == '}':
                counter +=1
                if counter >= 2:
                    vars.append((s[pos_start+2:i-1], pos_start, i+1))
                    state = STATE_WAIT_OPEN
            else:
                # reset the counter but stay here looking for closing bracket
                counter = 0

    return vars





def __format(target, sources=[]):

    while True:
        replacements = 0
        varmatches = __find_vars(target)
        if varmatches:
            for m in varmatches:
                sub = __get_sub(m[0], sources)
                if not sub:
                    pass # print("Substitution not found for {:20} in: {}".format(m[0], target))
                else:
                    # print('replacing {} with {}'.format(m[0], sub))
                    target = target.replace('{{' + m[0] + '}}', sub)
                    replacements += 1

        # When nothing more can be replaced, exit.
        if replacements == 0:
            break

    return target


def format_dict(env, argvars={}):
    subsenv = {}
    if env:
        for k in env:
            # print('formatting key {}'.format(k))
            # for each env var, do recursive substitution
            try:
                if isinstance(env[k], dict):
                    subsenv[k] = format_dict(env[k])
                else:
                    # print('formatting string {}'.format(env[k]))
                    subsenv[k] = __format(env[k], [argvars, env])
            except:
                pass
    return subsenv



