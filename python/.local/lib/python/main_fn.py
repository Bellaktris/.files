"""Main fn decorators by Yury Gitman, 2017."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys, os, traceback, signal


# ROOTPATH = os.path.dirname(__file__) + '/..'
# ROOTPATH = os.path.abspath(ROOTPATH)
ROOTPATH = '---------------------------------'


def process_assert_exception(exception):
  """Prints properly formatted assert exception."""

  _, _, info, text = sys.exc_info() + ('',)
  trace = traceback.extract_tb(info)

  text += '\n statement: {}\n'

  for trace_frame in trace[-1:-2:-1]:
    filename, line, function, _ = trace_frame
    basename = os.path.basename(filename)

    if filename.startswith(ROOTPATH):
      format_tmpl = '  function: {} ({}:{})\n'
      format_args = (function, basename, line)
      text += format_tmpl.format(*format_args)

  statement = trace[-1][3][7:]

  try:
    statement, data = statement.split(', ', 1)
  except ValueError:
    data = None

  text += '\n {}: {}\n' if data else ''

  format_args = (statement,)

  if data is not None and data[0] != '(':
    format_args += (data, exception)
  elif data is not None:
    format_args += (data[1:-1], str(exception)[1:-1])

  print(("\033[91m%s\033[0m" % text).format(*format_args))


@decorator.decorator
def with_logging(decorated_function):
  """Wraps function call with logging init."""

  # logging.basicConfig()
  logger = logging.getLogger("main")
  logger.addHandler(logging.StreamHandler())
  logger.handlers[-1].setLevel(logging.ERROR)
  return decorated_function()


@decorator.decorator
def with_try_catch(decorated_function):
  """Wraps function call with try-catch."""

  try:
    return decorated_function()

  except AssertionError as exception:
    process_assert_exception(exception)

  except KeyboardInterrupt:
    text = '\n.......Interrupted.......\n'
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    print("\033[91m" + text + "\033[0m")
