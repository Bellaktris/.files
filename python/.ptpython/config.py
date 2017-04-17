# -*- coding: <utf-8> -*-

"""Ptpython configuration file."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from prompt_toolkit.keys import Keys
import prompt_toolkit.key_binding.input_processor as ip

import itertools
from iterfzf import iterfzf

from prompt_toolkit.document import Document

from ptpython.layout import CompletionVisualisation

from prompt_toolkit.filters import ViInsertMode
from prompt_toolkit.filters import HasSearch
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
  repl.true_color = True

  # Use this colorscheme for the code.
  repl.use_code_colorscheme('monokai')

  def reset_buffer_before_accepting(buffer):
    text = buffer.document.text
    nspaces = sum(1 for _ in itertools.takewhile(str.isspace, text))
    text = '\n'.join([line[nspaces:] for line in text.split('\n')])
    buffer.set_document(Document(text.rstrip()))

  @repl.add_key_binding(Keys.Enter,
                        filter=ViInsertMode() & ~HasSearch())
  def _(event):
    document = event.current_buffer.document

    cursor = document.cursor_position_col
    row = document.current_line.rstrip('\r \t')

    if row and len(row) <= cursor and row[-1] == ':':
      event.current_buffer.newline()
      event.current_buffer.insert_text('  ')

    elif row and row[0] == ' ':
      event.current_buffer.newline()

    elif len(row) > cursor:
      event.current_buffer.newline()

    else:
      buffer = event.current_buffer
      reset_buffer_before_accepting(buffer)
      action = buffer.accept_action
      action.validate_and_handle(event.cli, buffer)

  @repl.add_key_binding(Keys.Escape, '[', '1', '3', ';', '2', 'u',
                        filter=ViNavigationMode())
  def _(event):
    document = event.current_buffer.document
    col = document.cursor_position_col

    row = document.current_line
    ws = len(row) - len(row.lstrip())

    event.current_buffer.insert_line_above()
    event.current_buffer.insert_text(' ')

    event.current_buffer.cursor_down()
    event.cli.input_processor.feed(ip.KeyPress('h'))

    for i in range(col - ws):
      event.cli.input_processor.feed(ip.KeyPress('l'))

    event.current_buffer.cancel_completion()

  @repl.add_key_binding(Keys.Enter, filter=ViNavigationMode())
  def _(event):
    document = event.current_buffer.document
    col = document.cursor_position_col

    row = document.current_line
    ws = len(row) - len(row.lstrip())

    event.current_buffer.insert_line_below()
    event.current_buffer.insert_text(' ')

    event.current_buffer.cursor_up()
    event.cli.input_processor.feed(ip.KeyPress('h'))

    for i in range(col - ws):
      event.cli.input_processor.feed(ip.KeyPress('l'))

    event.current_buffer.cancel_completion()

  @repl.add_key_binding(':', 'w', 'q', Keys.Enter,
                        filter=ViNavigationMode())
  def _(event):
    buffer = event.current_buffer
    reset_buffer_before_accepting(buffer)
    action = buffer.accept_action
    action.validate_and_handle(event.cli, buffer)

  @repl.add_key_binding(Keys.ControlR)
  def _(event):
    document = event.current_buffer.document
    line = document.current_line

    history = reversed(event.current_buffer.history)
    gen = map(lambda s: s.replace('\n', '\\n'), history)
    hist_line = iterfzf(gen, exact=True, query=line)

    if hist_line is not None:
      hist_line = hist_line.replace('\n', '\n\n')
      new_doc = Document(hist_line.replace('\\n', '\n'))
      event.current_buffer.set_document(new_doc)

  @repl.add_key_binding(Keys.Tab)
  def _(event):
    document = event.current_buffer.document
    line = document.current_line
    cursor = document.cursor_position_col

    if not line or line[cursor - 1].isspace():
      event.current_buffer.insert_text('  ')
    else:
      event.current_buffer.complete_next()

  @repl.add_key_binding(Keys.Escape,
                        '[', '3', '2', ';', '2', 'u')
  def _(event):
    event.current_buffer.insert_text(' ')

  @repl.add_key_binding('0', filter=ViNavigationMode() | ViWaitingForTextObjectMode())
  def _(event):
    event.cli.input_processor.feed(ip.KeyPress('$'))

  @repl.add_key_binding('-', filter=ViNavigationMode() | ViWaitingForTextObjectMode())
  def _(event):
    event.cli.input_processor.feed(ip.KeyPress('^'))
