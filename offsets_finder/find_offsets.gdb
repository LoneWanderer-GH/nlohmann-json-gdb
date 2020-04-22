
echo #\n
echo # Force gdb to use pretty print of structures managed by default (instead of a barely flat line)\n
echo #\n
echo # set print pretty\n
echo #\n
set print pretty


echo #\n
echo # load the offset finder python gdb script\n
echo #\n
echo source offsets_finder.py\n
echo #\n
source offsets_finder.py

#
echo #\n
echo # Auto setting break point before exe prints mixed_nested\n
echo #\n
break main.cpp:44


# code to execute once breakpoint is reached (basically, full jsons prints using various methods)
command 1

echo #\n
echo # ### Prints using python pretty printer offsetts finder ###\n
echo #\n
echo # Print simple_json (python pretty printer)\n
p simple_json
echo \n\n\n

echo #\n
echo # Print simple_array (python pretty printer)\n
echo #\n
p simple_array
echo \n\n\n

end

echo #\n
echo # Running the exe\n
r


