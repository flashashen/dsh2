#!python
from __future__ import unicode_literals
import os
import sys

from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token
# from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.key_binding.defaults import load_key_bindings_for_prompt
from prompt_toolkit.keys import Keys
# from prompt_toolkit.contrib.regular_languages.compiler import compile
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.filters import Condition
# import shlex, threading, time

from dsh import node, api


# def create_grammar():
#     return compile("""
#         (\s*  (?P<operator1>[a-z]+)   \s+   (?P<var1>[0-9.]+)   \s+   (?P<var2>[0-9.]+)   \s*) |
#         (\s*  (?P<operator2>[a-z]+)   \s+   (?P<var1>[0-9.]+)   \s*)
#     """)


style = style_from_dict({
    Token.Operator:       '#33aa33 bold',
    Token.Number:         '#aa3333 bold',
    Token.TrailingInput: 'bg:#662222 #ffffff',
    Token.Toolbar: '#000000 bg:#aaaaaa',
})




class DevShell(Completer):

    def __init__(self, root_node):
        self.root_node = root_node
        self.history = FileHistory(os.path.expanduser('~/.dsh.history'))
        self.registry = self.get_key_registry()




    def get_completions(self, document, complete_event):
        """
        This method returns completions as expected by prompt_toolkit (overrides method of Completer)
        :param document:
        :param complete_event:
        :return:
        """

        path = self.root_node.complete(document.text_before_cursor)
        # resolver.resolve(path, shlex.split(document.text_before_cursor), 0)
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


    def get_title(self):
        return None

    def get_prompt(self):
        if not api.CTX_VAR_PATH in self.root_node.context:
            return self.root_node.name + '$ '

        prompt = ".".join(self.root_node.context[api.CTX_VAR_PATH])
        return prompt + '$ '

    def get_root(self):

        roots = self.fcfg.objs(self.root_ns, model='dshnode')

        if not roots:
            print('No valid dsh configuration was found')
            self.fcfg.models['dshnode'].validator(self.root_ns)
            return 1

        return roots[0]


    def get_bottom_toolbar_tokens(self, cli):
        tokens = [
            (Token.Toolbar, '^H^D : dump context'),
            (Token.Toolbar, '  ^H^F : flange info')]
        if DevShell.__filter_ipython_installed():
            tokens.append((Token.Toolbar, '  ^H^P : Ipython shell'))
        return tokens


    @staticmethod
    def __filter_ipython_installed(ignore=None):
        try:
            import IPython
            return True
        except:
            return False

    def get_key_registry(self):

        registry = load_key_bindings_for_prompt()

        @registry.add_binding(Keys.ControlH, Keys.ControlF)
        def _flange_info(event):
            event.cli.run_in_terminal(self.root_node.info)

        @registry.add_binding(Keys.ControlH, Keys.ControlD)
        def _dump_ctx(event):
            def dump_context():
                import pprint
                pprint.pprint(api.format_dict(self.root_node.context))
            event.cli.run_in_terminal(dump_context)

        @registry.add_binding(Keys.ControlH, Keys.ControlR)
        def _reload(event):
            def reload():
                print('refreshing flange data..')
                self.root_node.flange.refresh()
                print(self.root_node.context[api.CTX_VAR_PATH])
            event.cli.run_in_terminal(reload)

        @registry.add_binding(Keys.ControlH, Keys.ControlP, filter=Condition(DevShell.__filter_ipython_installed))
        def _ipy(event):
            """
            run embedded ipython shell
            """
            def runipy():

                # Now we start ipython with our configuration
                import IPython
                try:
                    from traitlets.config.loader import Config
                except ImportError:
                    from IPython.config.loader import Config
                cfg = Config()
                cfg.TerminalInteractiveShell.confirm_exit = False
                IPython.embed(
                    config=cfg,
                    header="Added to IPython namespace:\n\n\tshell instance: shell\n\tdsh node: shell.root_node\n\tflange instance: shell.root_node.flange",
                    user_ns={
                        # self.root_node.name: self.root_node,
                        # 'fcfg': self.root_node.flange,
                        'shell': self})

            event.cli.run_in_terminal(lambda: runipy())

        return registry


    def prompt(self):
        return prompt(
            self.get_prompt(),
            # lexer=lexer,
            completer=self,
            get_bottom_toolbar_tokens=self.get_bottom_toolbar_tokens,
            style=style,
            key_bindings_registry=self.registry,
            patch_stdout=False,
            get_title=self.get_title(),
            history=self.history)



    def run(self):

        try:
            while True:

                try:
                    text = self.prompt()
                except KeyboardInterrupt as e:
                    import sys
                    sys.stdout.flush()
                except EOFError as e:
                    raise

                try:
                    node.execute(self.root_node, text)
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


