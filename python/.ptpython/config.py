# -*- coding: utf-8 -*-

"""Ptpython configuration file."""

import os, subprocess, shutil

from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.keys import Keys
import prompt_toolkit.key_binding.key_processor as kp

from ptpython.layout import CompletionVisualisation

from prompt_toolkit.filters import ViInsertMode
from prompt_toolkit.filters import ViNavigationMode
from prompt_toolkit.filters import ViWaitingForTextObjectMode

__all__ = ('configure',)


def configure(repl):
  """Main configuration function."""

  # Show function signature (bool).
  repl.show_signature = True

  # Show docstring (bool).
  repl.show_docstring = True

  # Show completions. (NONE, POP_UP, MULTI_COLUMN or TOOLBAR)
  repl.completion_visualisation = CompletionVisualisation.POP_UP

  # Paste mode. (When True, don't insert whitespace after new line.)
  repl.paste_mode = True

  # When CompletionVisualisation.POP_UP has been chosen, use this
  # scroll_offset in the completion menu.
  repl.completion_menu_scroll_offset = 0

  # Show line numbers (when the input contains multiple lines.)
  repl.show_line_numbers = True

  # Show status bar.
  repl.show_status_bar = False

  # When the sidebar is visible, also show the help text.
  repl.show_sidebar_help = False

  # Highlight matching parethesis.
  repl.highlight_matching_parenthesis = True

  # Line wrapping. (Instead of horizontal scrolling.)
  repl.wrap_lines = True

  # Mouse support.
  repl.enable_mouse_support = False

  # Complete while typing.
  repl.enable_dictionary_completion = True
  repl.enable_fuzzy_completion = True
  repl.complete_while_typing = True

  # Vi mode.
  repl.vi_mode = True

  # Use the ipython prompt.
  repl.prompt_style = 'ipython'

  # History Search.
  repl.enable_history_search = False

  # Enable auto suggestions.
  repl.enable_auto_suggest = False

  # Enable open-in-editor.
  repl.enable_open_in_editor = True

  # Enable system prompt.
  repl.enable_system_bindings = True

  # Ask for confirmation on exit.
  repl.confirm_exit = False

  # Enable input validation.
  repl.enable_input_validation = True

  # Enable 24bit True color.
  repl.color_depth = "DEPTH_24_BIT"

  # Use this colorschemes for the code and UI.
  repl.use_code_colorscheme('monokai')

  # Update key bindings to my custom style.
  @repl.add_key_binding('0', filter=ViNavigationMode() | ViWaitingForTextObjectMode())
  def _(event):
    event.app.key_processor.feed(kp.KeyPress('$'))

  @repl.add_key_binding('-', filter=ViNavigationMode() | ViWaitingForTextObjectMode())
  def _(event):
    event.app.key_processor.feed(kp.KeyPress('^'))

  # Ctrl-R searches the history through fzf. The entries come from ptpython's
  # own history object rather than its file, so this works wherever the file
  # lives; NUL-separated, so a multi-line entry stays one entry. No --scheme:
  # it needs fzf 0.36, and Ubuntu 22.04 ships 0.29.
  if shutil.which('fzf'):
    @repl.add_key_binding(Keys.ControlR, filter=ViInsertMode() | ViNavigationMode())
    async def _(event):
      # Newest first, each entry once.
      entries = list(dict.fromkeys(reversed(repl.history.get_strings())))
      if not entries:
        return

      def pick():
        try:
          return subprocess.run(
            ['fzf', '--read0', '--print0', '--no-sort', '--exact',
             '--no-multi', '--prompt=history> '],
            input='\0'.join(entries), stdout=subprocess.PIPE, text=True)
        except (OSError, subprocess.SubprocessError):
          return None

      # Suspends the prompt while fzf owns the terminal, and redraws after.
      result = await run_in_terminal(pick)
      selected = result.stdout.rstrip('\0') if result else ''
      if result and result.returncode == 0 and selected:
        buf = event.app.current_buffer
        buf.text = selected
        buf.cursor_position = len(buf.text)
