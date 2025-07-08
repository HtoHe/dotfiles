 ;; Custom settings(packages)

(require 'package)
(add-to-list 'package-archives '("melpa" . "https://melpa.org/packages/") t)
;; Comment/uncomment this line to enable MELPA Stable if desired.  See `package-archive-priorities`
;; and `package-pinned-packages`. Most users will not need or want to do this.
;;(add-to-list 'package-archives '("melpa-stable" . "https://stable.melpa.org/packages/") t)
(package-initialize)

;;Install packages
;;(setq my-package-list '(zenburn-theme evil magit))
;;(maqc #'package-install my-package-list)

(load-theme 'zenburn t)

;;(add-hook 'after-init-hook 'global-company-mode)
;;(setq company-dabbrev-downcase 0)
;;(setq company-idle-delay 0)

;;(require 'evil)
;;(evil-mode 1)
;;(evil-set-undo-system 'undo-redo)

;;(setq evil-want-keybinding nil)
;;(when (require 'evil-collection nil t)
 ;; (evil-collection-init '(org magit dired)))

;;(global-flycheck-mode)

;;(evilem-default-keybindings "SPC")

;;(global-set-key (kbd "M-x") #'helm-M-x)
;;(global-set-key (kbd "C-x r b") #'helm-filtered-bookmarks)
;;(global-set-key (kbd "C-x C-f") #'helm-find-files)

;;Magit seq error fix
;;(setq package-install-upgrade-built-in t)
;;(progn (unload-feature 'seq t) (require 'seq))

;;(require 'helm)
;;(helm-mode 1)

;;(require 'company)
;;(add-to-list 'company-backends 'company-c-headers)

;;(with-eval-after-load 'flycheck
;;  (flycheck-pos-tip-mode))

;;(require 'rust-mode)

;;(pdf-tools-install)  ; Standard activation command
(pdf-loader-install) ; On demand loading, leads to faster startup time

;;(use-package pdf-view-restore
;;  :after pdf-tools
;;  :config
;;  (add-hook 'pdf-view-mode-hook 'pdf-view-restore-mode))

;;(setq pdf-view-restore-filename "~/.emacs.d/.pdf-view-restore")

;;custom setting(ui)
;;(add-to-list 'default-frame-alist
;;             '(font . "DejaVu Sans Mono-10"))
(set-face-attribute 'default nil :family "Dejavu Sans Mono")
(set-face-attribute 'default nil :height 130)
(set-fontset-font t 'hangul (font-spec :name "NanumGothicCoding"))

(setq ring-bell-function 'ignore)

;; (global-display-line-numbers-mode 1)
(global-set-key (kbd "C-x /") 'display-line-numbers-mode)

(global-set-key (kbd "M-o") 'other-window)

;;(global-display-line-numbers-mode 1)
;;(visual-line-mode 1)

(tool-bar-mode -1)
(menu-bar-mode -1)
(scroll-bar-mode -1)

;;(setq inhibit-startup-screen t)

;;(setq initial-frame-alist
;;      '((top . 1) (left . 1) (width . 130) (height . 40)))


;; custom setting(editing)
(setq-default c-basic-offset 4)

;; org mode setting
(setq org-adapt-indentation t)

(winner-mode 1)
(repeat-mode)

;;(global-undo-tree-mode)

;;(custom-set-variables
 ;; custom-set-variables was added by Custom.
 ;; If you edit it by hand, you could mess it up, so be careful.
 ;; Your init file should contain only one such instance.
 ;; If there is more than one, they won't work right.
;; '(evil-undo-system 'undo-tree)
;; '(package-selected-packages
;;   '(pdf-view-restore pdf-tools flycheck-pos-tip company-c-headers evil-easymotion use-package helm flycheck magit avy undo-tree gnu-elpa-keyring-update company zenburn-theme evil)))
(custom-set-faces
 ;; custom-set-faces was added by Custom.
 ;; If you edit it by hand, you could mess it up, so be careful.
 ;; Your init file should contain only one such instance.
 ;; If there is more than one, they won't work right.
 )
(custom-set-variables
 ;; custom-set-variables was added by Custom.
 ;; If you edit it by hand, you could mess it up, so be careful.
 ;; Your init file should contain only one such instance.
 ;; If there is more than one, they won't work right.
 '(package-selected-packages '(magit pdf-tools zenburn-theme))
 '(warning-suppress-types '((comp))))
