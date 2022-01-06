#!python
import os
import pprint

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from pygments.token import Token
from prompt_toolkit.keys import Keys
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.filters import Condition
from prompt_toolkit.application import in_terminal

from prompt_toolkit import print_formatted_text
from prompt_toolkit.shortcuts import message_dialog

from prompt_toolkit.key_binding.key_bindings import (
    ConditionalKeyBindings,
    KeyBindings,
    KeyBindingsBase,
    merge_key_bindings,
)

from dsh import node, api


style = Style.from_dict({
    # Token.Operator:       '#33aa33 bold',
    # Token.Number:         '#aa3333 bold',
    # 'bottom-toolbar.text': 'bg:#662222 #ffffff',
    # 'bottom-toolbar': '#000000 bg:#662222'
})


class DevShell(Completer):

    def __init__(self, root_node):
        self.root_node = root_node
        self.history = FileHistory(os.path.expanduser('~/.dsh.history'))
        self.registry = self.get_key_bindings()


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
                    -len(word_before) if a.startswith(word_before) else 0)


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


    def get_bottom_toolbar(self):

        text = '  ^P : dump context   ^F : flange info';

        # if DevShell.__filter_ipython_installed():
        #     text += '  ^I : Ipython shell'
        return text


    # @staticmethod
    # def __filter_ipython_installed(ignore=None):
    #     try:
    #         import IPython
    #         return True
    #     except:
    #         return False


    def get_key_bindings(self):

        key_bindings = KeyBindings()

        async def print_flange_info(event):
            async with in_terminal():
                self.root_node.flange.info()

        key_bindings.add("c-f")(print_flange_info)

        async def print_context(event):
            async with in_terminal():
                pprint.pprint(api.format_dict(self.root_node.context))

        key_bindings.add("c-p")(print_context)

        # async def run_ipython(event):
        #     async with in_terminal():
        #         from IPython import embed
        #         embed()
        #
        # if DevShell.__filter_ipython_installed():
        #     key_bindings.add("c-i")(run_ipython)

        return key_bindings;


    def run(self):

        # try:
        session = PromptSession(
            style=style,
            key_bindings=self.get_key_bindings(),
            completer=self,
            bottom_toolbar=self.get_bottom_toolbar(),
            history=self.history)

        while True:

            try:
                text = session.prompt(self.get_prompt())
            except KeyboardInterrupt:
                continue
            except EOFError:
                break

            try:
                node.execute(self.root_node, text)
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            except Exception as e:
                print(e)

        # Stop thread.
        # running = False

        return 0


