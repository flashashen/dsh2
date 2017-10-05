#!python


from __future__ import unicode_literals
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token
from prompt_toolkit.shortcuts import confirm
from prompt_toolkit.key_binding.defaults import load_key_bindings_for_prompt
from prompt_toolkit.keys import Keys
from prompt_toolkit.contrib.regular_languages.compiler import compile
from prompt_toolkit.contrib.regular_languages.completion import GrammarCompleter
from prompt_toolkit.contrib.regular_languages.lexer import GrammarLexer
from prompt_toolkit.layout.lexers import SimpleLexer

# from pygments.style import Style
# from pygments.token import Token
# from pygments.styles.default import DefaultStyle

from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.completion import Completer, Completion

import threading, time, shlex

# import ans
from node import *
from resolver import *
from evaluators import *

def create_grammar():
    return compile("""
        (\s*  (?P<operator1>[a-z]+)   \s+   (?P<var1>[0-9.]+)   \s+   (?P<var2>[0-9.]+)   \s*) |
        (\s*  (?P<operator2>[a-z]+)   \s+   (?P<var1>[0-9.]+)   \s*)
    """)


style = style_from_dict({
    Token.Operator:       '#33aa33 bold',
    Token.Number:         '#aa3333 bold',
    Token.TrailingInput: 'bg:#662222 #ffffff',
    Token.Toolbar: '#ffffff bg:#aaaaaa',
})



class ProtoCompleter(Completer):

    def __init__(self, proto):
        self.root_proto = proto

    def get_completions(self, document, complete_event):

        path = ResolutionPath(self.root_proto)
        resolve(path, shlex.split(document.text_before_cursor), 0)
        c = path.match_result.completions

        # print '\ncompletions: ', c
        # print "text before cursor: '", document.text_before_cursor, "'"
        # print "text after cursor: '", document.text_after_cursor, "'"
        # print "char before cursor: ", document.char_before_cursor
        # print 'word before cursor WORD=True: ', document.get_word_before_cursor(WORD=True)
        # print 'word before cursor WORD=False: ', document.get_word_before_cursor(WORD=False)
        word_before = document.get_word_before_cursor()
        for a in c:
            if a.startswith(word_before) or document.char_before_cursor == ' ':
                yield Completion(
                    a,
                    -len(word_before) if a.startswith(word_before) else 0, # prevent replacement of prior, complete word
                    # display='alt display for {}'.format(a.name),
                    display_meta=None,
                    get_display_meta=None)



def main():
    history = InMemoryHistory()

    def get_bottom_toolbar_tokens(cli):
        return [(Token.Toolbar, '^H ^W : Hello World')]

    # We start with a `Registry` of default key bindings.
    registry = load_key_bindings_for_prompt()

    @registry.add_binding(Keys.ControlH, Keys.ControlW)
    def _(event):
        """
        Print 'hello world' in the terminal when ControlT is pressed.
        We use ``run_in_terminal``, because that ensures that the prompt is
        hidden right before ``print_hello`` gets executed and it's drawn again
        after it. (Otherwise this would destroy the output.)
        """
        def print_hello():
            print('hello world')
        event.cli.run_in_terminal(print_hello)


    # Print a counter every second in another thread.
    running = True
    def thread():
        i=0
        while running:
            i += 1
            print('i=%i' % i)
            time.sleep(1)
    t = threading.Thread(target=thread)
    t.daemon = True
    # t.start()

    def get_title():
        return 'This is the title'


    def test_cmd(self, ctx):
        print('executing test cmd. play={}, list={}'.format(ctx['play'],ctx['list']))

    node1 = CmdNode('filecmd', method_execute=test_cmd, method_evaluate=require_all_children)
    # node.add_children([choose_value_for('play', 'website.yml', 'appserver.yml'),
    #                    all_of('list', 'groups', 'hosts', 'playbooks') ])
    node1.add_child(CmdNode('filecmd', child_get_func=get_children_method_dir_listing()))


    from ans import CmdAns
    node = CmdNode('root', method_match=match_always_consume_no_input)
    node.add_children([CmdAns(), node1])

    # import flange
    # f = flange.Flange(data = DSH_FLANGE_PLUGIN, root_ns='prj', file_patterns=['.cmd.yml'], base_dir='~/workspace', file_search_depth=2)
    # root = CmdNode('flange')
    # # choose one
    # root.add_child(CmdNode('test', get_executor_python(f.get)))
    # fget = CmdNode('get', get_executor_python(f.get))
    # # required params
    # fget = CmdNode('key')
    # # independent optional node.
    # fget = CmdNode('model', children_as_options.function_evaluate_child_statuses)








    # Cmd('ans').option('verbose').option('user').choose('a','b','c').all('d','e')


    # import test_proto
    # p1 = test_proto.get_proto()
    # p1 = Proto('root')
    # p1 = Proto('root')
    # p1.add_child(Proto('app1'))
    # p1.add_child(Proto('app2'))
    # p1.children[0].add_child(Proto('app1_1', True))
    # p1.children[0].add_child(Proto('app1_2', True))
    # p1.children[0].add_tag('testtag')
    # p1.add_rule_one_of('testtag')


    text = ''
    try:
        while True:
            try:
                text = prompt('> ',
                # lexer=lexer,
                completer=ProtoCompleter(node),
                get_bottom_toolbar_tokens=get_bottom_toolbar_tokens,
                style=style,
                key_bindings_registry=registry,
                patch_stdout=True,
                get_title=None, # get_title,
                history=history)

                #answer = confirm('Should we do that? (y/n) ')
                #if answer:

                path = ResolutionPath(node)
                resolve(path, shlex.split(text), 0)
                execute(path, {})
            except KeyboardInterrupt as e:
                pass
    except EOFError as e:
        pass


    # Stop thread.
    running = False


if __name__ == '__main__':
    main()

