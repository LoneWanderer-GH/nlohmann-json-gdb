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

# heavily inspired from https://stackoverflow.com/questions/9788679/how-to-get-the-relative-address-of-a-field-in-a-structure-dump-c
# but with some significant additions

gdb_type_code_dict = {
    gdb.TYPE_CODE_PTR:"gdb.TYPE_CODE_PTR = The type is a pointer.",
    gdb.TYPE_CODE_ARRAY:"gdb.TYPE_CODE_ARRAY = The type is an array.",
    gdb.TYPE_CODE_STRUCT:"gdb.TYPE_CODE_STRUCT = The type is a structure.",
    gdb.TYPE_CODE_UNION:"gdb.TYPE_CODE_UNION = The type is a union.",
    gdb.TYPE_CODE_ENUM:"gdb.TYPE_CODE_ENUM = The type is an enum.",
    gdb.TYPE_CODE_FLAGS:"gdb.TYPE_CODE_FLAGS = A bit flags type, used for things such as status registers.",
    gdb.TYPE_CODE_FUNC:"gdb.TYPE_CODE_FUNC = The type is a function.",
    gdb.TYPE_CODE_INT:"gdb.TYPE_CODE_INT = The type is an integer type.",
    gdb.TYPE_CODE_FLT:"gdb.TYPE_CODE_FLT = A floating point type.",
    gdb.TYPE_CODE_VOID:"gdb.TYPE_CODE_VOID = The special type void.",
    gdb.TYPE_CODE_SET:"gdb.TYPE_CODE_SET = A Pascal set type.",
    gdb.TYPE_CODE_RANGE:"gdb.TYPE_CODE_RANGE = A range type, that is, an integer type with bounds.",
    gdb.TYPE_CODE_STRING:"gdb.TYPE_CODE_STRING = A string type. Note that this is only used for certain languages with language-defined string types; C strings are not represented this way.",
    gdb.TYPE_CODE_BITSTRING:"gdb.TYPE_CODE_BITSTRING = A string of bits. It is deprecated.",
    gdb.TYPE_CODE_ERROR:"gdb.TYPE_CODE_ERROR = An unknown or erroneous type.",
    gdb.TYPE_CODE_METHOD:"gdb.TYPE_CODE_METHOD = A method type, as found in C++.",
    gdb.TYPE_CODE_METHODPTR:"gdb.TYPE_CODE_METHODPTR = A pointer-to-member-function.",
    gdb.TYPE_CODE_MEMBERPTR:"gdb.TYPE_CODE_MEMBERPTR = A pointer-to-member.",
    gdb.TYPE_CODE_REF:"gdb.TYPE_CODE_REF = A reference type.",
    gdb.TYPE_CODE_RVALUE_REF:"gdb.TYPE_CODE_RVALUE_REF = A C++11 rvalue reference type.",
    gdb.TYPE_CODE_CHAR:"gdb.TYPE_CODE_CHAR = A character type.",
    gdb.TYPE_CODE_BOOL:"gdb.TYPE_CODE_BOOL = A boolean type.",
    gdb.TYPE_CODE_COMPLEX:"gdb.TYPE_CODE_COMPLEX = A complex float type.",
    gdb.TYPE_CODE_TYPEDEF:"gdb.TYPE_CODE_TYPEDEF = A typedef to some other type.",
    gdb.TYPE_CODE_NAMESPACE:"gdb.TYPE_CODE_NAMESPACE = A C++ namespace.",
    gdb.TYPE_CODE_DECFLOAT:"gdb.TYPE_CODE_DECFLOAT = A decimal floating point type.",
    gdb.TYPE_CODE_INTERNAL_FUNCTION:"gdb.TYPE_CODE_INTERNAL_FUNCTION = A function internal to GDB. This is the type used to represent convenience functions."
}

class Offsets(gdb.Command):
    def __init__(self):
        super (Offsets, self).__init__ ('offsets-of', gdb.COMMAND_DATA)

    def invoke(self, arg, from_tty):
        argv = gdb.string_to_argv(arg)
        if len(argv) != 1:
            raise gdb.GdbError('offsets-of takes exactly 1 argument.')
        
        t = argv[0]
        stype = gdb.execute("whatis {}".format(t), to_string=True)
        
        # print("{} is {}".format(t, stype))
        
        stype = stype.split("=")[-1].strip()
        
        gdb_type = gdb.lookup_type(stype)
        
        
        if gdb_type.code in [gdb.TYPE_CODE_PTR, gdb.TYPE_CODE_REF, gdb.TYPE_CODE_RVALUE_REF]:
            print("Type is a pointer, get referenced value type")
            gdb_type = gdb_type.referenced_value().type
        
        if not gdb_type.code in [gdb.TYPE_CODE_STRUCT, gdb.TYPE_CODE_UNION]:
            print("{} is not a structure with fields ...")
            print("{}".format(gdb_type_code_dict[gdb_type.code]))
            return
        lines = "\n".join(["\t{:<20.20} => {:5d}".format(field.name, field.bitpos//8) for field in gdb_type.fields()])
        # print(lines)
        print ("{0} (of type {1})\n{2}".format(t, gdb_type, lines))
        
Offsets()