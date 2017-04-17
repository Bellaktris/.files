import os

from IPython.terminal.prompts import Prompts, Token
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.key_binding.vi_state import InputMode as ViInputMode

cfg = get_config()
cfg.TerminalInteractiveShell.editing_mode = 'vi'
cfg.TerminalInteractiveShell.true_color = True
cfg.TerminalIPythonApp.display_banner = False

cfg.InteractiveShellApp.exec_lines = \
  ['import math', 'import scipy',
   'import numpy as np',
   'import itertools',
   'import matplotlib.pyplot as plt']

cfg.HistoryManager.hist_file = os.path.expanduser('~/.ptpython/history.sqlite')

HOMEDIR = os.path.expanduser('~')

class CwdPrompt(Prompts):
  prompt_mode = 0

  def in_prompt_tokens(self, cli=None):
    dirs = os.getcwd().replace(HOMEDIR, "~", 1)

    dirs = dirs.split('/')

    path = '/'.join([s[0:1] for s in dirs[:-1]])
    path += '/' + dirs[-1] if len(dirs) > 1 else dirs[-1]

    idx = self.shell.execution_count

    A = (cli is None) or cli.vi_state.operator_func
    B = (cli is None) or cli.vi_state.input_mode != ViInputMode.NAVIGATION

    P1 = [(Token.Literal, path),
              (Token.Generic, ' [%d] ' % idx),
              (Token.Operator, '❯'),
              (Token.String, '❯'),
              (Token.PromptNum, '❯ ')]

    P2 = [(Token.Literal, path),
              (Token.Generic, ' [%d] ' % idx),
              (Token.Operator, '❮'),
              (Token.String, '❮'),
              (Token.PromptNum, '❮ ')]

    if not cli:
      return P1 if not self.prompt_mode else P2

    if self.shell.editing_mode != 'vi' or A or B:
      self.prompt_mode = 0
      return P1
    else:
      self.prompt_mode = 1
      return P2

cfg.TerminalInteractiveShell.prompts_class = CwdPrompt
cfg.TerminalInteractiveShell.highlighting_style="monokai"
