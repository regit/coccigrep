;; Copyright (C) 2011 Eric Leblond
;;
;; this file is not part of Emacs
;;
;; Author: Eric Leblond
;; Maintainer: Eric Leblond
;; Description: provide interface to coccigrep
;;
;; Based on xargs-grep module by Le Wang
;;
;;; Installation: put this file in your load-path and
;;
;; (require 'cocci-grep)
;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;
;; This program is free software; you can redistribute it and/or
;; modify it under the terms of the GNU General Public License as
;; published by the Free Software Foundation; either version 3, or
;; (at your option) any later version.
;;
;; This program is distributed in the hope that it will be useful,
;; but WITHOUT ANY WARRANTY; without even the implied warranty of
;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
;; General Public License for more details.
;;
;; You should have received a copy of the GNU General Public License
;; along with this program; see the file COPYING.  If not, write to
;; the Free Software Foundation, Inc., 51 Franklin Street, Fifth
;; Floor, Boston, MA 02110-1301, USA.
;;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

(require 'compile)
(require 'grep)

(defvar cocci-s-type-history '()
  "The minibuffer history list for `\\[cocci-grep]'s type argument.")

(defvar cocci-s-attribute-history '()
  "The minibuffer history list for `\\[cocci-grep]'s attribute argument.")

(defvar cocci-s-operation-history '()
  "The minibuffer history list for `\\[cocci-grep]'s operation argument.")

(defvar cocci-files-history '()
  "The minibuffer history list for `\\[cocci-grep]'s files argument.")


(defun cocci-grep-read-type ()
  (read-from-minibuffer "Type: "
                        nil nil nil
                        'cocci-s-type-history
                        nil))
(defun cocci-grep-read-attribute ()
  (read-from-minibuffer "Attribut: "
                        nil nil nil
                        'cocci-s-attribute-history
                        nil))
(defun cocci-grep-read-operation ()
  (read-from-minibuffer "Operation: "
                        nil nil nil
                        'cocci-s-operation-history
                        nil))
(defun cocci-grep-read-file-string ()
  (read-from-minibuffer "Files: "
   nil nil nil
   'cocci-files-history
   nil))

;;;###autoload
(defun cocci-grep (s-type s-attribute s-operation files)
  "s-type is the searched type, s-attribute the attribute, s-operation the
operation on structure and files is a blob expression that will match files"
  (interactive (list
                (cocci-grep-read-type)
                (cocci-grep-read-attribute)
                (cocci-grep-read-operation)
                (cocci-grep-read-file-string)))
  (let (out-buf
        )
    (setq out-buf (compilation-start (concat "coccigrep -E -t " s-type " -a " s-attribute
                                             " -o " s-operation " " files) 'grep-mode))
    ))

(provide 'cocci-grep)

