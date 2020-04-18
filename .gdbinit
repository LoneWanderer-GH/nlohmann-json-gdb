set print pretty
source stl_parser.gdb

define pjson
# use the lohmann's builtin dump method, ident 4 and use space separator
printf "%s\n", $arg0.dump(4, ' ', true, json::error_handler_t::strict).c_str()
end
# configure command helper (text displayed when typing 'help pjson' in gdb)
document pjson
Prints a lohmann's JSON C++ variable as a human-readable JSON string
end

source printer.py
python gdb.printing.register_pretty_printer(gdb.current_objfile(), build_pretty_printer())

r
#

#echo "---\n"
#p fooz

#echo "---\n"
#p arr

#echo "---\n"
#p one

p foo

#echo "---\n"

# pset foo.m_value.object nlohmann::json
# pmap foo.m_value.object std::string nlohmann::json*

# pmap foo.m_value.object std::__cxx11::basic_string<char,std::char_traits<char>,std::allocator<char>> nlohmann::json*
