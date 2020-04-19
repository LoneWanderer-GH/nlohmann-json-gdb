# A simplistic nlohmann-json-gdb pretty printer

Provides gdb script and python gdb script to pretty print a  nlohmann / json  (https://github.com/nlohmann/json)

**Table*
 
 1. [Prerequisites](#1-Prerequisites)
 2. [Installing](#2-Installing)
 3. [Content](#3-Content)
 4. [Usage](#4-Usage)
 5. [Possible improvements](#5-Possible-improvements)
 6. [Known limitations](#6-Known-limitations)
 7. [Examples / Tests](#7-Examples--Tests)  
 8. [History](#8-History)
 9. [Acknowledgments / LICENSES](#9-Acknowledgments--LICENSES)

# 1. Prerequisites

 - *GDB 8.3* debugger installed, ready to use. Some GDB commands knowledge might be useful for your debug session to be successful ;)
 -an executable to debug that uses the [JSON lib 3.7.3] (https://github.com/nlohmann/json).

## Optional
 - a [GNAT CE 2019][2] install to play with the provided sample test project


## Compatibility
 
 For the GDB command, tt should work with other GDB versions that support commands and printf.

For the GDB Python pretty printer, it should work with any GDB version that supports python (provided no gdb api change, otherwise python code will be broken). Be aware that the python code relies on some JSON lib types definition, so JSON lib and python pretty printer code should evolve together.

<details>
It is confirmed to be working on w10 x64 with:
 - https://github.com/nlohmann/json version 3.7.3
 - GNU gdb (GDB) 8.3 for GNAT Community 2019 [rev=gdb-8.3-ref-194-g3fc1095]
 - c++ project built with GPRBUILD/ GNAT Community 2019 (20190517) (x86_64-pc-mingw32)
</details>

# 2. Installing

Just copy the gdb and/or python script you need in a folder near your executable to debug.
See [Content](#Content) and [Usage](#Usage) sections below for more details.

# 3. Content

 - [x] a [sample c++ project](cpp_test_project). To be built using terminal command:
  `gprbuild -P debug_printer.gpr`. I used it on Windows 10 x64 with [GNAT CE 2019][2]
 - [x] the *[gdb command](gdb_script/simple_gdb_method.gdb)* : it uses the live process under debug to call `dump()`. It implies that the executable and memory are not corrupted, and variables not optimized out
 - [x] the *[python gdb pretty printer](gdb_python_pretty_printer)* : here, we do not rely on the existing dump() method but we explore memory to do it ourselves

 # 4. Usage
 ## How to load a GDB script

 in your gdb console:
 ```
 (gdb) source some_file
 ```

 ## GDB pretty printer usage (the Python printer)

 The GDB Pretty printer is [written in Python](gdb_python_pretty_printer/printer.py) which is loaded with a [gdb script](gdb_python_pretty_printer/load_pretty_printer.gdb)

 Then, a simple gdb command does the trick:

 ```
(gdb) p foo
{
    "flex" : 0.2,
    "awesome_str": "bleh",
    "nested": {
        "bar": "barz"
    }
}
```

 ## GDB script usage (the gdb command)

Here we use a kind of GDB macro defined in a [gdb script file](gdb_script/simple_gdb_method.gdb)

 ```
(gdb) pjson foo
{
    "flex" : 0.2,
    "awesome_str": "bleh",
    "nested": {
        "bar": "barz"
    }
}
```

## Remarks

Floating point numbers may appear differently depending on the method used. This is due to differences in floating-to-string from fdb and json c++.
For more confidence, we should modify the python pretty printer to provide the exact hexadecimal memory value + the decimal one.

# 5. Possible improvements
 - [ ] the python gdb pretty printer core dump management is not (yet ?) done (i.e. core dump means no inferior process to call dump() in any way, and possibly less/no (debug) symbols to rely on)
 - [ ] printer can be customised further to print the 0x addresses, I chose not to since the whole point for me was NOT to explore them in gdb. You would have to add few python `print` here and there

# 6. Known limitations

Not much.

 - Linux over windows exe build : `gprbuild` command on Ubuntu-windows/Debian-windows may not work correctly, so a legit Linux environment may be needed if you want to play with this on Linux.

 # 7. Examples / Tests

 see [main.cpp](cpp_test_project/src/main.cpp) for some basic C++ JSON declarations.

 example:
 ```// C++ code
json foo;
foo["flex"] = 0.2;
foo["bool"] = true;
foo["int"] = 5;
foo["float"] = 5.22;
foo["trap "] = "you fell";
foo["awesome_str"] = "bleh";
foo["nested"] = {{"bar", "barz"}};
foo["array"] = { 1, 0, 2 };
```

 gdb commands (once everything correctly loaded)

 ```(gdb) pjson foo
{
    "array": [
        1,
        0,
        2
    ],
    "awesome_str": "bleh",
    "bool": true,
    "flex": 0.2,
    "float": 5.22,
    "int": 5,
    "nested": {
        "bar": "barz"
    },
    "trap ": "you fell"
}
 ```

 gdb python pretty printer:

 ```
 (gdb) p foo
 {
    "array" : [
            1,
            0,
            2,
    ],
    "awesome_str" : "bleh",
    "bool" : true,
    "flex" : 0.20000000000000001,
    "float" : 5.2199999999999998,
    "int" : 5,
    "nested" : {
            "bar" : "barz"
    },
    "trap " : "you fell",
}
```


 ## Another approach I know of
 _from a guru of my workplace_
  - simply define a single function in the program to perform the dump of a json variable. This is almost exactly similar to the gdb inferior dump() call
  
# 8. History

 - In March 2019, I was stuck with the lack of nlohmann json debug utilities. I could not find any support to print what the json was during a debug session. I ended up with a stack overflow post with [what I found to be revelant][1] for that matter. In addition, I was interested in playing around with GDB/memory/python, thats why I took some time to treat this matter. I ended up with the code here.
 - In 2020 a Github issue was opened with the same intent here and relies basically on the same initial solution I used: https://github.com/nlohmann/json/issues/1952

_I'm not claiming any right or precedence over the official nlohmann / json issue or the method to perform the print using dump(). I think we all did the same thing by serendipity, and I bet I am not the first one  to have taken the .dump() call approach. All in all, if everyone can ~~work~~ debug better, that all that matters to me_


# 9. Acknowledgments / LICENSES

My work is under following license
> Licensed under the MIT License <http://opensource.org/licenses/MIT>.
> SPDX-License-Identifier: MIT
>
> Copyright (c) 2020 LoneWanderer-GH https://github.com/LoneWanderer-GH
>
>Permission is hereby  granted, free of charge, to any  person obtaining a copy of this software and associated  documentation files (the "Software"), to deal in the Software  without restriction, including without  limitation the rights to  use, copy,  modify, merge,  publish, distribute,  sublicense, and/or  sell copies  of  the Software,  and  to  permit persons  to  whom  the Software  is furnished to do so, subject to the following conditions:
> 
> The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
>
> THE SOFTWARE  IS PROVIDED "AS  IS", WITHOUT WARRANTY  OF ANY KIND,  EXPRESS OR IMPLIED,  INCLUDING BUT  NOT  LIMITED TO  THE  WARRANTIES OF  MERCHANTABILITY, FITNESS FOR  A PARTICULAR PURPOSE AND  NONINFRINGEMENT. IN NO EVENT  SHALL THE AUTHORS  OR COPYRIGHT  HOLDERS  BE  LIABLE FOR  ANY  CLAIM,  DAMAGES OR  OTHER LIABILITY, WHETHER IN AN ACTION OF  CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE  OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Some files in this repo are not mine and under other licenses
### nlohmann JSON for Modern C++

as per the file content:

> JSON for Modern C++
> version 3.7.3
> https://github.com/nlohmann/json
>
> Licensed under the MIT License <http://opensource.org/licenses/MIT>
> SPDX-License-Identifier: MIT
> Copyright (c) 2013-2019 Niels Lohmann <http://nlohmann.me>

### STL GDB evaluators/views/utilities - 1.03

as per the file content:

>   Simple GDB Macros writen by Dan Marinescu (H-PhD) - License GPL
>   Inspired by intial work of Tom Malnar,
>     Tony Novac (PhD) / Cornell / Stanford,
>     Gilad Mishne (PhD) and Many Many Others.
>   Contact: dan_c_marinescu@yahoo.com (Subject: STL)
>
>   Modified to work with g++ 4.3 by Anders Elton
>   Also added _member functions, that instead of printing the entire class in map, prints a member.

[1]: https://stackoverflow.com/q/55316620/7237062
[2]: https://www.adacore.com/community
