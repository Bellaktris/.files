"""Argparse extra classes by Yury Gitman, 2017."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os, six, argparse, glob, itertools


_IMG_EXTS = ('.png', '.jpg', '.bmp', '.jpeg')


def _normalized_path(path):
  """Convert filepath to its normal form."""
  return os.path.abspath(os.path.expanduser(path))


def _iendswith(string, suffix):
  """Check if string ends with suffix."""
  return string.lower().endswith(suffix)


def _assert_non_empty(iterable):
  """Assert that next exists and fetch it."""
  first_elem = six.next(iterable, None)
  assert first_elem is not None, first_elem
  return itertools.chain([first_elem], iterable)


def _assert_file_is_good(filename):
  """Assserts that file exists and is readable*."""

  if not filename:
    return

  assert os.path.isfile(filename), filename
  assert os.access(filename, os.R_OK), filename
  assert os.access(filename, os.W_OK), filename


def _assert_dir_already_exists(dirname):
  """Assserts that dirname exists or create on*e."""

  if not dirname:
    return

  assert os.path.isdir(dirname), dirname
  assert os.access(dirname, os.R_OK), dirname
  assert os.access(dirname, os.W_OK), dirname


def _assert_dir_exists(dirname):
  """Assserts that dirname exists or create one."""

  if not dirname:
    return

  if not os.path.exists(dirname):
    text = "directory %s doesn't exist, so creating"
    print("\033[93m" + text % dirname + "\033[0m")

    os.makedirs(dirname)

  assert os.path.isdir(dirname), dirname
  assert os.access(dirname, os.R_OK), dirname
  assert os.access(dirname, os.W_OK), dirname


FLOAT_INF = float('inf')


def store_and(callable):
  """Stores value and call callable."""

  class store_and_action(argparse.Action):
    def __call__(self, *args, **kwargs):
      callable.__call__(args[2])
      setattr(args[1], self.dest, args[2])

  return store_and_action


class input_dir(str):
  """Argparse type for input dir options."""
  is_path, is_dir = True, True

  def __new__(cls, path):
    npath = _normalized_path(path) + '/'
    _assert_dir_already_exists(npath)
    return str.__new__(cls, npath)

  def __init__(self, path):
    super(input_dir, self).__init__()


class input_file(str):
  """Argparse type for input file options."""
  is_path, is_dir = True, False

  def __new__(cls, path):
    npath = _normalized_path(path)
    _assert_file_is_good(npath)
    return str.__new__(cls, npath)

  def __init__(self, path):
    super(input_file, self).__init__()


class output_dir(str):
  """Argparse type for output dir options."""
  is_path, is_dir = True, True

  def __new__(cls, path):
    npath = _normalized_path(path) + '/'
    _assert_dir_exists(npath)
    return str.__new__(cls, npath)

  def __init__(self, path):
    super(output_dir, self).__init__()


class output_file(str):
  """Argparse type for output file options."""
  is_path, is_dir = True, False

  def __new__(cls, path):
    npath = _normalized_path(path)
    _assert_dir_exists(os.path.dirname(npath))
    return str.__new__(cls, npath)

  def __init__(self, path):
    super(output_file, self).__init__()


def image_dir(ftype=".png"):
  """Image directory factory."""

  class image_dir():
    """Argparse type for input image glob."""
    is_path, is_dir = True, False

    def __str__(self):
      return self.path.__str__()

    def __next__(self):
      return six.next(self.imgs)

    def next(self):
      return six.next(self.imgs)

    def __iter__(self):
      return self

    def __init__(self, path, ext='.png'):
      self.path = _normalized_path(path) + '/'
      _assert_dir_already_exists(self.path)

      self.imgs = glob.iglob(self.path + '*' + ftype)
      self.imgs = _assert_non_empty(self.imgs)

  return image_dir


class input_image(input_file):
  """Argparse type for image file options."""

  def __new__(cls, path):
    assert _iendswith(path, _IMG_EXTS), path
    return input_file.__new__(cls, path)


class output_image(output_file):
  """Argparse type for image file options."""

  def __new__(cls, path):
    assert _iendswith(path, _IMG_EXTS), path
    return output_file.__new__(cls, path)


def ranged_float(A, B=FLOAT_INF):
  """Ranged floats type factory."""

  class ranged_float(float):
    """Float type in [A; B] range."""

    def __init__(self, value):
      assert A <= float(value) <= B, value
      super(ranged_float, self).__init__()

  return ranged_float


def ranged_int(A, B=FLOAT_INF):
  """Ranged floats type factory."""

  class ranged_int(int):
    """Int type in [A; B] range."""

    def __init__(self, value):
      assert A <= int(value) <= B, value
      super(ranged_int, self).__init__()

  return ranged_int


def multiple_of(factor):
  """Factory for x = k * factor, k in Z."""

  class multiple_of(int):
    """Int type in [A; B] range."""

    def __init__(self, k):
      assert int(k) % factor == 0, (k, factor)
      super(multiple_of, self).__init__()

  return multiple_of


def parse_args(parsers, args=None):
  """Returns subparser results."""

  arg_groups = [None] * (len(parsers) - 1)
  for i in range(1, len(parsers)):
    arg_groups[i - 1], args = parsers[i].parse_known_args(args)

  return (parsers[0].parse_args(args),) + tuple(arg_groups)
