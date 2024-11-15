#!/bin/bash

# Basic home dotfiles
stow -nv -t ~/ --dotfiles home_dotfiles

# .config dotfiles
stow -nv -t ~/.config/ --no-folding dot-config

# .emacs.d init.el
stow -nv -t ~/.emacs.d/ --no-folding dot-emacs.d
