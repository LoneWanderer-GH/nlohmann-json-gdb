
echo #\n
echo # Force gdb to use pretty print of structures managed by default (instead of a barely flat line)\n
set print pretty

source offsets_finder.py

#
echo #\n
echo # Auto setting break point before exe prints mixed_nested\n
break main.cpp:44


# code to execute once breakpoint is reached (basically, full jsons prints using various methods)
command 1

echo #\n
echo # ### Prints using python pretty printer offsetts finder ###\n
echo #\n
echo # Print foo (python pretty printer)\n
p simple_json
echo \n\n\n

echo #\n
p simple_array
echo \n\n\n

end

echo #\n
echo # Running the exe\n
r


