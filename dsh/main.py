
import os, yaml, six, copy
from dsh import shell, api, node, evaluators, matchers, executors



with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data/schema.yml')) as f:
    DSH_SCHEMA = yaml.load(f)

def dsh_schema():
    return DSH_SCHEMA


DSH_FLANGE_PLUGIN = {'dshnode': {
    'type': 'FLANGE.TYPE.PLUGIN',
    'schema': 'python://dsh/main.dsh_schema',
    'factory': 'python://dsh/main.node_dsh_context'
}}





def node_dsh_cmd(key, val, ctx={}, usage=None):
    """
    handles "#/definitions/type_command"

    :param key:
    :param val:
    :param ctx:
    :return:
    """
    # command can be specified by a simple string
    if isinstance(val, six.string_types):
        root = node.CmdNode(key, context=ctx, usage=usage, method_evaluate=evaluators.require_all_children)
        n = node.node_shell_command(key+"_cmdstr", val, ctx=ctx, return_output=False)
        n.match = matchers.match_always_consume_no_input
        root.add_child(n)
        return root

    # command can be a list of commands (nesting allowed)
    elif isinstance(val, list):
        root = node.CmdNode(key, context=ctx, usage=usage, method_evaluate=evaluators.require_all_children)
        # add child cmds
        for i, c in enumerate(val):
            cn = node_dsh_cmd(key+'_'+str(i+1), c, ctx=ctx)
            root.add_child(cn)
            # swallow completions
            cn.match = matchers.match_always_consume_no_input
            # cn.evaluate = evaluators.require_all_children

        return root

    # command can be a dict with keys {do,help,env}
    elif isinstance(val, dict):
        root = node.CmdNode(key, context=ctx, method_evaluate=evaluators.require_all_children)

        newctx = ctx.copy()
        if 'vars' in val:
            newctx.update(val['vars'])

        cn = node_dsh_cmd(
            key+'_do_dict',
            val['do'],
            ctx=newctx)
        root.add_child(cn)
        # swallow completions
        cn.match = matchers.match_always_consume_no_input
        # cn.evaluate = evaluators.require_all_children

        if 'on_failure' in val:
            cn.on_failure(node_dsh_cmd(
                key+'_on_failure',
                val['on_failure'],
                ctx=newctx))

        return root

    else:
        raise ValueError("value of command {} must be a string, list, or dict. type is {}".format(key, type(val)))



def __make_child_context(parent_ctx, data):
    newctx = copy.deepcopy(parent_ctx) if parent_ctx else {}
    if 'vars' in data:
        newctx.update(data['vars'])
    return newctx


def node_dsh_context(data, name=None, ctx={}):

    ns = data['ns'] if 'ns' in data else ''

    if name:
        # a named command is not the root
        rootCmd = node_shell(name, __make_child_context(ctx, data))
    else:
        name = ns if ns else 'dsh'
        rootCmd = node.node_root(name, __make_child_context(ctx, data))

    # maintain a tuple in the node context that keeps nested context names
    if '__DSH_CTX_PATH__' in rootCmd.context and rootCmd.context['__DSH_CTX_PATH__']:
        rootCmd.context['__DSH_CTX_PATH__'] = rootCmd.context['__DSH_CTX_PATH__'] + (name,)
    else:
        rootCmd.context['__DSH_CTX_PATH__'] = (name,)

    # Process the remaining keys
    for key, val in data.items():
        if key in ['dsh', 'vars', 'ns', 'include']:
            pass
        elif key == 'contexts':
            for k, v in val.items():
                rootCmd.add_child(node_dsh_context(v, k, ctx=rootCmd.context))
        elif key == 'commands':
            for k, v in val.items():
                rootCmd.add_child(node_dsh_cmd(k, v, __make_child_context(rootCmd.context, data)))
        else:
            rootCmd.add_child(node_dsh_cmd(key, val, __make_child_context(rootCmd.context, data)))
    return rootCmd





def node_shell(name, ctx=None):

    snode = node.CmdNode(name, context=ctx)
    snode.execute = lambda match_result, child_results: execute_context(snode, match_result, child_results)
    return snode



def execute_context(snode, match_result, child_results):

    # If no child node results are available, then this node is assumed to be
    # at the end of the input and will execute as a interactive subcontext/shell
    matched_input = match_result.matched_input()
    if len(matched_input) == 1 and matched_input[0] == snode.name and not match_result.input_remainder():
        # clone the this node as a root node and run it
        cnode = node.node_root(snode.name, snode.context)
        for child in snode.get_children():
            cnode.add_child(child)
        return shell.run(cnode)

    # If there are children that returned a result, then just pass those on.
    # In this case this node is acting as a container
    if child_results:
        return child_results



def get_executor_shell(cnode):
    return lambda ctx, matched_input, child_results: execute_context(cnode, ctx, child_results)





def get_flange_data(options=None):

    data = {}
    data.update(DSH_FLANGE_PLUGIN)
    if options:
        data.update(options)

    from flange import cfg
    f = cfg.Cfg(
        data=data,
        include_os_env=False,
        # research_models=False,
        root_ns='root',
        file_patterns=['.*cmd.yml'],
        base_dir=[ '.', '~'],
        # base_dir=['.'],
        # file_ns_from_dirname=False,
        file_search_depth=0)

    # # add each
    # if f.get('include'):
    #     includes = [os.path.realpath(os.path.expanduser(x)) for x in f.get('include')]
    # else:
    #     includes = []
    #
    # # Add any top level includes
    # for x in includes:
    #     if not os.path.exists(x):
    #         print 'Path does not exist {}'.format(x)
    #         continue
    #     elif os.path.isdir(x):
    #         print 'including directory ', x
    #         path = x
    #         basename = '.cmd.xml'
    #     else:
    #         print 'including file ', x
    #         path, basename = os.path.split(x)
    #
    #     f.add_file_set(
    #             root_ns='prj.contexts',
    #             file_patterns=[basename],
    #             base_dir=path,
    #             file_ns_from_dirname=True,
    #             file_search_depth=1)
    #
    # # Add current working dir if not already included
    # if os.getcwd() not in includes:
    #     f.add_file_set(
    #         root_ns='prj.contexts',
    #         file_patterns=['.cmd.yml'],
    #         base_dir='.',
    #         file_ns_from_dirname=True,
    #         file_search_depth=1)


    # sources = [x['src'] for x in f.sources if x['src'] not in ['python']]
    # print('loaded config from: \n\t- {}'.format('\n\t-'.join(sources)))

    # f.research_models()
    return f



import click

@click.group(invoke_without_command=True)
@click.option('--verbose/--not-verbose', default=False)
@click.pass_context
def main(ctx, verbose):

    options = {
        api.DSH_VERBOSE: verbose
    }

    FG = get_flange_data(options)

    # print FG.info()
    # import json
    # print json.dumps(FG.data, indent=4)
    # # from IPython import embed; embed()
    # print FG.info()

    # root = FG.mget(os.path.basename(os.getcwd()), model='dshnode')
    root = FG.mget('root', model='dshnode')

    # root = node.node_container('root')
    # root.one_of([node_shell('panelson',FG.mget('panelson')), node.CmdNode('cmd_two').one_of(['opt1', 'opt2'])])

    # validate possible candidates
    #
    # for nkey in FG.models.get('dshnode').keys():
    #     root.add_child(node.node_root(nkey).add_child(FG.mget([1])))

    #
    # import pprint
    # pprint.pprint(FG.data)
    if not root:
        print('No valid dsh configuration was found')
        FG.models.get('dshnode', raise_absent=True).validate(FG.get(os.path.basename(os.getcwd())))
        return 1

    shell.run(root)



if __name__ == '__main__':
    main()
