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

SEARCH_MIN = 2
SEARCH_MAX = 512
SEARCH_STEP = 2
SEARCH_RANGE = range(SEARCH_MIN, SEARCH_MAX, SEARCH_STEP)

print("")
print("Search range will be:")
print("MIN: {} - MAX: {} - STEP: {}".format(SEARCH_MIN, SEARCH_MAX, SEARCH_STEP))
print("")

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
        print("""{} File "{}", line {:d}, in {}()""".format(
            DOWN_ARROW, filename, lineno, method))
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
        for l in lines:
            print("### Log info types output : {}".format(l))
        l = lines[-1]
        if l.startswith(helper_type_name):
            # line format "type_name;"
            t = l.split(";")[0]
        else:
            # example
            # 14708:  nlohmann::basic_json<std::map, std::vector, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> >, bool, long long, unsigned long long, double, std::allocator, nlohmann::adl_serializer>;
            t = re.split("^\d+:\s+", lines[-1])
            # transform result
            t = "".join(t[1::]).split(";")[0]
        print("")
        print("The researched {} type for this executable is".format(
            helper_type_name).center(80, "-"))
        print("{}".format(t).center(80, "-"))
        print("(Using regex: {})".format(regex))
        print("".center(80, "-"))
        print("")
        return t

    else:
        raise ValueError(
            "Too many matching types found for JSON ...\n{}".format("\n\t".join(lines)))


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

    nlohmann_json_type_namespace = find_platform_json_type(
        NLOHMANN_JSON_TYPE_PREFIX)

    # enum type that represents what is eaxtcly the current json object
    nlohmann_json_type = gdb.lookup_type(nlohmann_json_type_namespace)

    # the real type behind "std::string"
    # std::map is a C++ template, first template arg is the std::map key type
    nlohmann_json_map_key_type = nlohmann_json_type.template_argument(0)

    enum_json_detail_type = None
    for field in nlohmann_json_type.fields():
        if NLOHMANN_JSON_KIND_FIELD_NAME == field.name:
            enum_json_detail_type = field.type
            break

    enum_json_details = enum_json_detail_type.fields()

    return nlohmann_json_type_namespace, nlohmann_json_type.pointer(), enum_json_details, nlohmann_json_map_key_type


def find_std_map_rb_tree_types():
    try:
        std_rb_tree_node_type = gdb.lookup_type(STD_RB_TREE_NODE_TYPE_NAME)
        return std_rb_tree_node_type
    except:
        raise ValueError("Could not find the required RB tree types")


# SET GLOBAL VARIABLES
try:
    NLOHMANN_JSON_TYPE_NAMESPACE, NLOHMANN_JSON_TYPE_POINTER, ENUM_JSON_DETAIL, NLOHMANN_JSON_MAP_KEY_TYPE = find_lohmann_types()
    STD_RB_TREE_NODE_TYPE = find_std_map_rb_tree_types()
except:
    show_last_exception()


# convert the full namespace to only its litteral value
# useful to access the corect variant of JSON m_value
ENUM_LITERAL_NAMESPACE_TO_LITERAL = dict(
    [(f.name, f.name.split("::")[-1]) for f in ENUM_JSON_DETAIL])


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
        key = "first"
        value = "second"
        print("Expected pair: <key:{}, value:{}>".format(key, value))
        o = self.val["m_value"][self.field_type_short]

        # traversing tree is a an adapted copy pasta from STL gdb parser
        # (http://www.yolinux.com/TUTORIALS/src/dbinit_stl_views-1.03.txt and similar links)

        node = o["_M_t"]["_M_impl"]["_M_header"]["_M_left"]
        tree_size = o["_M_t"]["_M_impl"]["_M_node_count"]

        # for safety
        # assert(node.referenced_value().type        == STD_RB_TREE_NODE_TYPE)
        # assert(node.referenced_value().type.sizeof == STD_RB_TREE_NODE_TYPE.sizeof)

        i = 0
        if tree_size == 0:
            return "{}"
        else:
            key_found = False
            for offset_key in SEARCH_RANGE:
                try:
                    print("Testing Node.Key offset {}".format(offset_key))
                    key_address = gdb_value_address_to_int(node) + offset_key # + 1
                    k_str = parse_std_string_from_hexa_address(hex(key_address))
                    if key in k_str:
                        key_found = True
                        print("Found the key '{}'".format(k_str))
                        break
                except:
                    continue
            if key_found:
                value_found = False
                for offset_val in SEARCH_RANGE:
                    try:
                        print("Testing Node.Value offset {}".format(offset_val))
                        value_address = key_address + offset_val
                        value_object = gdb.Value(value_address).cast(NLOHMANN_JSON_TYPE_POINTER)
                        v_str = LohmannJSONPrinter(value_object, self.indent_level + 1).to_string()
                        if value in v_str:
                            print("Found the value '{}'".format(v_str))
                            value_found = True
                            break
                    except:
                        continue
                if key_found and value_found:
                    if offset_key == STD_RB_TREE_NODE_TYPE.sizeof and offset_val == NLOHMANN_JSON_MAP_KEY_TYPE.sizeof:
                        print("\n\nOffsets for STD::MAP <key,val> exploration from a given node are:\n")
                        print("MAGIC_OFFSET_STD_MAP_KEY        = {} = expected value from symbols {}".format(offset_key, STD_RB_TREE_NODE_TYPE.sizeof))
                        print("MAGIC_OFFSET_STD_MAP_VAL        = {} = expected value from symbols {}".format(offset_val, NLOHMANN_JSON_MAP_KEY_TYPE.sizeof))
                        return "\n ===> Offsets for STD::MAP : [ FOUND ] <=== "
        print("MAGIC_OFFSET_STD_MAP_KEY should be {} (from symbols)".format(STD_RB_TREE_NODE_TYPE.sizeof))
        print("MAGIC_OFFSET_STD_MAP_VAL should be {} (from symbols)".format(STD_STRING.sizeof))
        print("\n ===> Offsets for STD::MAP : [ NOT FOUND ] <=== ")
        gdb.execute("q 25")


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
        expected_value ="996699FOO"
        expected_index = 2
        print("Trying to search array element {} at index ({})".format(expected_value, expected_index))
        o = self.val["m_value"][self.field_type_short]
        start = o["_M_impl"]["_M_start"]
        size = o["_M_impl"]["_M_finish"] - start
        # capacity = o["_M_impl"]["_M_end_of_storage"] - start
        # size_max = size - 1
        # test code has the interesting part at index 1 (2nd element)

        element_size = start.referenced_value().type.sizeof
        # start at expected index directly
        i = expected_index
        start_address = gdb_value_address_to_int(start)
        if size == 0:
            return "error with  std::vector"
        else:
            for offset in SEARCH_RANGE:
                try:
                    print("Testing vector value offset {}".format(offset))
                    o = (i * offset)
                    i_address = start_address + o
                    value_object = gdb.Value(i_address).cast(NLOHMANN_JSON_TYPE_POINTER)
                    v_str = LohmannJSONPrinter(value_object, self.indent_level + 1).to_string()
                    print("value: {}".format(v_str))
                    if expected_value in v_str: # or "9966990055" in v_str:
                        if offset == element_size:
                            print("\n\nOffsets for STD::VECTOR exploration are:\n")
                            print("MAGIC_OFFSET_STD_VECTOR = {}".format(offset))
                            print('OFFSET expected value   = {} (o["_M_impl"]["_M_start"], vector element size)'.format(element_size))
                            return "\n ===> Offsets for STD::VECTOR : [ FOUND ] <=== "
                except:
                    continue
        print('MAGIC_OFFSET_STD_VECTOR should be = {} (from symbols)'.format(element_size))
        print(" ===> Offsets for STD::VECTOR : [ NOT FOUND ] <=== ")
        gdb.execute("q 620")

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
        self.field_type_full_namespace = self.val[NLOHMANN_JSON_KIND_FIELD_NAME]
        str_val = str(self.field_type_full_namespace)
        if not str_val in ENUM_LITERAL_NAMESPACE_TO_LITERAL:
            # gdb.execute("q 100")
            return "Not a valid JSON type, continuing"
        self.field_type_short = ENUM_LITERAL_NAMESPACE_TO_LITERAL[str_val]
        return self.function_map[str_val]()


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
    pp.add_printer(NLOHMANN_JSON_TYPE_NAMESPACE, "^{}$".format(
        NLOHMANN_JSON_TYPE_POINTER), LohmannJSONPrinter)
    return pp


# executed at script load
gdb.printing.register_pretty_printer(
    gdb.current_objfile(), build_pretty_printer())
