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
