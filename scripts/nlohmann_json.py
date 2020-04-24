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

# https://stackoverflow.com/questions/29285287/c-getting-size-in-bits-of-integer
PLATFORM_BITS = "64" if sys.maxsize > 2 ** 32 else "32"

print("PLATFORM_BITS {}".format(PLATFORM_BITS))


""""""
# GDB black magic
""""""
NLOHMANN_JSON_TYPE_PREFIX = "nlohmann::basic_json"
NLOHMANN_JSON_KIND_FIELD_NAME = "m_type"
STD_RB_TREE_NODE_TYPE_NAME = "std::_Rb_tree_node_base"


class NO_RB_TREE_TYPES_ERROR(Exception):
    pass


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




def find_platform_type(regex, helper_type_name):
    # we suppose its a unique match, 4 lines output
    info_types = gdb.execute("info types {}".format(regex), to_string=True)
    # make it multines
    lines = info_types.splitlines()
    # correct command should have given  lines, the last one being the correct one
    if len(lines) == 4:
         # split last line, after line number and spaces
        t = re.split("^\d+:\s+", lines[-1])
        # transform result
        t = "".join(t[1::]).split(";")[0]
        print("")
        print("The researched {} type for this executable is".format(helper_type_name).center(80, "-"))
        print("{}".format(t).center(80, "-"))
        print("(Using regex: {})".format(regex))
        print("".center(80, "-"))
        print("")
        return t

    else:
        raise ValueError("Too many matching types found fro JSON ...\n{}".format("\n\t".join(lines)))


def find_platform_json_type(nlohmann_json_type_prefix):
    """
    Executes GDB commands to find the correct JSON type in a platform independant way.
    Not debug symbols => no cigar
    """
    # takes a regex and returns a multiline string
    regex = "^{}<.*>$".format(nlohmann_json_type_prefix)
    return find_platform_type(regex, nlohmann_json_type_prefix)


def find_lohmann_types():
    """
    Finds essentials types to debug nlohmann JSONs
    """

    nlohmann_json_type_namespace = find_platform_json_type(NLOHMANN_JSON_TYPE_PREFIX)

    # enum type that represents what is eaxtcly the current json object
    nlohmann_json_type = gdb.lookup_type(nlohmann_json_type_namespace)

    # the real type behind "std::string"
    # std::map is a C++ template, first template arg is the std::map key type
    nlohmann_json_map_key_type = nlohmann_json_type.template_argument(0)

    enum_json_detail_type = None
    for field in nlohmann_json_type.fields():
        if NLOHMANN_JSON_KIND_FIELD_NAME == field.name:
            enum_json_detail_type = field.type
            break;

    enum_json_details = enum_json_detail_type.fields()

    return nlohmann_json_type_namespace, nlohmann_json_type.pointer(), enum_json_details, nlohmann_json_map_key_type


def find_std_map_rb_tree_types():
    try:
        std_rb_tree_node_type = gdb.lookup_type(STD_RB_TREE_NODE_TYPE_NAME)
        return std_rb_tree_node_type
    except:
        raise ValueError("Could not find the required RB tree types")

## SET GLOBAL VARIABLES
try:
    NLOHMANN_JSON_TYPE_NAMESPACE, NLOHMANN_JSON_TYPE_POINTER, ENUM_JSON_DETAIL, NLOHMANN_JSON_MAP_KEY_TYPE = find_lohmann_types()
    STD_RB_TREE_NODE_TYPE = find_std_map_rb_tree_types()
except:
    show_last_exception()


# convert the full namespace to only its litteral value
# useful to access the corect variant of JSON m_value
ENUM_LITERAL_NAMESPACE_TO_LITERAL = dict([ (f.name, f.name.split("::")[-1]) for f in ENUM_JSON_DETAIL])



def gdb_value_address_to_int(node):
    val = None
    if type(node) == gdb.Value:
        # gives the int value of the address
        # .address returns another gdb.Value that cannot be cast to int
        val = int(str(node), 0)
    return val


def parse_std_string_from_hexa_address(hexa_str):
    # https://stackoverflow.com/questions/6776961/how-to-inspect-stdstring-in-gdb-with-no-source-code
    return '"{}"'.format(gdb.parse_and_eval("*(char**){}".format(hexa_str)).string())


class LohmannJSONPrinter(object):
    """Print a nlohmann::json in GDB python
    BEWARE :
     - Contains shitty string formatting (defining lists and playing with ",".join(...) could be better; ident management is stoneage style)
     - NO LIB VERSION MANAGEMENT.
            TODO: determine if there are serious variants in nlohmann data structures that would justify working with strucutres
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

        node      = o["_M_t"]["_M_impl"]["_M_header"]["_M_left"]
        tree_size = o["_M_t"]["_M_impl"]["_M_node_count"]

        # for safety
        # assert(node.referenced_value().type        == STD_RB_TREE_NODE_TYPE)
        # assert(node.referenced_value().type.sizeof == STD_RB_TREE_NODE_TYPE.sizeof)

        i = 0
        if tree_size == 0:
            return "{}"
        else:
            s = "{\n"
            self.indent_level += 1
            while i < tree_size:
                # when it is written "+1" in the STL GDB script, it performs an increment of 1 x size of object
                # key is right after
                key_address = gdb_value_address_to_int(node) + STD_RB_TREE_NODE_TYPE.sizeof

                k_str = parse_std_string_from_hexa_address(key_address)

                value_address = key_address + NLOHMANN_JSON_MAP_KEY_TYPE.sizeof
                value_object = gdb.Value(value_address).cast(NLOHMANN_JSON_TYPE_POINTER)

                v_str = LohmannJSONPrinter(value_object, self.indent_level + 1).to_string()

                k_v_str = "{} : {}".format(k_str, v_str)
                end_of_line = "\n" if tree_size <= 1 or i == (tree_size - 1) else ",\n"

                s = s + (" " * (self.indent_level * INDENT)) + k_v_str + end_of_line

                if gdb_value_address_to_int(node["_M_right"]) != 0:
                    node = node["_M_right"]
                    while gdb_value_address_to_int(node["_M_left"]) != 0:
                        node = node["_M_left"]
                else:
                    tmp_node = node["_M_parent"]
                    while gdb_value_address_to_int(node) == gdb_value_address_to_int(tmp_node["_M_right"]):
                        node = tmp_node
                        tmp_node = tmp_node["_M_parent"]

                    if gdb_value_address_to_int(node["_M_right"]) != gdb_value_address_to_int(tmp_node):
                        node = tmp_node
                i += 1
            self.indent_level -= 2
            s = s + (" " * (self.indent_level * INDENT)) + "}"
            return s

    def parse_as_str(self):
        return parse_std_string_from_hexa_address(str(self.val["m_value"][self.field_type_short]))

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
        # when it is written "+1" in the STL GDB script, it performs an increment of 1 x size of object
        element_size = start.referenced_value().type.sizeof
        start_address = gdb_value_address_to_int(start)
        if size == 0:
            s = "[]"
        else:
            self.indent_level += 1
            s = "[\n"
            while i < size:
                offset = i * element_size
                i_address = start_address + offset
                value_object = gdb.Value(i_address).cast(NLOHMANN_JSON_TYPE_POINTER)
                v_str = LohmannJSONPrinter(value_object, self.indent_level + 1).to_string()
                end_of_line = "\n" if size <= 1 or i == (size -1) else ",\n"
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
        if self.is_leaf():
            s = self.parse_as_leaf()
        else:
            s = self.parse_as_aggregate()
        return s

    def to_string(self):
        try:
            self.field_type_full_namespace = self.val[NLOHMANN_JSON_KIND_FIELD_NAME]
            str_val = str(self.field_type_full_namespace)
            if not str_val in ENUM_LITERAL_NAMESPACE_TO_LITERAL:
                raise ValueError("Unkown litteral for data type enum. Found {}\nNot in:\n{}".format(str_val,
                                                                                                    "\n\t".join(
                                                                                                        ENUM_LITERAL_NAMESPACE_TO_LITERAL)))
            self.field_type_short = ENUM_LITERAL_NAMESPACE_TO_LITERAL[str_val]
            return self.function_map[str_val]()
            # return self.parse()
        except:
            show_last_exception()
            return "NOT A JSON OBJECT // CORRUPTED ?"

    def display_hint(self):
        return self.val.type


def build_pretty_printer():
    pp = gdb.printing.RegexpCollectionPrettyPrinter("nlohmann_json")
    pp.add_printer(NLOHMANN_JSON_TYPE_NAMESPACE, "^{}$".format(NLOHMANN_JSON_TYPE_POINTER), LohmannJSONPrinter)
    return pp


# executed at autoload
gdb.printing.register_pretty_printer(gdb.current_objfile(), build_pretty_printer())
