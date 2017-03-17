from matches import Matches

class Proto():

    def __init__(self, name, cmd=None, tags=None, satisfaction_rules = None, completekey='tab', stdin=None, stdout=None):
        self.name = name
        self.children = []
        self.cmd = cmd
        self.tags = tags if tags else []
        self.satisfaction_rules = satisfaction_rules if satisfaction_rules else []


        # cmd loop stuff
        import sys
        if stdin is not None:
            self.stdin = stdin
        else:
            self.stdin = sys.stdin
        if stdout is not None:
            self.stdout = stdout
        else:
            self.stdout = sys.stdout
        self.cmdqueue = []
        self.completekey = completekey


    def __repr__(self):
        s = "<Proto " + self.name
        s += ": cmd=" + str(self.cmd)
        s += ". tags=" + str(self.tags)
        s += ">"
        return s

    def execute(self, str_input):
        print "execute {} called on '{}'".format(self.name, str_input)


    def add_child(self, proto):
        self.children.append(proto)



    def add_rule_one_of(self, tag):
        self.satisfaction_rules.append(
            lambda resolver: len([x for x in resolver.resolved if tag in x.tags]) == 1)

    def add_tag(self, tag):
        self.tags.append(tag)



    def resolve_line(self, segments):
        """
            from input return a tuple (self.resolution,[partially resolved children],[unresolved children])

            case1: no resolution.
            case2: partial resolution. self contains input, but input does not contains self.
            case3: exact resolution. self == input. input resolves to self with no further input.
            case4: extra resolution. input contains self and there is more input to resolve. delegate
                    further resolution to children
        """

        if len(segments) == 0:
            # If nothing is given as the input, then it matches anything as a fragment
            return Matches([],[self],[],[])


        seg0 = segments[0].strip()

        if self.name.startswith(seg0):
            if self.name != seg0:
                # fragment resolution. Terminal condition.
                return Matches([],[self],[],[])

        elif not seg0.startswith(self.name):
            # unresolved, Terminal condition.
            return Matches([],[],[self],[])

            # If we're here, then self matched the first input segment. Continue resolving children.
        matches = Matches()
        for c in self.children:
            matches.extend(c.resolve_line(segments[1:]))

        if matches.satisfies(self.satisfaction_rules):
            matches.resolved.append(self)
        else:
            matches.unsatisfied.append(self)

        return matches



    def do(self, segments):

        print('do called on {}'.format(segments))

        matches = self.resolve_line(segments)

        if len(matches.resolved) == 0:
            print 'No commands resovled'
            return
        elif len(matches.resolved) > 1:
            print 'ambiguous command. These resovled: ',  matches.resolved
            return


        matches.resolved[0].cmd()

        # if cmd.strip() == self.name:
        #     print "do called for {} on '{}', '{}'".format(self.name, cmd, args)

        # if cmd.strip() != self.name and not self.cmd:
        #     return []
        #
        # if not self.children:
        #     return [self]
        # cmds = []
        # if args != None:
        #     segs = args
        #     for c in self.children:
        #         cmds.extend(c.do(segs[0], ' '.join(segs[1:])))
        # return cmds


    def complete(self, line):
        return self.resolve_line(line.split()).fragment

