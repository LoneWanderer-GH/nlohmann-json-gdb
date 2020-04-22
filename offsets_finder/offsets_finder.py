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
import re
import gdb
import platform
import traceback

ERROR_NO_CORRECT_JSON_TYPE_FOUND = 1
ERROR_NO_RB_TYPES_FOUND = 2
ERROR_PARSING_ERROR = 42

# adapted from https://github.com/hugsy/gef/blob/dev/gef.py
# their rights are theirs
HORIZONTAL_LINE = "_"  # u"\u2500"
LEFT_ARROW = "<-"  # "\u2190 "
RIGHT_ARROW = "->"  # " \u2192 "
DOWN_ARROW = "|"  # "\u21b3"

INDENT = 4

PLATFORM_BITS = "64" if sys.maxsize > 2 ** 32 else "32"

print("PLATFORM_BITS {}".format(PLATFORM_BITS))


""""""
# GDB black magic
""""""
NLOHMANN_JSON_TYPE_PREFIX = "nlohmann::basic_json"

class NO_JSON_TYPE_ERROR(Exception):
    pass


class NO_ENUM_TYPE_ERROR(Exception):
    pass


class NO_RB_TREE_TYPES_ERROR(Exception):
    pass


def find_platform_json_type(nlohmann_json_type_prefix):
    """
    Executes GDB commands to find the correct JSON type in a platform independant way.
    Not debug symbols => no cigar
    """
    # takes a regex and returns a multiline string
    info_types = gdb.execute("info types ^{}<.*>$".format(nlohmann_json_type_prefix), to_string=True)
    # make it multines
    lines = info_types.splitlines()
    # correct command should have given  lines, the last one being the correct one
    if len(lines) == 4:
         # split last line, after line number and spaces
        t = re.split("^\d+:\s+", lines[-1])
        # transform result
        t = "".join(t[1::]).split(";")[0]
        print("")
        print("The JSON type for this executable is".center(80, "-"))
        print("{}".format(t).center(80, "-"))
        print("".center(80, "-"))
        print("")
        return t

    else:
        raise NO_JSON_TYPE_ERROR("Too many matching types found ...\n{}".format("\n\t".join(lines)))

def find_lohmann_types():
    nlohmann_json_type_namespace = find_platform_json_type(NLOHMANN_JSON_TYPE_PREFIX)
    try:
        NLOHMANN_JSON_TYPE = gdb.lookup_type(nlohmann_json_type_namespace).pointer()
    except:
        raise NO_JSON_TYPE_ERROR("Type namesapce found but could not obtain type data ... WEIRD !")
    try:
        enum_json_detail = gdb.lookup_type("nlohmann::detail::value_t").fields()
    except:
        raise NO_ENUM_TYPE_ERROR()
    return nlohmann_json_type_namespace, NLOHMANN_JSON_TYPE, enum_json_detail

def find_rb_tree_types():
    try:
        std_rb_tree_node_type = gdb.lookup_type("std::_Rb_tree_node_base::_Base_ptr").pointer()
        std_rb_tree_size_type = gdb.lookup_type("std::size_t").pointer()
        return std_rb_tree_node_type, std_rb_tree_size_type
    except:
        raise NO_RB_TREE_TYPES_ERROR()

## SET GLOBAL VARIABLES
try:
    NLOHMANN_JSON_TYPE_NAMESPACE, NLOHMANN_JSON_TYPE, ENUM_JSON_DETAIL = find_lohmann_types()
    STD_RB_TREE_NODE_TYPE, STD_RB_TREE_SIZE_TYPE = find_rb_tree_types()
except NO_JSON_TYPE_ERROR:
    print("FATAL ERROR {}".format(ERROR_NO_CORRECT_JSON_TYPE_FOUND))
    print("FATAL ERROR {}".format(ERROR_NO_CORRECT_JSON_TYPE_FOUND))
    print("FATAL ERROR {}: missing JSON type definition, could not find the JSON type starting with {}".format(NLOHMANN_JSON_TYPE_PREFIX))
    gdb.execute_command("q {}".format(ERROR_NO_CORRECT_JSON_TYPE_FOUND))
except NO_RB_TREE_TYPES_ERROR:
    print("FATAL ERROR {}".format(ERROR_NO_RB_TYPES_FOUND))
    print("FATAL ERROR {}".format(ERROR_NO_RB_TYPES_FOUND))
    print("FATAL ERROR {}: missing some STL RB tree types definition")
    gdb.execute_command("q {}".format(ERROR_NO_RB_TYPES_FOUND))


ENUM_LITERAL_NAMESPACE_TO_LITERAL = dict([ (f.name, f.name.split("::")[-1]) for f in ENUM_JSON_DETAIL])
# ENUM_LITERALS_NAMESPACE = ENUM_LITERAL_NAMESPACE_TO_LITERAL.keys()

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
        for first_node_offset in range(1,256,1):
            try:
                tree_size = None
                node = None
                _M_t = std_stl_item_to_int_address(o.referenced_value().address)
                _M_t_M_impl_M_header_M_left = _M_t + first_node_offset
                for node_count_offset in range(1,256,1):
                    try:
                        _M_t_M_impl_M_node_count    = _M_t + first_node_offset + node_count_offset
                        node = gdb.Value(long(_M_t_M_impl_M_header_M_left)).cast(STD_RB_TREE_NODE_TYPE).referenced_value()
                        tree_size = gdb.Value(long(_M_t_M_impl_M_node_count)).cast(STD_RB_TREE_SIZE_TYPE).referenced_value()

                        if tree_size != 1:
                            continue
                        else:
                            # print("Correct tree size (=1)")
                            # print("Testing _M_Impl._M_header._M_left offset {}".format(first_node_offset))
                            # print("Testing _M_Impl._M_node_count offset {}".format(node_count_offset))
                            key_found = False

                            for offset_key in range(1,256,1):
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
                            for offset_val in range(1,256,1):
                                try:
                                    # print("Testing Node.Value {}".format(offset_val))
                                    value_address = key_address + offset_val
                                    value_object = gdb.Value(long(value_address)).cast(NLOHMANN_JSON_TYPE)
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
            for offset in range(1,256,1):
                try:
                    i_address = start_address + offset
                    value_object = gdb.Value(long(i_address)).cast(NLOHMANN_JSON_TYPE)
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
            if not str_val in ENUM_LITERAL_NAMESPACE_TO_LITERAL:
                return "invalid"
                # raise ValueError("Unkown litteral for data type enum. Found {}\nNot in:\n{}".format(str_val,
                #                                                                                     "\n\t".join(
                #                                                                                         ENUM_LITERAL_NAMESPACE_TO_LITERAL)))
            self.field_type_short = ENUM_LITERAL_NAMESPACE_TO_LITERAL[str_val]
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
    gdb.execute("q {}".format(ERROR_PARSING_ERROR))
    sys.exit(ERROR_PARSING_ERROR)


def build_pretty_printer():
    pp = gdb.printing.RegexpCollectionPrettyPrinter("nlohmann_json")
    pp.add_printer(NLOHMANN_JSON_TYPE_NAMESPACE, "^{}$".format(NLOHMANN_JSON_TYPE), LohmannJSONPrinter)
    return pp


# executed at script load by GDB
gdb.printing.register_pretty_printer(gdb.current_objfile(), build_pretty_printer())
