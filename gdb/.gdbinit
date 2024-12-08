# General
set disassembly-flavor intel
alias exit = quit

set history size 10000
set history remove-duplicates 50
set history filename ~/.gdb_history

define quiet
  set logging file /dev/null
  set logging redirect on
  set logging on

  if $argc == 1
    $arg0
  end

  if $argc == 2
    $arg0 $arg1
  end

  if $argc == 3
    $arg0 $arg1 $arg2
  end

  shell clear
  set logging off
end

catch throw

# Add libc++ pretty printers
python
import sys, os.path
sys.path.insert(0, os.path.expanduser('~/.gdb/libc++'))
from libcxx.printers import register_libcxx_printers
register_libcxx_printers (None)
end

# Source python dashboard
source ~/.gdb/dashboard/.gdbinit

dashboard -layout source expressions
dashboard stack -style locals True

# dashboard -style prompt_running     '(gdb) [1m[31m❯[33m❯[32m❯[39m[0m'
# dashboard -style prompt_not_running '(gdb) [1m[31m❯[33m❯[32m❯[39m[0m'

alias pprint = 'dashboard expressionsv2 watch'
alias pclear = 'dashboard expressionsv2 unwatch'

# Slightly prettify backtrace
python
import sys, os.path
sys.path.insert(0, os.path.expanduser('~/.gdb/backtrace'))
import framefilter
framefilter.CppFrameFilter()
end

# Add Eigen pretty printers
python
import sys, os.path
sys.path.insert(0, os.path.expanduser('~/.gdb/eigen'))
from eigen_printers import register_eigen_printers
register_eigen_printers(None)
end

# Add command for investigating OpenCV images
source ~/.gdb/imshow/cv_imshow.py
alias imshow = cv_imshow

# Add Qt5 pretty printers
python
import sys, os.path
sys.path.insert(0, os.path.expanduser('~/.gdb'))
import qt5printers
qt5printers.register_printers(gdb.current_objfile())
end
