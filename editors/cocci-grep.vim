" Vim global plugin for calling coccigrep
" Last Change: 2011 Aug 28
" Maintener: Eric Leblond <eric@regit.org>
" License: GNU General Public License version 3 or later


if exists("g:loaded_coccigrep")
    finish
endif
let g:loaded_coccigrep = 1

if !exists("g:coccigrep_path")
    let g:coccigrep_path = 'coccigrep'
endif

function! s:CocciGrep(...)
" if we've got
"    0 args: interactive mode
    if a:0 == 0
        call inputsave()
        let s:type = input('Enter type: ')
        let s:attribut = input('Enter attribut: ')
        let s:op_list = system(g:coccigrep_path . ' -L')
        let s:operation = input('Enter operation in ('. substitute(s:op_list,'\n','','g') . '): ')
        let s:files = input('Enter files: ')
        call inputrestore()
        let cgrep = '-V -t ' . s:type . ' -a ' . s:attribut . ' -o ' . s:operation . ' ' . s:files
"    1 args: use files in current dir
    elseif a:0 == 1
        let cgrep = '-V -t ' . a:1 . ' *.[ch]'
"    2 args: 'used' on first arg, second is files
    elseif a:0 == 2
        let cgrep = '-V -t ' . a:1 . ' ' . a:2
"       3 args: 'deref' operation
    elseif a:0 == 3
        let cgrep = '-V -t ' . a:1 . ' -a ' . a:2 . ' ' . a:3
"    4 args: command is type
    elseif a:0 == 4
        let cgrep = '-V -t ' . a:1 . ' -a ' . a:2 . ' -o ' . a:3 . ' ' . a:4
    endif
    echo "Running coccigrep, please wait..."
    let cocciout = system(g:coccigrep_path . ' '. cgrep)
    if cocciout == ""
        echohl WarningMsg | echo "Warning: No match found" | echohl None
    else
        :cexpr cocciout | cw
    endif
endfunction

command! -nargs=* -complete=tag_listfiles Coccigrep :call <SID>CocciGrep(<f-args>)
