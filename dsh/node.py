import random, string, six, os, traceback, sys, shlex, os, contextlib
import api
import matchers
import executors
import evaluators




def node_container(name=None, method_evaluate=None, usage=None, ctx=None):
    '''
    Create a container node that delegates responsibilities to children. It
    consumes no input and just propagates child execution results up. It's used
    for grouping child nodes for different evaluation rules.
    '''
    # eval =
    return CmdNode(
        # if no name, generate a random one
        name=name,
        usage=usage,
        context=ctx,
        method_match=matchers.match_always_consume_no_input,
        method_evaluate=method_evaluate if method_evaluate else evaluators.require_all_children,
        method_execute=executors.get_executor_return_child_results())


def node_any_value_for(name, usage=None):
    node = CmdNode(
        name,
        usage=usage,
        method_match=matchers.get_matcher_exact_string(name),
        method_evaluate=evaluators.choose_one_child,
        method_execute=executors.get_executor_return_child_result_value())
    node.add_child(node_free_value())
    return node



def node_choose_value_for(name, choices, usage=None):
    children = get_nodes_from_choices(choices)
    message = usage if usage else '{} {}'.format(name, choices)
    node = CmdNode(
        name,
        usage=message,
        method_evaluate=evaluators.choose_one_child,
        method_execute=executors.get_executor_return_child_result_value())
    f = executors.get_executor_return_matched_input()
    for choice in children:
        choice.method_execute=f
        node.add_child(choice)
    return node



def node_argument(name, choices=None):

    if choices:
        return node_choose_value_for(name, choices)
    else:
        node = CmdNode(
            name,
            method_match=matchers.get_matcher_exact_string(name),
            method_execute=executors.get_executor_return_child_result_value())
        node.add_child(node_free_value(name + "_free_val"))
        return node



def get_nodes_from_choices(nodes):
    children = []

    if isinstance(nodes, six.string_types):
        nodes = nodes.split()
    for node in nodes:
        children.append(node if isinstance(node, CmdNode) else node_string(node))
    return children


def node_option(name):
    return CmdNode(
        name,
        initial_status=api.STATUS_SATISFIED,
        method_match=matchers.get_matcher_exact_string(name),
        method_evaluate=evaluators.no_children,
        method_execute=executors.get_executor_return_matched_input)


def node_free_value(name=None):
    return CmdNode(
        method_match=matchers.match_any_word,
        method_evaluate=evaluators.no_children,
        method_execute=executors.get_executor_return_matched_input())


def node_string(s):
    return CmdNode(
        method_match=matchers.get_matcher_exact_string(s),
        method_evaluate=evaluators.no_children,
        method_execute=executors.get_executor_return_matched_input())



def node_root(name='root', ctx=None):

    n = CmdNode(
        name,
        method_match=matchers.match_always_consume_no_input,
        method_evaluate=evaluators.choose_one_child,
        context=ctx)
    n.execute = lambda matched_input, child_results: executors.get_executor_return_child_results()
    return n



def node_shell_command(name, command, return_output=True, ctx=None):

    # repeat the test with variable substitution in the command string
    n = CmdNode(name, context=ctx)
    n.execute = executors.get_executor_shell_cmd(name, command, return_output, ctx=ctx)
    return n



def node_python(name, method, args_required=None, args_optional=None, options=None, ctx=None):
    # Return a node that executes a python method. By default, children are all required, which
    # is with the expectation that containers like allOf and oneOf will be used to group arguments.
    m = CmdNode(
        name,
        method_match=matchers.get_matcher_exact_string(name),
        method_evaluate=evaluators.require_all_children,
        method_execute=executors.get_executor_python(method),
        context=ctx)


    if options:
        m.options(options)

    if args_required:
        m.all_of(args_required)

    if args_optional:
        c = node_container(method_evaluate=evaluators.children_as_options)
        for arg in args_optional:
            c.add_child(arg if isinstance(arg, CmdNode) else node_argument(arg))


    return m






class CmdNode(object):

    def __init__(self,
                 name=None,
                 usage=None,
                 method_execute=None,
                 method_match=None,
                 method_evaluate=None,
                 child_get_func=None,
                 context=None,
                 initial_status=api.STATUS_UNSATISFIED):

        self.name = name if name else api.NODE_ANONYMOUS_PREFIX + ''.join([random.choice(string.ascii_letters+string.digits) for n in range(8)])
        self.context = context if context else {}
        self.usage = usage
        self.execute = method_execute if method_execute else executors.get_executor_noop()
        self.match = method_match if method_match else matchers.get_matcher_exact_string(name)
        self.evaluate = method_evaluate if method_evaluate else evaluators.choose_one_child
        self.initial_status = initial_status

        if child_get_func:
            self.get_children = child_get_func
        else:
            children = []
            self.__children = children
            self.get_children = lambda: children




    def __repr__(self):

            try:
                c = self.__children
            except:
                c = []

            return "<CmdNode:{}>".format(self.name)



    #
    #
    #   Builder methods
    #
    #

    def add_child(self, node):

        try:
            len(self.__children)
        except:
            raise ValueError("add_child() cannot be called if a get_children method has been provided ")

        if node:
            self.__children.append(node if isinstance(node, CmdNode) else CmdNode(node))

        return self



    def add(self, nodes):

        for node in get_nodes_from_choices(nodes):
            self.add_child(node)

        return self


    def any_value_for(self, name):
        self.add_child(node_any_value_for(name))
        return self

    def choose_value_for(self, name, choices):
        self.add_child(node_choose_value_for(name, choices))
        return self


    def one_of(self, choices):
        self.add_child(
            node_container(method_evaluate=evaluators.choose_one_child).
                add(choices))
        return self


    def all_of(self, choices):
        self.add_child(
            node_container(method_evaluate=evaluators.require_all_children).
                add(choices))
        return self


    def options(self, options):

        for opt in options:
            if not isinstance(opt, six.string_types):
                raise ValueError('options must be strings. got {}'.format(type(opt)))
            self.add_child(node_option(opt))
        return self


    def resolve(self, matched_input):
        path = ResolutionPath(self)
        if matched_input and isinstance(matched_input, six.string_types):
            matched_input = shlex.split(matched_input)
        ResolutionPath.resolve(path, matched_input if matched_input else [])
        return path





@contextlib.contextmanager
def given_dir(path):
    """
    Usage:
    >>> with given_dir(prj_base):
    ...   subprocess.call('project_script.sh')
    """
    if not path:
        yield

    starting_directory = os.getcwd()
    try:
        os.chdir(os.path.abspath(os.path.expanduser(path)))
        yield
    finally:
        os.chdir(starting_directory)



def get_children_method_dir_listing(dir='.'):
    import glob
    def dir_listing():
        with given_dir(dir):
            return [CmdNode(p) for p in glob.glob('*')]
    return dir_listing




class ResolutionPath:

    '''
    A tree structure that realizes an input against the node tree.

    '''
    def __init__(self, node):

        self.cmd_node = node

        self.status = node.initial_status
        self.match_result = api.MatchResult()
        self.exe_result = None

        # lazy initialized list of children paths which wrap cmd_node.children
        self.children = []

        # list of children in order of resolution. From this list the input could be reconstructed
        self.resolutions = []


    @staticmethod
    def resolve(path, input_segments, start_index=0, input_mode=api.MODE_COMPLETE):

        path.match_result = path.cmd_node.match(input_segments, start_index)
        if path.match_result.status not in [api.MATCH_FULL]:
            return

        # Call the cmd node get_children method. Children can be dynamic based on context and
        # external conditions. Its up to the resolver for now to be careful with this feature.
        # something will need to be done later to optimize so that slow calls aren't made more
        # than is necessary
        node_children = path.cmd_node.get_children()
        if not node_children:
            path.status = path.cmd_node.evaluate([])
            return


        path.children = [ResolutionPath(child) for child in node_children]
        start_index = path.match_result.stop

        while True:

            # if input_mode != MODE_COMPLETE and start_index >= len(input_segments):
            #     # No more input so nothing to resolve except completions against empty input
            #     break

            remaining_children = [child for child in path.children if child not in path.resolutions]
            if not remaining_children:
                break

            # depth first traversal, resolving against current position in input.
            # print 'resolving children of ', path.cmd_node.name
            for child in remaining_children:
                ResolutionPath.resolve(child, input_segments, start_index, input_mode)
                # if child.match_result.matched_input():
                #     print child.cmd_node.name, ':', child.match_result


                # INVARIANT - Children have all resolved as much input as possible on current input,index.

            # re-evaluate status
            path.status = path.cmd_node.evaluate([child.status for child in path.children])

            # select child that resolved best. First, select based on amount of input consumed,
            # then take the completed, then take the satisfied, then take whichever is first
            ranked = sorted(remaining_children, reverse=True, key=lambda child: child.get_match_score())


            if ranked[0].amount_input_consumed():

                # case 1: one child consumed most input, even counting fragment matches
                #   -> winner contributes completions, etc. resolution is over and solely dependent on this winning child
                if len(ranked) == 1 or ranked[0].amount_input_consumed() > ranked[1].amount_input_consumed():

                    # As children are resolved, append to the resolved list so they won't be processed again
                    # and also so we can re-construct the 'path' of resolution
                    path.resolutions.append(ranked[0])

                    # Stop index and completions come from winner
                    path.match_result.stop = ranked[0].match_result.stop
                    path.match_result.completions = ranked[0].match_result.completions[:]

                    # If the winner is unsatisfied, then don't give its peers a chance to consume more input.
                    # Otherwise change the index into the input and see if its peers can do something with the
                    # remaining input
                    if ranked[0].status not in (api.STATUS_SATISFIED, api.STATUS_COMPLETED):
                        break
                    else:
                        start_index = ranked[0].match_result.stop

                # case 2: two or more children 'consumed' input and same amount
                #   -> full/frag matches
                #   -> current path cannot be complete. map complete to satisfied if needed.
                else:
                    # By definition, this node can't be completed if there are multiple possible
                    # resolutions or completions of the input
                    if path.status == api.STATUS_COMPLETED:
                        path.status = api.STATUS_SATISFIED

                    # Increase the stop index and extend the current completions
                    path.match_result.stop = ranked[0].match_result.stop
                    for child in path.children:
                        path.match_result.completions.extend(child.match_result.completions)
                    break


            else:
                # case 3: no children consumed input
                # -> eval is complete as is. take completions from all
                for child in remaining_children:
                    path.match_result.completions.extend(child.match_result.completions)
                # In the case of an ordered list of children that resolve without input, the execution
                # order should match the order in which they're defined. Since the execution order is last
                # to first, these ordered children need to be reversed so that they will be executed in
                # their original order. This inconsistency is due to execution being designed for
                # command line input where last to first execution makes sense, but when a static list is
                # provided, last to first execution is not what is intended
                for child in reversed(remaining_children):
                    if path.status == api.STATUS_COMPLETED or path.status == api.STATUS_SATISFIED:
                        path.resolutions.append(child)
                break


            # if current node is completed there is nothing more to resolve, by definition
            if path.status == api.STATUS_COMPLETED:
                break


    def execute(self):
        """
        Execute the resolved nodes in reversed post-order (effectively its a stack).

        :return:
        """

        child_results = {child.cmd_node.name: child.execute() for child in reversed(self.resolutions)}

        # If this node isn't satisfied, then don't execute. Check this after recursive call
        # in order to do the check from the bottom up. Otherwise the root node would always
        # be unsatisfied   - comment out to give the cmd the chance to report it's own error and allow unsatisfied to execute as with context nodes
        # if self.status not in [STATUS_SATISFIED, STATUS_COMPLETED]:
        #     # print('input invalid. {}: {}\n{}'.format(self.cmd_node.name, self.match_result.matched_input(), self.cmd_node.usage))
        #     # return
        #     raise NodeUnsatisfiedError('input invalid for {}'.format(self.cmd_node.name))

        # print 'execute {} on {}, {}, {}'.format(path.cmd_node, path.match_result, child_results)
        anon_keys = [x for x in child_results.keys() if str(x).startswith(api.NODE_ANONYMOUS_PREFIX) and isinstance(child_results[x], dict)]


        # For any results that are returned by a container node, take the values of it's children
        # rather than itself. Otherwise the container's generated name shows up as a result, rather
        # the important values of the contained nodes.
        for k in anon_keys:
            child_results.update(child_results[k])
            del child_results[k]

        # print('executing node {} with matched input {}'.format(self.cmd_node.name, self.match_result.matched_input()))
        self.exe_result = self.cmd_node.execute(self.match_result, child_results)
        return self.exe_result




    def amount_input_consumed(self):
        return self.match_result.stop - self.match_result.start


    def get_match_score(self):
        score = self.amount_input_consumed()*10
        if self.status == api.STATUS_COMPLETED:
            score += 2
        elif self.status == api.STATUS_SATISFIED:
            score += 1
        return score


    def pprint(self, level=0):
        print("name:{}, status:{}, match:{}, resolved:{}".format(
            self.cmd_node.name,
            self.status,
            self.match_result,
            [c.cmd_node.name for c in self.resolutions]).ljust(level*3))
        for child in self.children:
            child.pprint(level+1)

    def __repr__(self):
        return "name:{}, status:{}, match:{}, resolved:{}".format(
            self.cmd_node.name,
            self.status,
            self.match_result,
            [c.cmd_node.name for c in self.resolutions])






def execute(root, input=None):
    return resolve(root, input).execute()

def resolve(root, input):
    return root.resolve(input)


