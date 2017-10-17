import random, string, six, os
from api import *
import matchers
import executors
import evaluators
import yaml


def node_root():
    # normal root node will be just a container where one command is selected and the
    # result should be the result of that single selected child
    return CmdNode(
        'root',
        method_match=matchers.match_always_consume_no_input,
        method_evaluate=evaluators.choose_one_child,
        method_execute=executors.get_executor_return_child_result_value())


def node_option(name):
    return CmdNode(
        name,
        initial_status=STATUS_SATISFIED,
        method_match=matchers.get_matcher_exact_string(name),
        method_evaluate=evaluators.no_children,
        method_execute=executors.get_executor_return_matched_input)


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


def node_container(name=None, method_evaluate=None, usage=None):
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
        method_match=matchers.match_always_consume_no_input,
        method_evaluate=method_evaluate if method_evaluate else evaluators.require_all_children,
        method_execute=executors.get_executor_return_child_results())


def node_python(name, method, args_required=None, args_optional=None, options=None):
    # Return a node that executes a python method. By default, children are all required, which
    # is with the expectation that containers like allOf and oneOf will be used to group arguments.
    m = CmdNode(
        name,
        method_match=matchers.get_matcher_exact_string(name),
        method_evaluate=evaluators.require_all_children,
        method_execute=executors.get_executor_python(method))


    if options:
        m.options(options)

    if args_required:
        m.all_of(args_required)

    if args_optional:
        c = node_container(method_evaluate=evaluators.children_as_options)
        for arg in args_optional:
            c.add_child(arg if isinstance(arg, CmdNode) else node_argument(arg))


    return m


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



#
# def one_of(choices, usage=None):
#     node = node_container().add(choices)
#     node.method_evaluate = evaluators.choose_one_child
#     node.usage = usage if usage else 'choose one of: {}'.format([c.name for c in node.get_children()])
#     return node
#
#
# def all_of(choices, usage=None):
#     node = node_container().add(choices)
#     node.method_evaluate = evaluators.require_all_children
#     node.usage = usage if usage else 'must provide all of: {}'.format([c.name for c in node.get_children()])
#     return node
#
#
# def options(choices, usage=None):
#     node = node_container().add(choices)
#     node.method_evaluate = evaluators.children_as_options
#     node.usage = usage if usage else 'options: {}'.format([c.name for c in node.get_children()])
#     return node
#

#
# def options(name, options):
#     node = CmdNode('--'+name, method_evaluate=evaluators.children_as_options)
#     node.add(options)
#     return node




def get_nodes_from_choices(nodes):
    children = []

    if isinstance(nodes, six.string_types):
        nodes = nodes.split()
    for node in nodes:
        children.append(node if isinstance(node, CmdNode) else node_string(node))
    return children




class CmdNode(object):

    def __init__(self,
                 name=None,
                 usage=None,
                 method_execute=None,
                 method_match=None,
                 method_evaluate=None,
                 child_get_func=None,
                 context=None,
                 initial_status=STATUS_UNSATISFIED):

        self.name = name if name else NODE_ANONYMOUS_PREFIX + ''.join([random.choice(string.ascii_letters+string.digits) for n in range(8)])
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
            self.get_children = lambda ctx: children




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
            if not isinstance(opt, basestring):
                raise ValueError('options must be strings. got {}'.format(type(opt)))
            self.add_child(node_option(opt))
        return self




def get_children_method_dir_listing():
    import glob
    return lambda ctx: [CmdNode(p) for p in glob.glob('*')]


#
#
#   Flange setup
#
#



def create_cmd_node(key, val, ctx={}, usage=None):
    """
    handles "#/definitions/type_command"

    :param key:
    :param val:
    :param ctx:
    :return:
    """
    # command can be specified by a simple string
    if isinstance(val, six.string_types):
        return CmdNode(key, context=ctx, usage=usage, method_execute=executors.get_executor_shell(val))

    # command can be a list of commands (nesting allowed)
    elif isinstance(val, list):
        root = CmdNode(key, context=ctx, usage=usage)
        for i, c in enumerate(val):
            root.add_child(create_cmd_node(key+'_'+str(i+1), c))
        return root

    # command can be an dict with keys {do,help,env}
    elif isinstance(val, dict):
        root = CmdNode(key, context=ctx)
        if 'vars' in val:
            ctx
        root.add_child(create_cmd_node(
            key+'_do',
            val['do'],
            ctx=val['vars'] if 'vars' in val else {}))

        return root

    else:
        raise ValueError("value of command {} must be a string, list, or dict. type is {}".format(key, type(val)))



def get_node(data, name='root'):
    rootCmd = CmdNode(name)
    for key, val in data.iteritems():
        ctx = {}
        if key == 'dsh':
            pass
        elif key == 'ns':
            print('ns', val)
        elif key == 'vars':
            ctx = val
            print('vars', val)
        elif key == 'contexts':
            for k, v in val.items():
                rootCmd.add_child(get_node(v, k))
        elif key == 'commands':
            for k, v in val.items():
                rootCmd.add_child(create_cmd_node(k, v, ctx))
        else:
            rootCmd.add_child(create_cmd_node(key, val, ctx))
    return rootCmd





with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'schema.yml')) as f:
    DSH_SCHEMA = yaml.load(f)

MODULE_NAME = __name__.replace('.', '/')


def dsh_schema():
    return DSH_SCHEMA


DSH_FLANGE_PLUGIN = {'dshnode': {
    'type': 'FLANGE.TYPE.PLUGIN',
    'schema': 'python://{}.dsh_schema'.format(MODULE_NAME),
    'factory': 'python://{}.get_node'.format(MODULE_NAME)
}}