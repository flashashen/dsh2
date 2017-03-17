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

from pygments.style import Style
from pygments.token import Token
from pygments.styles.default import DefaultStyle

from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.completion import Completer, Completion

import threading
import time

from proto import Proto


sql_completer = WordCompleter(['create', 'select', 'insert', 'drop',
                               'delete', 'from', 'where', 'table'], ignore_case=True)


operators1 = ['add', 'sub', 'div', 'mul']
operators2 = ['sqrt', 'log', 'sin', 'ln']


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
        self.proto = proto

    def get_completions(self, document, complete_event):

        c = self.proto.complete(document.text_before_cursor)
        # print '\ncompletions: ', c
        # print "text before cursor: '", document.text_before_cursor, "'"
        # print "char before cursor: ", document.char_before_cursor
        # print 'word before cursor WORD=True: ', document.get_word_before_cursor(WORD=True)
        # print 'word before cursor WORD=False: ', document.get_word_before_cursor(WORD=False)
        word_before = document.get_word_before_cursor()
        for a in c:
            if a.name.startswith(word_before) or document.char_before_cursor == ' ':
                yield Completion(
                    a.name,
                    -len(word_before) if a.name.startswith(word_before) else 0, # prevent replacement of prior, complete word
                    display='alt display for {}'.format(a.name),
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


    g = create_grammar()

    lexer = GrammarLexer(g, lexers={
        'operator1': SimpleLexer(Token.Operator),
        'operator2': SimpleLexer(Token.Operator),
        'var1': SimpleLexer(Token.Number),
        'var2': SimpleLexer(Token.Number),
    })

    completer = GrammarCompleter(g, {
        'operator1': WordCompleter(operators1),
        'operator2': WordCompleter(operators2),
    })


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

    p1 = Proto('root')
    p1 = Proto('root')
    p1.add_child(Proto('app1'))
    p1.add_child(Proto('app2'))
    p1.children[0].add_child(Proto('app1_1', True))
    p1.children[0].add_child(Proto('app1_2', True))
    p1.children[0].add_tag('testtag')
    p1.add_rule_one_of('testtag')


    text = ''
    while True:
        text = prompt('> ', 
		lexer=lexer, 
		completer=ProtoCompleter(p1),
		get_bottom_toolbar_tokens=get_bottom_toolbar_tokens,
		style=style,
		key_bindings_registry=registry,
		patch_stdout=True,
		get_title=None, # get_title,
		history=history)
	
	#answer = confirm('Should we do that? (y/n) ')
        #if answer:

        p1.do(text.split())

    # Stop thread.
    running = False


if __name__ == '__main__':
    main()

