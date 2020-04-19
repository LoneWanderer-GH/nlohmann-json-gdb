#
# Licensed under the MIT License <http://opensource.org/licenses/MIT>.
# SPDX-License-Identifier: MIT
# Copyright (c) 2020 LoneWanderer-GH https://github.com/LoneWanderer-GH
#
# Permission is hereby  granted, free of charge, to any  person obtaining a copy
# of this software and associated  documentation files (the "Software"), to deal
# in the Software  without restriction, including without  limitation the rights
# to  use, copy,  modify, merge,  publish, distribute,  sublicense, and/or  sell
# copies  of  the Software,  and  to  permit persons  to  whom  the Software  is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE  IS PROVIDED "AS  IS", WITHOUT WARRANTY  OF ANY KIND,  EXPRESS OR
# IMPLIED,  INCLUDING BUT  NOT  LIMITED TO  THE  WARRANTIES OF  MERCHANTABILITY,
# FITNESS FOR  A PARTICULAR PURPOSE AND  NONINFRINGEMENT. IN NO EVENT  SHALL THE
# AUTHORS  OR COPYRIGHT  HOLDERS  BE  LIABLE FOR  ANY  CLAIM,  DAMAGES OR  OTHER
# LIABILITY, WHETHER IN AN ACTION OF  CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE  OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

# disclaimer:
# I'm not a layern and I like to give people credit as much as I
# like them given me. I was inspired or adapted some code pieces her and there
# the source link is given in comments.

import gdb
import platform
import sys
import traceback

# adapted from https://github.com/hugsy/gef/blob/dev/gef.py
# their rights are theirs
HORIZONTAL_LINE = "_"  # u"\u2500"
LEFT_ARROW = "<-"  # "\u2190 "
RIGHT_ARROW = "->"  # " \u2192 "
DOWN_ARROW = "|"  # "\u21b3"

# the stirngs were obtained with gdb
nlohmann_json_type_namespace = \
    r"nlohmann::basic_json<std::map, std::vector, std::__cxx11::basic_string<char, std::char_traits<char>, " \
    r"std::allocator<char> >, bool, long long, unsigned long long, double, std::allocator, nlohmann::adl_serializer>"
nlohmann_json_internal_map_type = \
    r"std::map<" \
    r"std::__cxx11::basic_string<" \
    r"char, std::char_traits<char>, std::allocator<char> >, " \
    r"nlohmann::basic_json<std::map, std::vector, std::__cxx11::basic_string<char, std::char_traits<char>, " \
    r"std::allocator<char> >, bool, long long, unsigned long long, double, std::allocator, nlohmann::adl_serializer>, " \
    r"std::less<void>, std::allocator<std::pair<std::__cxx11::basic_string<char, std::char_traits<char>, " \
    r"std::allocator<char> > const, nlohmann::basic_json<std::map, std::vector, std::__cxx11::basic_string<char, " \
    r"std::char_traits<char>, std::allocator<char> >, bool, long long, unsigned long long, double, std::allocator, " \
    r"nlohmann::adl_serializer> > > " \
    r">"

# STD black magic
MAGIC_STD_VECTOR_OFFSET = 16  # win 10 x64 values
MAGIC_OFFSET_STD_MAP = 32     # win 10 x64 values

""""""
# GDB black magic
""""""
nlohmann_json_type = gdb.lookup_type(nlohmann_json_type_namespace).pointer()
std_rb_tree_node_type = gdb.lookup_type("std::_Rb_tree_node_base::_Base_ptr").pointer()
std_rb_tree_size_type = gdb.lookup_type("std::size_t").pointer()

""""""
# from source code. copy here for readability/understanding
# nlohmann_json reminder
# enum class value_t : std::uint8_t
# {
#     null,             ///< null value
#     object,           ///< object (unordered set of name/value pairs)
#     array,            ///< array (ordered collection of values)
#     string,           ///< string value
#     boolean,          ///< boolean value
#     number_integer,   ///< number value (signed integer)
#     number_unsigned,  ///< number value (unsigned integer)
#     number_float,     ///< number value (floating-point)
#     discarded         ///< discarded by the the parser callback function
# };

""""""
enum_literals_namespace = ["nlohmann::detail::value_t::null",
                           "nlohmann::detail::value_t::object",
                           "nlohmann::detail::value_t::array",
                           "nlohmann::detail::value_t::string",
                           "nlohmann::detail::value_t::boolean",
                           "nlohmann::detail::value_t::number_integer",
                           "nlohmann::detail::value_t::number_unsigned",
                           "nlohmann::detail::value_t::number_float",
                           "nlohmann::detail::value_t::discarded"]

enum_literal_namespace_to_literal = dict([(e, e.split("::")[-1]) for e in enum_literals_namespace])

INDENT = 4


def std_stl_item_to_int_address(node):
    return int(str(node), 0)


def parse_std_str_from_hexa_address(hexa_str):
    # https://stackoverflow.com/questions/6776961/how-to-inspect-stdstring-in-gdb-with-no-source-code
    return '"{}"'.format(gdb.parse_and_eval("*(char**){}".format(hexa_str)).string())


class LohmannJSONPrinter(object):
    """Print a nlohmann::json in GDB python
    BEWARE :
     - Contains shitty string formatting (defining lists and playing with ",".join(...) could be better; ident management is stoneage style)
     - Parsing barely tested only with a live inferior process.
     - It could possibly work with a core dump + debug symbols.
            TODO: read that stuff https://doc.ecoscentric.com/gnutools/doc/gdb/Core-File-Generation.html
     - Not idea what happens with no symbols available, lots of fields are retrieved by name and should be changed to offsets if possible
     - NO LIB VERSION MANAGEMENT.
            TODO: determine if there are serious variants in nlohmann data structures that would justify working with strucutres
     - PLATFORM DEPENDANT
            TODO: remove the black magic offsets or handle them in a nicer way (get the exact types sizes with some gdb commands)
    NB: If you are python-kaizer-style-guru, please consider helping or teaching how to improve all that mess
    """

    def __init__(self, val, indent_level=0):
        self.val = val
        self.field_type_full_namespace = None
        self.field_type_short = None
        self.indent_level = indent_level

        self.function_map = {"nlohmann::detail::value_t::null"           : self.parse_as_leaf,
                             "nlohmann::detail::value_t::object"         : self.parse_as_object,
                             "nlohmann::detail::value_t::array"          : self.parse_as_array,
                             "nlohmann::detail::value_t::string"         : self.parse_as_str,
                             "nlohmann::detail::value_t::boolean"        : self.parse_as_leaf,
                             "nlohmann::detail::value_t::number_integer" : self.parse_as_leaf,
                             "nlohmann::detail::value_t::number_unsigned": self.parse_as_leaf,
                             "nlohmann::detail::value_t::number_float"   : self.parse_as_leaf,
                             "nlohmann::detail::value_t::discarded"      : self.parse_as_leaf}

    def parse_as_object(self):
        assert (self.field_type_short == "object")

        o = self.val["m_value"][self.field_type_short]

        # traversing tree is a an adapted copy pasta from STL gdb parser
        # (http://www.yolinux.com/TUTORIALS/src/dbinit_stl_views-1.03.txt and similar links)

        #   Simple GDB Macros writen by Dan Marinescu (H-PhD) - License GPL
        #   Inspired by intial work of Tom Malnar,
        #     Tony Novac (PhD) / Cornell / Stanford,
        #     Gilad Mishne (PhD) and Many Many Others.
        #   Contact: dan_c_marinescu@yahoo.com (Subject: STL)
        #
        #   Modified to work with g++ 4.3 by Anders Elton
        #   Also added _member functions, that instead of printing the entire class in map, prints a member.

        _M_t = std_stl_item_to_int_address(o.referenced_value().address)
        _M_t_M_impl_M_header_M_left = _M_t + 8 + MAGIC_STD_VECTOR_OFFSET
        _M_t_M_impl_M_node_count = _M_t + 8 + MAGIC_STD_VECTOR_OFFSET + MAGIC_STD_VECTOR_OFFSET

        node = gdb.Value(long(_M_t_M_impl_M_header_M_left)).cast(std_rb_tree_node_type).referenced_value()
        tree_size = gdb.Value(long(_M_t_M_impl_M_node_count)).cast(std_rb_tree_size_type).referenced_value()

        i = 0

        if tree_size == 0:
            return "{}"
        else:
            s = "{\n"
            self.indent_level += 1
            while i < tree_size:
                # STL GDB scripts write "+1" which in my w10 x64 GDB makes a +32 bits move ...
                # may be platform dependant and should be taken with caution
                key_address = std_stl_item_to_int_address(node) + MAGIC_OFFSET_STD_MAP

                k_str = parse_std_str_from_hexa_address(hex(key_address))

                value_address = key_address + MAGIC_OFFSET_STD_MAP
                value_object = gdb.Value(long(value_address)).cast(nlohmann_json_type)

                v_str = LohmannJSONPrinter(value_object, self.indent_level + 1).to_string()

                k_v_str = "{} : {}".format(k_str, v_str)
                end_of_line = "\n" if tree_size <= 1 or i == tree_size else ",\n"

                s = s + (" " * (self.indent_level * INDENT)) + k_v_str + end_of_line  # ",\n"

                if std_stl_item_to_int_address(node["_M_right"]) != 0:
                    node = node["_M_right"] ## todo finish access by offset ?
                    while std_stl_item_to_int_address(node["_M_left"]) != 0:
                        node = node["_M_left"] ## todo finish access by offset ?
                else:
                    tmp_node = node["_M_parent"] ## todo finish access by offset ?
                    while std_stl_item_to_int_address(node) == std_stl_item_to_int_address(tmp_node["_M_right"]):
                        node = tmp_node
                        tmp_node = tmp_node["_M_parent"] ## todo finish access by offset ?

                    if std_stl_item_to_int_address(node["_M_right"]) != std_stl_item_to_int_address(tmp_node):
                        node = tmp_node
                i += 1
            self.indent_level -= 2
            s = s + (" " * (self.indent_level * INDENT)) + "}"
            return s

    def parse_as_str(self):
        return parse_std_str_from_hexa_address(str(self.val["m_value"][self.field_type_short]))

    def parse_as_leaf(self):
        s = "WTFBBQ !"
        if self.field_type_short == "null" or self.field_type_short == "discarded":
            s = self.field_type_short
        elif self.field_type_short == "string":
            s = self.parse_as_str()
        else:
            s = str(self.val["m_value"][self.field_type_short])
        return s

    def parse_as_array(self):
        assert (self.field_type_short == "array")
        o = self.val["m_value"][self.field_type_short]
        start = o["_M_impl"]["_M_start"]
        size = o["_M_impl"]["_M_finish"] - start
        # capacity = o["_M_impl"]["_M_end_of_storage"] - start
        # size_max = size - 1
        i = 0
        start_address = std_stl_item_to_int_address(start)
        if size == 0:
            s = "[]"
        else:
            self.indent_level += 1
            s = "[\n"
            while i < size:
                # STL GDB scripts write "+1" which in my w10 x64 GDB makes a +16 bits move ...
                offset = i * MAGIC_STD_VECTOR_OFFSET
                i_address = start_address + offset
                value_object = gdb.Value(long(i_address)).cast(nlohmann_json_type)
                v_str = LohmannJSONPrinter(value_object, self.indent_level + 1).to_string()
                end_of_line = "\n" if size <= 1 or i == size else ",\n"
                s = s + (" " * (self.indent_level * INDENT)) + v_str + end_of_line
                i += 1
            self.indent_level -= 2
            s = s + (" " * (self.indent_level * INDENT)) + "]"
        return s

    def is_leaf(self):
        return self.field_type_short != "object" and self.field_type_short != "array"

    def parse_as_aggregate(self):
        if self.field_type_short == "object":
            s = self.parse_as_object()
        elif self.field_type_short == "array":
            s = self.parse_as_array()
        else:
            s = "WTFBBQ !"
        return s

    def parse(self):
        # s = "WTFBBQ !"
        if self.is_leaf():
            s = self.parse_as_leaf()
        else:
            s = self.parse_as_aggregate()
        return s

    def to_string(self):
        try:
            self.field_type_full_namespace = self.val["m_type"]
            str_val = str(self.field_type_full_namespace)
            if not str_val in enum_literal_namespace_to_literal:
                return "TIMMY !"
            self.field_type_short = enum_literal_namespace_to_literal[str_val]
            return self.function_map[str_val]()
            # return self.parse()
        except:
            show_last_exception()
            return "NOT A JSON OBJECT // CORRUPTED ?"

    def display_hint(self):
        return self.val.type


# adapted from https://github.com/hugsy/gef/blob/dev/gef.py
def show_last_exception():
    """Display the last Python exception."""
    print("")
    exc_type, exc_value, exc_traceback = sys.exc_info()

    print(" Exception raised ".center(80, HORIZONTAL_LINE))
    print("{}: {}".format(exc_type.__name__, exc_value))
    print(" Detailed stacktrace ".center(80, HORIZONTAL_LINE))
    for (filename, lineno, method, code) in traceback.extract_tb(exc_traceback)[::-1]:
        print("""{} File "{}", line {:d}, in {}()""".format(DOWN_ARROW, filename, lineno, method))
        print("   {}    {}".format(RIGHT_ARROW, code))
    print(" Last 10 GDB commands ".center(80, HORIZONTAL_LINE))
    gdb.execute("show commands")
    print(" Runtime environment ".center(80, HORIZONTAL_LINE))
    print("* GDB: {}".format(gdb.VERSION))
    print("* Python: {:d}.{:d}.{:d} - {:s}".format(sys.version_info.major, sys.version_info.minor,
                                                   sys.version_info.micro, sys.version_info.releaselevel))
    print("* OS: {:s} - {:s} ({:s}) on {:s}".format(platform.system(), platform.release(),
                                                    platform.architecture()[0],
                                                    " ".join(platform.dist())))
    print(horizontal_line * 80)
    print("")
    exit(-6000)


def build_pretty_printer():
    pp = gdb.printing.RegexpCollectionPrettyPrinter("nlohmann_json")
    pp.add_printer(nlohmann_json_type_namespace, "^{}$".format(nlohmann_json_type_namespace), LohmannJSONPrinter)
    return pp

# executed at autoload gdb.printing.register_pretty_printer(gdb.current_objfile(),build_pretty_printer())
