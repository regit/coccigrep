" Vim global plugin for calling coccigrep
" Last Change: 2012 Aug 31
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
    let argl = []
    let i = 1
    while i <= a:0
        if stridx(a:{i}, '"') == 0
            " Check quoted value
            if stridx(a:{i}, '"', 1) == len(a:{i}) - 1
                call add(argl, a:{i})
                let i += 1
                continue
            endif
            let tmparg = a:{i}
            if i + 1 == a:0
                echohl WarningMsg | echo "Warning: Unbalanced quotes" | echohl None
                return
            endif
            let i += 1
            while 1
                let tmparg = tmparg." ". a:{i}
                if stridx(a:{i}, '"') == len(a:{i}) - 1
                    call add(argl, tmparg)
                    let i += 1
                    break
                elseif i == a:0
                    echohl WarningMsg | echo "Warning: Unfinished quotes" | echohl None
                    return
                endif
                let i += 1
            endwhile
        else
            call add(argl, a:{i})
            let i += 1
        endif
    endwhile

    if !exists("g:coccigrep_files")
        let s:b_files_arg = 1
    else
        let s:b_files_arg = 0
    endif

" if we've got
"    0 args: interactive mode
    if len(argl) == 0
        call inputsave()
        let s:type = input('Enter type: ')
        let s:attribute = input('Enter attribute: ')
        let s:op_list = system(g:coccigrep_path . ' -L')
        let s:operation = input('Enter operation in ('. substitute(s:op_list,'\n','','g') . '): ')
        let s:files = input('Enter files: ')
        call inputrestore()
        let cgrep = '-V '
        if s:type
            let cgrep = cgrep. '-t ' . shellescape(s:type) . ' '
        endif
        if s:attribute
            let cgrep = cgrep. '-a ' . s:attribute . ' '
        endif
        let cgrep = cgrep . '-o ' . s:operation . ' ' . s:files
"    1 args: use files in current dir
    elseif len(argl) == (0 + s:b_files_arg)
        let cgrep = '-V -t ' . get(argl, 0) . ' *.[ch]'
"    2 args: 'used' on first arg, second is files
    elseif len(argl) == (1 + s:b_files_arg)
        let cgrep = '-V -t ' . get(argl, 0)
"    3 args: 'deref' operation
    elseif len(argl) == (2 + s:b_files_arg)
        let cgrep = '-V -t ' . get(argl, 0) . ' -a ' . get(argl, 1)
"    4 args: command is type
    elseif len(argl) == (3 + s:b_files_arg)
        let cgrep = '-V -t ' . get(argl, 0) . ' -a ' . get(argl, 1) . ' -o ' . get(argl, 2)
    endif

    if s:b_files_arg
        if ! exists ("s:files")
            let cgrep = cgrep . ' ' . get(argl, len(argl)-1)
        endif
    else
        let cgrep = cgrep . ' -l ' . g:coccigrep_files
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
