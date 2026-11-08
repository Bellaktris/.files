# My configuration files

zsh (a [Prezto fork](https://github.com/Bellaktris/prezto)), neovim
([Bellaktris/vim](https://github.com/Bellaktris/vim)), tmux, git, and a few
scripts, for macOS and Linux.

## Installation

    git clone --recursive https://github.com/Bellaktris/.files ~/.files
    ~/.files/install

Keep the clone at `~/.files`: `main/.vimrc` and `.zprofile` refer to it by that
path.

`install` is safe to re-run, and `install -n` shows what it would do without
doing it. It:

1. fetches the submodules;
2. installs whatever is missing of stow, git, zsh, tmux, neovim, python3,
   cmake, curl, fzf, ripgrep, universal-ctags, the tree-sitter CLI (brew
   only) and a C++ toolchain, through
   brew, apt, dnf or pacman (`--no-tools` skips this);
3. creates `~/.config`, `~/.config/nvim` and `~/.local/bin`, so stow links
   into them rather than replacing them with a link into this repo;
4. moves any real file that is in the way of a link to
   `~/.dotfiles-backup/<date>/`;
5. stows the packages into `$HOME` - `main`, `git` and `fonts` unless others
   are named (`./install main git fonts python`);
6. copies `fonts/Library/Fonts` into `~/Library/Fonts` on macOS, which does
   not reliably load fonts that are symlinks;
7. runs `zsh/runcoms/.zlogin`, which compiles the zsh tree, builds
   `tmux-mem-cpu-load` and installs fzf, and `vim/configs.py`, which installs
   the vim plugins.

Then switch the login shell if it is not zsh yet: `chsh -s "$(command -v zsh)"`.

## Packages

Each top-level directory is a stow package that mirrors `$HOME`:

| package  | contents                                                        |
| -------- | --------------------------------------------------------------- |
| `main`   | `.zshenv`, `.vimrc`, tmux, `.inputrc`, `.dir_colors`, `~/bin`, `.config/{htop,mpv,nvim,cppman}`, `.local/bin` |
| `git`    | `.gitconfig`, global ignore, commit message template, a template whose hooks keep ctags current |
| `fonts`  | `.fonts`, fontconfig; `Library/Fonts` is copied on macOS, not linked |
| `python` | `.pythonrc`, `.pylintrc`, ptpython, flake8, pycodestyle, matplotlib |
| `gdb`    | `.gdbinit` and the dashboard, imshow, qt5printers and backtrace plugins |
| `c++`    | a quick-start template and `prettyprinters.hpp` in `~/.local/include` |
| `fbterm` | framebuffer terminal config, for Linux consoles                 |

`zsh/` and `vim/` are submodules and not stowed: `~/.zshenv` (from `main`)
points zsh at `zsh/runcoms/`, and `~/.vimrc` (also from `main`) loads
`vim/vimrc/main.vim`. See their own readmes.

## Scripts in ~/bin

| script     | what it is                                   | needs                     |
| ---------- | -------------------------------------------- | ------------------------- |
| `mpcc`     | mpd client over mpc and fzf, with an up-next block | mpd, mpc            |
| `mpcc-tag` | apply `tags.conf` to the library's Ogg tags  | python3                   |
| `oggtag`   | read and write multi-valued Ogg comments     | python3                   |
| `yt2ogg`   | YouTube audio to `.ogg` without re-encoding  | yt-dlp, ffmpeg            |
| `vpnchain` | chained WireGuard-over-SOCKS proxy for a browser (macOS) | sing-box; tor, i2pd optional |

Their dependencies are not installed by `install`. Each documents itself in
the comment block at its top.

## Machine-local settings

Never committed, read when present:

- `zsh/runcoms/.zprofile-local`, `zsh/runcoms/.zshrc-local`
- `vim/vimrc/secret.vim`
- `~/.gitconfig-local` - put `[user]` name and email here

## Updating

    git -C ~/.files pull --recurse-submodules
    ~/.files/install
