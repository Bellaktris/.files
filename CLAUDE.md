# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Personal dotfiles, forked from `Bellaktris/.files`. There is no build system, test
suite, or linter for the repo itself — work here is editing config files and
syncing submodules. Two submodules carry most of the substance:

- `vim/` — fork of `Bellaktris/vim` (custom vimrc + plugin list).
- `zsh/` — fork of `Bellaktris/prezto` (custom prezto modules). Itself contains
  a nested submodule `modules/completion/external-modules/autocompletion` →
  `Bellaktris/auto-fu` (another fork, the source of the `afu-vicmd` keymap
  referenced in `.zshrc`).

Plus several gdb plugin submodules under `gdb/.gdb/`.

When pulling, use `--recursive` (or `git submodule update --init --recursive`).
When editing files inside `vim/` or `zsh/`, you are editing the submodule's
working tree — commit there first, then bump the pointer in the outer repo.
The most recent outer-repo commit (`b791d73`) is an example of this pattern.

## Install / re-run

From `readme.md`:

```
source ~/.files/zsh/runcoms/.zlogin       # zcompile + build helpers + install fzf
python3 ~/.files/vim/configs.py           # write ~/.vimrc, ~/.config/nvim/init.vim, run PlugInstall
```

- Re-run `.zlogin` after editing anything under `zsh/modules/` or `zsh/runcoms/`
  to refresh the `.zwc` caches it produces. It also compiles `tmux-mem-cpu-load`
  via cmake on first run and installs `fzf` if missing.
- Re-run `vim/configs.py` after editing `vim/vimrc/main.vim` or moving the repo;
  it rewrites `~/.vimrc` with absolute paths baked in.

There is no symlink/stow automation in the repo for the non-zsh, non-vim dotfiles
under `main/`, `git/`, `python/`, `gdb/`, `c++/`, `fbterm/`, `fonts/` — they are
expected to be symlinked into `$HOME` externally. The one in-repo symlink is
`main/.zshenv -> ../zsh/runcoms/.zshenv`.

## Architecture

### zsh: ZDOTDIR-rooted, not $HOME-rooted

`zsh/runcoms/.zshenv` sets `ZDOTDIR` to its own directory:

```
export ZDOTDIR=${${(%):-%N}:A:h}
```

So only `~/.zshenv` (a symlink to this file) needs to live in `$HOME`; every
other zsh file (`.zprofile`, `.zshrc`, `.zlogin`, `.zpreztorc`) is read from
`zsh/runcoms/` directly. Prezto's `init.zsh` is sourced from `zsh/runcoms/.zshrc`.

Machine-local overrides are sourced if present and never committed:
- `zsh/runcoms/.zprofile-local` (from `.zprofile`)
- `zsh/runcoms/.zshrc-local` (from `.zshrc`)
- `~/.gitconfig-local` (from `git/.gitconfig`)

Active prezto modules and their settings are configured in `zsh/runcoms/.zpreztorc`.
Custom modules added on top of upstream prezto live under `zsh/modules/` —
notably `autosuggestions`, the auto-fu fork under
`completion/external-modules/autocompletion` (compiled by `.zlogin`, drives the
`afu-vicmd` keymap), `syntax-highlighting`, and `tmux` (which vendors
`tmux-mem-cpu-status`).

`.zlogin` does a lot: it backgrounds (`&!`) a job that calls `zrecompile` on
nearly every zsh file in the tree, builds `tmux-mem-cpu-load`, installs `fzf`,
and cleans up stale `.zwc.old` files. Keep that pattern in mind when adding new
zsh code — it should compile cleanly under `zrecompile`.

### vim: configs.py generates ~/.vimrc; main.vim is the source

`vim/configs.py` writes a tiny `~/.vimrc` that hard-codes absolute paths to
`vim/vimrc/main.vim`, `vim/ultisnips/`, and `~/.tempd`. `~/.config/nvim/init.vim`
is generated to just `source $HOME/.vimrc`.

The real plugin list and configuration is `vim/vimrc/main.vim`, which uses
vim-plug installed to `~/.vim-thirdparty`. Per-plugin tuning lives in
`vim/vimrc/plugin-options/*.vim`. `vim/vimrc/secret.vim` is auto-created empty
and is the place for machine-local vim settings.

`main/.vimrc` is an alternate bootstrap that points at the same `main.vim`
without going through `configs.py` — useful when you can't run python.

### tmux

`main/.tmux.conf` sets prefix to `` ` ``, then sources either
`.tmux-local.conf` or `.tmux-remote.conf` depending on `$SSH_TTY`.
The status line uses `tmux-mem-cpu-load` built by `.zlogin`.

### git

`git/.gitconfig` includes `~/.gitconfig-local` for user identity / secrets
(not committed). The pager and interactive diff filter both shell out to
`diff-so-fancy`, so that binary needs to be on PATH.

Commit message style (from `git/.gitmessage` and recent history): short
imperative subject; multi-action commits list the actions
(e.g. "Update zsh submodule: replace echo with printf, fix TRAPEXIT errors").

### main/

`main/` mirrors `$HOME` layout: top-level dotfiles (`.vimrc`, `.tmux.conf`,
`.inputrc`, `.dir_colors`), `.config/{htop,nvim,mpv,cppman}`, `.local/bin/`,
and `bin/mpcc` (a python MPD client that wraps `fzf-tmux`).

## Conventions

- No emojis in config files or commit messages.
- Don't commit `.zwc` / `.zcompdump` / `.DS_Store` / `*.pyc` — `.gitignore`
  and `git/.gitignore_global` already cover these.
- Don't commit `*-local` override files or `vim/vimrc/secret.vim`.
- When changing zsh behavior, prefer editing the submodule (`zsh/`) and then
  bumping the pointer here, rather than working around prezto in `runcoms/`.
