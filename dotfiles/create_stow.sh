#!/bin/bash

# Basic home dotfiles
stow -t ~/ --dotfiles home_dotfiles

# .config dotfiles
stow -t ~/.config/ --no-folding dot-config

# .emacs.d init.el
stow -t ~/.emacs.d/ --no-folding dot-emacs.d
