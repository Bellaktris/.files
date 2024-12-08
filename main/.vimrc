if !exists('g:root_dir')
  let g:vimrc_dir = "/Users/ygitman/.files/vim/vimrc"
  let g:temp_dir = "/Users/ygitman/.tempd"
  let g:snippet_dir = "/Users/ygitman/.files/vim/ultisnips"

  if !isdirectory(g:temp_dir)
      execute 'silent !mkdir -p ' . g:temp_dir
  endif

  if !isdirectory($HOME + '/.vim')
      execute 'silent !mkdir -p ' . $HOME . '/.vim'
  endif

  let g:root_dir = "/Users/ygitman/.files/vim"
  let g:vim_plug_dir = "/Users/ygitman/.vim-thirdparty"

  execute 'let &runtimepath .=",' . g:root_dir . '"'

  execute 'source ' . g:vimrc_dir . '/main.vim'
endif
