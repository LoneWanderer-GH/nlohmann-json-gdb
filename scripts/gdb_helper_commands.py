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
import gdb


# def get_fields_offset_from_type(str_type):
#     gdb_type = gdb.lookup_type(str_type)
#     s = gdb.execute("ptype /o {}".format(gdb_type), to_string=True)
#     lines = s.splitlines()
#     field_names = [f.name for f in gdb_type.fields()]
#     fields_offsets = dict()

#     # structure to read
#     # /* offset    |  size */  type = struct std::_Rb_tree_node_base {
#     # /*    0      |     4 */    std::_Rb_tree_color _M_color;
#     # /* XXX  4-byte hole */
#     # /*    8      |     8 */    _Base_ptr _M_parent;
#     # /*   16      |     8 */    _Base_ptr _M_left;
#     # /*   24      |     8 */    _Base_ptr _M_right;
#     # /**/
#     #                            /* total size (bytes):   32 */
#     #                          }
#     matcher = re.compile("\/\*\s+(\d+).*")
#     for l in lines:
#         for field in field_names:
#             if field in l:
#                 match = matcher.match(l)# re.split("\|", l)[0].
#                 field_offset = int(match.group(1))
#                 fields_offsets[field] = field_offset
#                 # print("Found offset {:02d} for {}".format(field_offset, field))
#                 break # break the loop over fields names, go next line
#             else:
#                 continue
#     return fields_offsets

class List_Types_To_File(gdb.Command):
    command_name_str = "list-types-to-file"
    command_expected_args_nb = 1
    def __init__(self):
        super(List_Types, self).__init__(List_Types.command_name_str, gdb.COMMAND_DATA)

    def invoke(self, arg, from_tty):

        argv = gdb.string_to_argv(arg)
        nb_args = len(argv)
        if nb_args != List_Types.command_expected_args_nb:
            raise gdb.GdbError("{} takes exactly {} argument".format(List_Types.command_name_str, List_Types.command_expected_args_nb))
        with open(arg, "w") as f:
            infos_ = gdb.execute("info types", to_string=True)
            f.write(infos_)

List_Types()
