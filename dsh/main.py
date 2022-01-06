
import os, yaml, copy
from dsh import api, shell, node, evaluators, matchers
from flange import cfg



with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data/schema.yml')) as f:
    DSH_SCHEMA = yaml.safe_load(f)

def dsh_schema():
    return DSH_SCHEMA


DSH_FLANGE_PLUGIN = {'dshnode': {
    'name': 'dshnode',
    'type': 'FLANGE.TYPE.PLUGIN',
    'schema': 'python://dsh/main.dsh_schema',
    'factory': 'python://dsh/main.node_factory_context',
    'inject': 'flange'
}}

DSH_MARKER_ELEMENT = 'dsh'
DSH_DEFAULT_ROOT = 'root'
NS_SEPARATOR = cfg.DEFAULT_UNFLATTEN_SEPARATOR + 'contexts' + cfg.DEFAULT_UNFLATTEN_SEPARATOR



def node_factory_context(data, name=None, ctx={}):

    if name:
         # a named context is not the root
        rootCmd = node_factory_shell(name, __make_child_context(ctx, data))
    else:
        name = data[DSH_MARKER_ELEMENT] if data.get(DSH_MARKER_ELEMENT ) else DSH_DEFAULT_ROOT
        rootCmd = node.node_root(name, __make_child_context(ctx, data))


    # maintain a tuple in the node context that keeps nested context names
    if rootCmd.context and rootCmd.context.get(api.CTX_VAR_PATH):
        rootCmd.context[api.CTX_VAR_PATH] = rootCmd.context[api.CTX_VAR_PATH] + (name,)
    else:
        rootCmd.context[api.CTX_VAR_PATH] = (name,)

    # Process the remaining keys
    for key, val in data.items():
        # print 'dsh ctx contructr ', key, val
        if key in ['dsh', 'vars', 'include']:
            pass
        elif key == 'contexts':
            for k, v in val.items():
                rootCmd.add_child(node_factory_context(v, k, ctx=rootCmd.context))
        elif key == 'commands':
            for k, v in val.items():
                rootCmd.add_child(node_factory_command(k, v, __make_child_context(rootCmd.context, data)))
        else:
            # print 'visiting ', key, ' as a ctx rather than cmd'
            # if isinstance(val, dict) and not 'do' in val:
            #     print 'attempting ', key, ' as a ctx rather than cmd'
            #     # This is not a valid command node. its mostly likely a context. try it that way
            #     rootCmd.add_child(node_factory_context(val, key, ctx=rootCmd.context))
            # else:
            rootCmd.add_child(node_factory_command(key, val, __make_child_context(rootCmd.context, data)))
    return rootCmd


def node_factory_command(key, val, ctx={}, usage=None):
    """
    handles "#/definitions/type_command"

    :param key:
    :param val:
    :param ctx:
    :return:
    """
    # command can be specified by a simple string
    if isinstance(val, str):
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
            cn = node_factory_command(key+'_'+str(i+1), c, ctx=ctx)
            root.add_child(cn)
            # swallow completions
            cn.match = matchers.match_always_consume_no_input

        return root

    # command can be a dict with keys {do,help,env}
    elif isinstance(val, dict):
        root = node.CmdNode(key, context=ctx, method_evaluate=evaluators.require_all_children)

        newctx = ctx.copy()
        if 'vars' in val:
            newctx.update(val['vars'])

        try:
            cn = node_factory_command(
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
            print('adding failure node exe wrapper. cmd = {}'.format(val['on_failure']))
            root.on_failure(node_factory_command(
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



def node_factory_shell(name, ctx=None):

    def run_as_shell(snode, match_result, child_results):
        # If no child node results are available, then this node is assumed to be
        # at the end of the input and will execute as a interactive subcontext/shell
        matched_input = match_result.matched_input()
        if len(matched_input) == 1 and matched_input[0] == snode.name and not match_result.input_remainder():
            # clone this node as a root node and run it
            cnode = node.node_root(snode.name, snode.context)
            for child in snode.get_children():
                cnode.add_child(child)
                cnode.flange = snode.flange
            return shell.DevShell(cnode).run()

        # If there are children that returned a result, then just pass those on.
        # In this case this node is acting as a container
        if child_results:
            return child_results

    snode = node.CmdNode(name, context=ctx)
    snode.execute = lambda match_result, child_results: run_as_shell(snode, match_result, child_results)
    return snode

#
# def get_executor_shell(cnode):
#     return lambda ctx, matched_input, child_results: execute_context(cnode, ctx, child_results)
#
#


def get_flange_cfg(
        options=None,
        root_ns='dsh',
        base_dir=['.', '~'],
        file_patterns=['.cmd*.yml'],
        file_exclude_patterns=['.history'],
        file_search_depth=2,
        initial_data={}):

    # The initial data force 
    # data = {} #{root_ns: {'dsh': root_ns}}
    initial_data.update(DSH_FLANGE_PLUGIN)
    initial_data.update({root_ns: {DSH_MARKER_ELEMENT: root_ns}})
    if options:
        initial_data.update(options)


    def update_source_root_path(dsh_root, src):
        '''
        Define a flange source post-processor to set the root path for the source.
        The root path is determined from the value of the DSH_MARKER_ELEMENT

        :param dsh_root: 'location' of dsh config in the flange data
        :param src: flange source object
        :return: None
        '''

        if not src.contents or not isinstance(src.contents, dict) or DSH_MARKER_ELEMENT not in src.contents:
            return

        ns = src.contents.get(DSH_MARKER_ELEMENT)
        if not ns:
            src.root_path = DSH_DEFAULT_ROOT

        elif ns.startswith(dsh_root):
            # if the dsh ns starts with the current root, then assume
            # they're referring to the same ns. Just replace separator
            src.root_path = ns.replace('.', NS_SEPARATOR)

        else:
            # just append the dsh ns
            src.root_path = dsh_root + NS_SEPARATOR + ns.replace('.', NS_SEPARATOR)
        # print 'setting {} ns from {} to {}'.format(src.uri, curent_root, src.ns)

        # Add the src location to the vars so context nodes can change cwd
        src.contents['vars' + cfg.DEFAULT_UNFLATTEN_SEPARATOR + api.CTX_VAR_SRC_DIR] = os.path.dirname(src.uri)


    # get flange config. dont pass root_ns so that config that does not
    # contain the 'dsh' element will not fall under dsh root node. If it
    # did then there will more likely be invalid config
    fcfg = cfg.Cfg(
        data=initial_data,
        root_path=None,
        include_os_env=False,
        file_patterns=file_patterns,
        file_exclude_patterns=file_exclude_patterns,
        base_dir=base_dir,
        file_search_depth=file_search_depth,
        src_post_proc=lambda src: update_source_root_path(root_ns, src))

    return fcfg



def set_flange(n, f):
    n.flange = f
    children = n.get_children()
    for i in range(len(children)):
        # print 'setting flange to ', hex(id(child))
        set_flange(children[i], f)



import click

@click.group(invoke_without_command=True)
@click.option('--base_dir', '-b', multiple=True, default=['~', '.'], 
    help='Base directory to begin search. Mulitple accepted')
@click.option('--file_pattern', '-fp', multiple=True, default=['.dsh*.yml'],
    help='File glob pattern for matching source files. Mulitple accepted')
@click.option('--search_depth', '-sd', default=2,
    help='Depth of directory search starting with base')
@click.option('--ignore_errors', '-ie', is_flag=True, default=False,
    help='Ignore failures to parse matched files. By default, any failure to parse will terminate the shell')
@click.option('--exist_on_init', '-ei', is_flag=True, default=False)
# @click.pass_context
def cli(base_dir,
        file_pattern,
        search_depth,
        ignore_errors,
        exist_on_init):

    options = {
        # api.DSH_VERBOSE: verbose
    }

    if isinstance(base_dir, str):
        base_dir = [base_dir]

    root_ns = DSH_DEFAULT_ROOT

    f = get_flange_cfg(
        root_ns=root_ns,
        options=options,
        base_dir=base_dir,
        file_patterns=file_pattern,
        file_search_depth=search_depth)


    roots = f.objs(root_ns, model='dshnode')
    # from IPython import embed; embed()
    if not [src for src in f.sources if src.parser] :
        print(f'No sources found matching {file_pattern}')
        return 1
       
    # Dump src info and set namespaces from data
    print(f"\n{'sources':<60} ns:")
    for src in [f for f in f.sources if f.uri != 'init_data' and not f.error]:
        ns = str(src.root_path).replace(NS_SEPARATOR, '.') if src.root_path else ''
        print(f"{src.uri:60.65} {ns:20}")

    error_sources = [src for src in f.sources if src.error]
    if error_sources:
        print('\nfailed to parse:')
        for src in error_sources:
            # ns = str(src.root_path).replace(NS_SEPARATOR, '.') if src.root_path else ''
            print(f"{src.uri:<60} {src.error}")

    if [src for src in f.sources if src.error] and not ignore_errors:
        print('\nExiting due to parse errors. Set --ignore_errors=true to ignore.\n')
        return 1

    # if roots and :
    #     print(f'No sources found matching {file_pattern}')
    #     return 1

    if not roots:
        # from IPython import embed; embed()
        print('No valid dsh configuration was found')
        try:
            f.models['dshnode'].validator(f.value(root_ns))
        except Exception as e:
            print(e)
        return 1

    set_flange(roots[0], f)

    dsh = shell.DevShell(roots[0])
    if exist_on_init:
        return 0
        
    dsh.run()



if __name__ == '__main__':
    cli()
