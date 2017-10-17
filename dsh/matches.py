
class Matches():

    def __init__(self,
                 resolved = None,
                 fragment = None,
                 unresolved = None,
                 unsatisfied = None):

        self.resolved = [] # resolved if resolved else []
        self.fragment = fragment if fragment else []
        self.unresolved = unresolved if unresolved else []
        self.unsatisfied = unsatisfied if unsatisfied else []


    def extend(self, resolver):

        self.resolved.extend(resolver.resolved)
        self.fragment.extend(resolver.fragment)
        self.unresolved.extend(resolver.unresolved)
        self.unsatisfied.extend(resolver.unsatisfied)


    def gather_not_resolved(self, filter_func):
        filtered = filter(filter_func, self.fragment)
        filtered.extend(filter(filter_func, self.unresolved))
        filtered.extend(filter(filter_func, self.unsatisfied))
        return filtered


    def satisfies(self, rules):
        for rule in rules:
            if not rule(self):
                return False
        return True


    def __str__(self):

        p = lambda x: "'{}'".format(x.name)

        str = 'matched:'
        for x in self.resolved:
            str += p(x)
        str +=  '. match candidates:'
        for x in self.fragment:
            str += p(x)
        str +=  '. unmatched:'
        for x in self.unresolved:
            str  += p(x)
        str +=  '. matched unsatisfied:'
        for x in self.unsatisfied:
            str  += p(x)
        return str
