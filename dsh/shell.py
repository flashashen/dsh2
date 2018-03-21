#!python


from __future__ import unicode_literals
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token
from prompt_toolkit.key_binding.defaults import load_key_bindings_for_prompt
from prompt_toolkit.keys import Keys
from prompt_toolkit.contrib.regular_languages.compiler import compile
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.filters import Condition
import shlex, threading, time

from . import node, api


# def create_grammar():
#     return compile("""
#         (\s*  (?P<operator1>[a-z]+)   \s+   (?P<var1>[0-9.]+)   \s+   (?P<var2>[0-9.]+)   \s*) |
#         (\s*  (?P<operator2>[a-z]+)   \s+   (?P<var1>[0-9.]+)   \s*)
#     """)


style = style_from_dict({
    Token.Operator:       '#33aa33 bold',
    Token.Number:         '#aa3333 bold',
    Token.TrailingInput: 'bg:#662222 #ffffff',
    Token.Toolbar: '#ffffff bg:#aaaaaa',
})


counter = 0

class ProtoCompleter(Completer):

    def __init__(self, proto):
        self.root_proto = proto

    def get_completions(self, document, complete_event):
        global counter
        counter += 1
        # print('**********************  get completions {} **********************'.format(counter))

        path = self.root_proto.complete(document.text_before_cursor)
        # resolver.resolve(path, shlex.split(document.text_before_cursor), 0)
        c = path.match_result.completions

        # print('\ncompletions: ', c)
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
                    # display='alt display for {}'.format(a),
                    # display_meta='meta info',
                    get_display_meta=None)



def prompt_from_cmdnode(n):
    if not '__DSH_CTX_PATH__' in n.context:
        return n.name + '$ '

    prompt = ".".join(n.context['__DSH_CTX_PATH__'])
    return prompt + '$ '


FLANGE_CFG_SAVE = None


def run(cmdnode, fcfg=None):

    global FLANGE_CFG_SAVE
    history = InMemoryHistory()

    if fcfg and not FLANGE_CFG_SAVE:
        FLANGE_CFG_SAVE = fcfg


    def get_bottom_toolbar_tokens(cli):

        tokens = [
            (Token.Toolbar, '^H ^D : dump context')]
        if __filter_ipython_installed() :
            tokens.append((Token.Toolbar, '^H ^P : Ipython shell'))
        return tokens

    # We start with a `Registry` of default key bindings.
    registry = load_key_bindings_for_prompt()

    @registry.add_binding(Keys.ControlH, Keys.ControlD)
    def _dump(event):
        """
        Print 'hello world' in the terminal when ControlT is pressed.
        We use ``run_in_terminal``, because that ensures that the prompt is
        hidden right before ``print_hello`` gets executed and it's drawn again
        after it. (Otherwise this would destroy the output.)
        """
        def dump_context():
            import pprint
            pprint.pprint(api.__format_dict(cmdnode.context))
        event.cli.run_in_terminal(dump_context)


    def __filter_ipython_installed(ignore=None):
        try:
            import IPython
            return True
        except:
            return False

    @registry.add_binding(Keys.ControlH, Keys.ControlP, filter=Condition(__filter_ipython_installed))
    def _ipy(event):
        """
        Print 'hello world' in the terminal when ControlT is pressed.
        We use ``run_in_terminal``, because that ensures that the prompt is
        hidden right before ``print_hello`` gets executed and it's drawn again
        after it. (Otherwise this would destroy the output.)
        """
        def runipy():

            # Now we start ipython with our configuration
            import IPython
            IPython.embed(
                header="Added to IPython namespace: dsh node: '{}', flange cfg: '{}'".format(cmdnode.name, 'fcfg'),
                user_ns={cmdnode.name: cmdnode, 'fcfg': fcfg if fcfg else FLANGE_CFG_SAVE})

        event.cli.run_in_terminal(lambda: runipy())




    # Print a counter every second in another thread.
    running = True
    # def thread():
    #     i=0
    #     while running:
    #         i += 1
    #         print('i=%i' % i)
    #         time.sleep(1)
    # t = threading.Thread(target=thread)
    # t.daemon = True

    completer = ProtoCompleter(cmdnode)

    try:
        while True:

            try:
                import sys
                text = prompt(
                    prompt_from_cmdnode(cmdnode),
                    # lexer=lexer,
                    completer=completer,
                    get_bottom_toolbar_tokens=get_bottom_toolbar_tokens,
                    style=style,
                    key_bindings_registry=registry,
                    patch_stdout=False,
                    get_title=None, # get_title,
                    history=history)
            except KeyboardInterrupt as e:
                import sys
                sys.stdout.flush()
            except EOFError as e:
                raise

            try:
                node.execute(cmdnode, text)
            except KeyboardInterrupt:
                # dump anything to stdout to prevent last command being re-executed
                print(' ** interrupted **')
            except Exception as e:
                print(e)

    except EOFError as e:
        pass

    # Stop thread.
    # running = False

    return 0


