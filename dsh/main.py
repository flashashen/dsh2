
import os, yaml, six, copy
from dsh import shell, node, evaluators, matchers
from flange import cfg



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

        try:
            cn = node_dsh_cmd(
                key+'_do_dict',
                val['do'],
                ctx=newctx)

            root.add_child(cn)
            # swallow completions
            cn.match = matchers.match_always_consume_no_input
        # cn.evaluate = evaluators.require_all_children
        except Exception as e:
            # replace the root node with an error message echo
            root = node.node_display_message(key, str(e))

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
        # print 'dsh ctx contructr ', key, val
        if key in ['dsh', 'vars', 'ns', 'include']:
            pass
        elif key == 'contexts':
            for k, v in val.items():
                rootCmd.add_child(node_dsh_context(v, k, ctx=rootCmd.context))
        elif key == 'commands':
            for k, v in val.items():
                rootCmd.add_child(node_dsh_cmd(k, v, __make_child_context(rootCmd.context, data)))
        else:
            # print 'visiting ', key, ' as a ctx rather than cmd'
            # if isinstance(val, dict) and not 'do' in val:
            #     print 'attempting ', key, ' as a ctx rather than cmd'
            #     # This is not a valid command node. its mostly likely a context. try it that way
            #     rootCmd.add_child(node_dsh_context(val, key, ctx=rootCmd.context))
            # else:
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




def get_flange_cfg(
        options=None,
        root_ns='dsh2',
        base_dir=['.', '~'],
        file_patterns=['.cmd.yml'],
        file_search_depth=2,
        file_ns_from_dirname=False):

    data = {}
    data.update(DSH_FLANGE_PLUGIN)
    if options:
        data.update(options)

    # get flange config. dont pass root_ns so that config that does not
    # contain the 'dsh' element will not fall under dsh root node. If it
    # did then there will more likely be invalid config
    f = cfg.Cfg(
        data=data,
        include_os_env=False,
        file_patterns=file_patterns,
        file_exclude_patterns=[],
        file_ns_from_dirname=file_ns_from_dirname,
        base_dir=base_dir,
        file_search_depth=file_search_depth,
        merge=False,
        research=False,
        key_filter=None)

    ns_separator = f.unflatten_separator + 'contexts' + f.unflatten_separator
    # massage source namespaces so the merged config lines up right in dsh
    # '' -> root
    # root -> root
    # prj -> root__contexts__prj
    # root.prj --> root__contexts__prj
    for s in f.sources:
        if s.contents and 'ns' in s.contents and 'dsh' in s.contents:
            if not s.contents['ns'] or s.contents['ns'] == root_ns:
                newns = root_ns
            elif s.contents['ns'].startswith(root_ns):
                newns = s.contents['ns'].replace('.', ns_separator)
            else:
                newns = root_ns + ns_separator + s.contents['ns'].replace('.', ns_separator)
            # print 'setting {} ns from {} to {}'.format(s.uri, s.ns, newns)
            s.ns = newns

    # f.merge_sources()
    # print 'a', sorted([s.ns for s in f.sources])
    # f.sources[0].ns = 'something  new...'
    f.refresh(gather=False, merge=True, research=True)
    # f.sources[0].ns = 'something completely new...'
    # print 'b', sorted([s.ns for s in f.sources])

    return f


def run_from_flange(f, root_ns='dsh2'):
    root = f.mget(root_ns, model='dshnode')

    if not root:
        print('No valid dsh configuration was found')
        f.models.get('dshnode', raise_absent=True).validate(f.get(os.path.basename(os.getcwd())))
        return 1

    shell.run(root, f)

#
# import click
#
# @click.group(invoke_without_command=True)
# @click.option('--verbose/--not-verbose', default=False)
# @click.pass_context
# def main(ctx, verbose):
def run(options=None,
        base_dir=['.', '~'],
        file_patterns=['.cmd.yml'],
        file_search_depth=0):

    options = {
        # api.DSH_VERBOSE: verbose
    }

    f = get_flange_cfg(
        options=options,
        base_dir=base_dir,
        file_patterns=file_patterns,
        file_search_depth=file_search_depth)

    run_from_flange(f)

    # print FG.info()
    # import json
    # print json.dumps(FG.data, indent=4)
    # # from IPython import embed; embed()
    # print FG.info()


    # root = FG.mget(os.path.basename(os.getcwd()), model='dshnode')

    # root = node.node_container('root')
    # root.one_of([node_shell('panelson',FG.mget('panelson')), node.CmdNode('cmd_two').one_of(['opt1', 'opt2'])])

    # validate possible candidates
    #
    # for nkey in FG.models.get('dshnode').keys():
    #     root.add_child(node.node_root(nkey).add_child(FG.mget([1])))

    #
    # import pprint
    # pprint.pprint(FG.data)


def main():
    run()

if __name__ == '__main__':
    run()
