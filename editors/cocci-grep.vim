
function! s:CocciGrep(...)
" if we've got
"	0 args: interactive mode
    if a:0 == 0
    	let cgrep = 'coccigrep -V -t Packet src/su*.c'
"	1 args: use files in current dir
	call inputsave()
	let type = input('Enter type: ')
	let attribut = input('Enter attribut: ')
	let operation = input('Enter operation: ')
	let files = input('Enter files: ')
	call inputrestore()
    	let cgrep = 'coccigrep -V -t ' . type . ' -a ' . attribut . ' -o ' . operation . ' ' . files
    elseif a:0 == 1
    	let cgrep = 'coccigrep -V -t ' . a:1 . ' *.[ch]' 
"	2 args: 'used' on first arg, second is files
    elseif a:0 == 2
    	let cgrep = 'coccigrep -V -t ' . a:1 . ' ' . a:2
"       3 args: 'deref' operation
    elseif a:0 == 3
    	let cgrep = 'coccigrep -V -t ' . a:1 . ' -a ' . a:2 . ' ' . a:3
"	4 args: command is type 
    elseif a:0 == 4
    	let cgrep = 'coccigrep -V -t ' . a:1 . ' -a ' . a:2 . ' -o ' . a:3 . ' ' . a:4
    endif
    :cexpr system(cgrep)
endfunction

command! -nargs=* -complete=tag_listfiles Coccigrep :call <SID>CocciGrep(<f-args>) | cw
