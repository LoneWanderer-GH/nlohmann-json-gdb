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

SEARCH_MIN = 2
SEARCH_MAX = 512
SEARCH_STEP = 2
SEARCH_RANGE = range(SEARCH_MIN, SEARCH_MAX, SEARCH_STEP)

print("")
print("Search range will be:")
print("MIN: {} - MAX: {} - STEP: {}".format(SEARCH_MIN,SEARCH_MAX, SEARCH_STEP))
print("")

""""""
# GDB black magic
""""""
NLOHMANN_JSON_TYPE_PREFIX = "nlohmann::basic_json"

class NO_TYPE_ERROR(Exception):
    pass


class NO_ENUM_TYPE_ERROR(Exception):
    pass


class NO_RB_TREE_TYPES_ERROR(Exception):
    pass


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
        print("Using regex: {}".format(regex))
        print("".center(80, "-"))
        print("")
        return t

    else:
        raise NO_TYPE_ERROR("Too many matching types found ...\n{}".format("\n\t".join(lines)))

def find_platform_std_string_type():
    std_str_regex = "^std::__cxx.*::basic_string<char,.*>$" # platform/compilation dependant ?
    t = find_platform_type(std_str_regex, "std::string")
    return gdb.lookup_type(t)


def find_platform_json_type(nlohmann_json_type_prefix):
    """
    Executes GDB commands to find the correct JSON type in a platform independant way.
    Not debug symbols => no cigar
    """
    # takes a regex and returns a multiline string
    regex = "^{}<.*>$".format(nlohmann_json_type_prefix)
    return find_platform_type(regex, nlohmann_json_type_prefix)


def find_lohmann_types():
    nlohmann_json_type_namespace = find_platform_json_type(NLOHMANN_JSON_TYPE_PREFIX)
    try:
        NLOHMANN_JSON_TYPE = gdb.lookup_type(nlohmann_json_type_namespace).pointer()
    except:
        raise NO_TYPE_ERROR("Type namespace found but could not obtain type data ... WEIRD !")
    try:
        enum_json_detail = gdb.lookup_type("nlohmann::detail::value_t").fields()
    except:
        raise NO_ENUM_TYPE_ERROR()
    return nlohmann_json_type_namespace, NLOHMANN_JSON_TYPE, enum_json_detail

def get_fields_offset_from_type(str_type):
    gdb_type = gdb.lookup_type(str_type)
    s = gdb.execute("ptype /o {}".format(gdb_type), to_string=True)
    lines = s.splitlines()
    field_names = [f.name for f in gdb_type.fields()]
    fields_offsets = dict()

    # structure to read
    # /* offset    |  size */  type = struct std::_Rb_tree_node_base {
    # /*    0      |     4 */    std::_Rb_tree_color _M_color;
    # /* XXX  4-byte hole */
    # /*    8      |     8 */    _Base_ptr _M_parent;
    # /*   16      |     8 */    _Base_ptr _M_left;
    # /*   24      |     8 */    _Base_ptr _M_right;
    # /**/
    #                            /* total size (bytes):   32 */
    #                          }
    matcher = re.compile("\/\*\s+(\d+).*")
    for l in lines:
        for field in field_names:
            if field in l:
                match = matcher.match(l)# re.split("\|", l)[0].
                field_offset = int(match.group(1))
                fields_offsets[field] = field_offset
                # print("Found offset {:02d} for {}".format(field_offset, field))
                break # break the loop over fields names, go next line
            else:
                continue
    return fields_offsets

def find_rb_tree_types():
    try:
        std_rb_header_offsets = get_fields_offset_from_type("std::_Rb_tree_node_base")
        std_rb_tree_node_type = gdb.lookup_type("std::_Rb_tree_node_base::_Base_ptr").pointer()
        std_rb_tree_size_type = gdb.lookup_type("std::size_t").pointer()
        return std_rb_tree_node_type, std_rb_tree_size_type, std_rb_header_offsets
    except:
        raise NO_RB_TREE_TYPES_ERROR()

## SET GLOBAL VARIABLES
try:
    STD_STRING = find_platform_std_string_type()
    NLOHMANN_JSON_TYPE_NAMESPACE, NLOHMANN_JSON_TYPE, ENUM_JSON_DETAIL = find_lohmann_types()
    STD_RB_TREE_NODE_TYPE, STD_RB_TREE_SIZE_TYPE, STD_RB_HEADER_OFFSETS = find_rb_tree_types()
except NO_TYPE_ERROR:
    print("FATAL ERROR {}".format(ERROR_NO_CORRECT_JSON_TYPE_FOUND))
    print("FATAL ERROR {}".format(ERROR_NO_CORRECT_JSON_TYPE_FOUND))
    print("FATAL ERROR {}: missing JSON type definition, could not find the JSON type starting with {}".format(NLOHMANN_JSON_TYPE_PREFIX))
    gdb.execute("q {}".format(ERROR_NO_CORRECT_JSON_TYPE_FOUND))
except NO_RB_TREE_TYPES_ERROR:
    print("FATAL ERROR {}".format(ERROR_NO_RB_TYPES_FOUND))
    print("FATAL ERROR {}".format(ERROR_NO_RB_TYPES_FOUND))
    print("FATAL ERROR {}: missing some STL RB tree types definition")
    gdb.execute("q {}".format(ERROR_NO_RB_TYPES_FOUND))


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

        node      = o["_M_t"]["_M_impl"]["_M_header"]["_M_left"]
        tree_size = o["_M_t"]["_M_impl"]["_M_node_count"]

        size_of_node = o["_M_t"]["_M_impl"]["_M_header"]["_M_left"].referenced_value().type.sizeof

        i = 0

        if tree_size == 0:
            return "{}"
        else:
            key_found = False
            for offset_key in SEARCH_RANGE:
                try:
                    print("Testing Node.Key offset {}".format(offset_key))
                    key_address = std_stl_item_to_int_address(node) + offset_key
                    k_str = parse_std_str_from_hexa_address(hex(key_address))
                    if key in k_str:
                        key_found = True
                        print("Found the key '{}'".format(k_str))
                        break
                except:
                    continue
            if not key_found:
                return "No offset found for STD::MAP key (starting from RB node address)"

            value_found = False
            for offset_val in SEARCH_RANGE:
                try:
                    print("Testing Node.Value offset {}".format(offset_val))
                    value_address = key_address + offset_val
                    value_object = gdb.Value(long(value_address)).cast(NLOHMANN_JSON_TYPE)
                    v_str = LohmannJSONPrinter(value_object, self.indent_level + 1).to_string()
                    if value in v_str:
                        print("Found the value '{}'".format(v_str))
                        value_found = True
                        break
                except:
                    continue
            if not value_found:
                return "No offset found for STD::MAP value (starting from RB key address)"
            if key_found and value_found:
                print("\n\nOffsets for STD::MAP <key,val> exploration from a given node are:\n")
                print("MAGIC_OFFSET_STD_MAP_KEY        = {} (expected value from symbols {})".format(offset_key, size_of_node))
                print("MAGIC_OFFSET_STD_MAP_VAL        = {} (expected value from symbols {})".format(offset_val, STD_STRING.sizeof))
                return "\n ===> Offsets for STD::MAP : [ FOUND ] <=== "
        print("MAGIC_OFFSET_STD_MAP_KEY should be {} (from symbols)".format(offset_key, size_of_node))
        print("MAGIC_OFFSET_STD_MAP_VAL should be {} (from symbols)".format(offset_val, STD_STRING.sizeof))
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
        start_address = std_stl_item_to_int_address(start)
        if size == 0:
            return "error with  std::vector"
        else:
            for offset in SEARCH_RANGE:
                try:
                    print("Testing vector value offset {}".format(offset))
                    o = (i * offset)
                    i_address = start_address + o
                    value_object = gdb.Value(long(i_address)).cast(NLOHMANN_JSON_TYPE)
                    v_str = LohmannJSONPrinter(value_object, self.indent_level + 1).to_string()
                    print("value: {}".format(v_str))
                    if expected_value in v_str: # or "9966990055" in v_str:
                        print("\n\nOffsets for STD::VECTOR exploration are:\n")
                        print("MAGIC_OFFSET_STD_VECTOR                           = {}".format(offset))
                        print('OFFSET should be size of o["_M_impl"]["_M_start"] = {}'.format(element_size))
                        return "\n ===> Offsets for STD::VECTOR : [ FOUND ] <=== "
                except:
                    continue
        print('MAGIC_OFFSET_STD_VECTOR should be = {} (from symbols)'.format(element_size))
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
