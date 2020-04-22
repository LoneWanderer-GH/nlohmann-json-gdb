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
# I'm not a layer and I like to give people credit.
# I was inspired or I adapted some code pieces her and the the source links are
# given in comments.

import sys

import gdb
import platform
import traceback

# adapted from https://github.com/hugsy/gef/blob/dev/gef.py
# their rights are theirs
HORIZONTAL_LINE = "_"  # u"\u2500"
LEFT_ARROW = "<-"  # "\u2190 "
RIGHT_ARROW = "->"  # " \u2192 "
DOWN_ARROW = "|"  # "\u21b3"

INDENT = 4

PLATFORM_BITS = "64" if sys.maxsize > 2 ** 32 else "32"

print("PLATFORM_BITS {}".format(PLATFORM_BITS))

# the strings were obtained with gdb
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

# STD offsets black magic
# 64 obtained from win x64
# 32 obtained from raspberry pi arm32
# other platforms ? find them yourself ^^
MAGIC_OFFSET_STD_VECTOR = None
MAGIC_OFFSET_STD_MAP_KEY = None
MAGIC_OFFSET_STD_MAP_VAL = None
MAGIC_OFFSET_STD_MAP_NODE_COUNT = None
MAGIC_OFFSET_STD_MAP = None

""""""
# GDB black magic
""""""
nlohmann_json_type = gdb.lookup_type(nlohmann_json_type_namespace).pointer()
std_rb_tree_node_type = gdb.lookup_type("std::_Rb_tree_node_base::_Base_ptr").pointer()
std_rb_tree_size_type = gdb.lookup_type("std::size_t").pointer()

""""""
# from c++ source code
# enum class value_t : std::uint8_t
# {
#  ...
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


def std_stl_item_to_int_address(node):
    return int(str(node), 0)


def parse_std_str_from_hexa_address(hexa_str):
    # https://stackoverflow.com/questions/6776961/how-to-inspect-stdstring-in-gdb-with-no-source-code
    return '"{}"'.format(gdb.parse_and_eval("*(char**){}".format(hexa_str)).string())


class LohmannJSONPrinter(object):
    """Print a nlohmann::json in GDB python
    BEWARE :
     - Contains shitty string formatting (defining lists and playing with ",".join(...) could be better; ident management is stoneage style)
     - NO LIB VERSION MANAGEMENT.
            TODO: determine if there are serious variants in nlohmann data structures that would justify working with strucutres
     - PLATFORM DEPENDANT
            TODO: handle magic offsets in a nicer way (get the exact types sizes with some gdb commands ?)
    NB: If you are python-kaizer-style-guru, please consider helping or teaching how to improve all that mess
    """

    def __init__(self, val, indent_level=0):
        self.val = val
        self.field_type_full_namespace = None
        self.field_type_short = None
        self.indent_level = indent_level

        self.function_map = {"nlohmann::detail::value_t::null": self.parse_as_leaf,
                             "nlohmann::detail::value_t::object": self.parse_as_object,
                             "nlohmann::detail::value_t::array": self.parse_as_array,
                             "nlohmann::detail::value_t::string": self.parse_as_str,
                             "nlohmann::detail::value_t::boolean": self.parse_as_leaf,
                             "nlohmann::detail::value_t::number_integer": self.parse_as_leaf,
                             "nlohmann::detail::value_t::number_unsigned": self.parse_as_leaf,
                             "nlohmann::detail::value_t::number_float": self.parse_as_leaf,
                             "nlohmann::detail::value_t::discarded": self.parse_as_leaf}

    def parse_as_object(self):
        assert (self.field_type_short == "object")

        o = self.val["m_value"][self.field_type_short]

        # traversing tree is a an adapted copy pasta from STL gdb parser
        # (http://www.yolinux.com/TUTORIALS/src/dbinit_stl_views-1.03.txt and similar links)
        first_node_offset = -1
        node_count_offset = -1
        offset_key = -1
        offset_val = -1
        for first_node_offset in range(1,96,1):
            try:
                tree_size = None
                node = None
                _M_t = std_stl_item_to_int_address(o.referenced_value().address)
                _M_t_M_impl_M_header_M_left = _M_t + first_node_offset
                for node_count_offset in range(1,96,1):
                    try:
                        _M_t_M_impl_M_node_count    = _M_t + first_node_offset + node_count_offset
                        node = gdb.Value(long(_M_t_M_impl_M_header_M_left)).cast(std_rb_tree_node_type).referenced_value()
                        tree_size = gdb.Value(long(_M_t_M_impl_M_node_count)).cast(std_rb_tree_size_type).referenced_value()

                        if tree_size != 1:
                            continue
                        else:
                            # print("Correct tree size (=1)")
                            # print("Testing _M_Impl._M_header._M_left offset {}".format(first_node_offset))
                            # print("Testing _M_Impl._M_node_count offset {}".format(node_count_offset))
                            key_found = False

                            for offset_key in range(1,96,1):
                                try:
                                    # print("Testing Node.Key {}".format(offset_key))
                                    key_address = std_stl_item_to_int_address(node) + offset_key
                                    k_str = parse_std_str_from_hexa_address(hex(key_address))
                                    if "first" in k_str:
                                        key_found = True
                                        print("Found the key '{}'".format(k_str))
                                        break
                                except:
                                    continue
                            if not key_found:
                                continue

                            value_found = False
                            for offset_val in range(1,96,1):
                                try:
                                    # print("Testing Node.Value {}".format(offset_val))
                                    value_address = key_address + offset_val
                                    value_object = gdb.Value(long(value_address)).cast(nlohmann_json_type)
                                    v_str = LohmannJSONPrinter(value_object, self.indent_level + 1).to_string()
                                    if "second" in v_str:
                                        print("Found the value '{}'".format(v_str))
                                        value_found = True
                                        break
                                except:
                                    continue
                            if not value_found:
                                continue
                            if key_found and value_found:
                                print("\n\nOffsets for STD::MAP exploration are:\n")
                                print("MAGIC_OFFSET_STD_MAP            = {}".format(first_node_offset))
                                print("MAGIC_OFFSET_STD_MAP_NODE_COUNT = {}".format(node_count_offset))
                                print("MAGIC_OFFSET_STD_MAP_KEY        = {}".format(offset_key))
                                print("MAGIC_OFFSET_STD_MAP_VAL        = {}".format(offset_val))
                                return "\n ===> Offsets for STD::MAP : [ FOUND ] <=== "
                    except:
                        continue
            except:
                continue
            # print("Offsets for STD::MAP exploration incomplete with these values:")
            # print("MAGIC_OFFSET_STD_MAP            = {}".format(first_node_offset))
            # print("MAGIC_OFFSET_STD_MAP_NODE_COUNT = {}".format(node_count_offset))
            # print("MAGIC_OFFSET_STD_MAP_KEY        = {}".format(offset_key))
            # print("MAGIC_OFFSET_STD_MAP_VAL        = {}".format(offset_val))
        return "\n ===> Offsets for STD::MAP : [ NOT FOUND ] <=== "


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
            pass
        else:
            for offset in range(1,128,1):
                try:
                    i_address = start_address + offset
                    value_object = gdb.Value(long(i_address)).cast(nlohmann_json_type)
                    v_str = LohmannJSONPrinter(value_object, self.indent_level + 1).to_string()
                    if "25" in v_str:
                        print("\n\nOffsets for STD::VECTOR exploration are:\n")
                        print("MAGIC_OFFSET_STD_VECTOR = {}".format(offset))
                        return "\n ===> Offsets for STD::VECTOR : [ FOUND ] <=== "
                except:
                    continue
        return " ===> Offsets for STD::VECTOR : [ NOT FOUND ] <=== "

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
                return "invalid"
                # raise ValueError("Unkown litteral for data type enum. Found {}\nNot in:\n{}".format(str_val,
                #                                                                                     "\n\t".join(
                #                                                                                         enum_literal_namespace_to_literal)))
            self.field_type_short = enum_literal_namespace_to_literal[str_val]
            return self.function_map[str_val]()
            # return self.parse()
        except:
            # show_last_exception()
            return "invalid"

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
    print(HORIZONTAL_LINE * 80)
    print("")
    exit(-6000)


def build_pretty_printer():
    pp = gdb.printing.RegexpCollectionPrettyPrinter("nlohmann_json")
    pp.add_printer(nlohmann_json_type_namespace, "^{}$".format(nlohmann_json_type_namespace), LohmannJSONPrinter)
    return pp


# executed at script load by GDB
gdb.printing.register_pretty_printer(gdb.current_objfile(), build_pretty_printer())
