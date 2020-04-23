
echo #\n
echo # Force gdb to use pretty print of structures managed by default (instead of a barely flat line)\n
set print pretty


# load the classic STL gdb tools for navigating in std collections (std::map, std::vector ...)
# nbot absolutly necessary, but is helpful
echo #\n
echo # Loading STL gdb script\n
source ../../scripts/stl_parser.gdb

# examples on how to use the STL / STD gdb readers
# pset foo.m_value.object nlohmann::json
# pmap foo.m_value.object std::string nlohmann::json*
# pmap foo.m_value.object std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>> nlohmann::json*


# load the simple gdb method requiring a live inferior process
echo #\n
echo # Loading simple gdb json dump method\n
source ../../scripts/nlohmann_json.gdb


# load the python gdb pretty printer
echo #\n
echo # Loading the complex gdb json dump method\n
source ../../scripts/nlohmann_json.py

#
echo #\n
echo # Auto setting break point before exe prints mixed_nested\n
break main.cpp:70


# code to execute once breakpoint is reached
# (basically, full jsons prints using various methods)
command 1

echo #\n
echo # ### Prints using gdb custom command ###\n
echo #\n
echo # Print foo (gdb custom command)\n
pjson fooz
echo \n\n\n

echo #\n
echo # Print arr (gdb custom command)\n
pjson arr
echo \n\n\n

echo #\n
echo # Print one (gdb custom command)\n
pjson one
echo \n\n\n

echo #\n
echo # Print foo (gdb custom command)\n
pjson foo
echo \n\n\n

echo #\n
echo # Print mixed_nested (gdb custom command)\n
pjson mixed_nested
echo \n\n\n



echo #\n
echo # ### Prints using python pretty printer ###\n
echo #\n
echo # Print foo (python pretty printer)\n
p fooz
echo \n\n\n

echo #\n
echo # Print arr (python pretty printer)\n
p arr
echo \n\n\n

echo #\n
echo # Print one (python pretty printer)\n
p one
echo \n\n\n

echo #\n
echo # Print foo (python pretty printer)\n
p foo
echo \n\n\n

echo #\n
echo # Print mixed_nested (python pretty printer)\n
p mixed_nested
echo \n\n\n
end

echo #\n
echo # Running the exe\n
r


