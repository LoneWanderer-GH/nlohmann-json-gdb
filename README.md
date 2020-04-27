# A simplistic GDB pretty printer for [nlohmann-json c++][3]

![CI-OS-ubuntu-windows](https://github.com/LoneWanderer-GH/nlohmann-json-gdb/workflows/CI-OS-ubuntu-windows/badge.svg)
![CI-GDB-releases-Ubuntu](https://github.com/LoneWanderer-GH/nlohmann-json-gdb/workflows/CI-GDB-releases-Ubuntu/badge.svg)

Provides GDB script and python GDB pretty printer script that allows to to print a  [nlohmann / json][3]
 - [x] compatible with a live inferior process with debug symbols
 - [x] compatible with core dump files with debug symbols

This is also a playground for me to get used to Git, Github, and GDB.

## Release notes:

### v0.0.1: first pretty printer release

Features:
 - improved overall GDB python pretty printer code
    - now multiplatform
 - created some sort of a CI process to check we did not mess up with features. It currently checks that the pretty printer matches the json.dump() output.

Limitations:
 - I found that finding the exact real symbol behind `std::string` is not possible until you have run the inferior GDB process (command `r`).
     So for now, it finds the symbol with what I had at hand, I'm pretty sure its is C++11 compatible only.
     see [Known limitations](#Known-limitations)

---

**Table of contents**

 1. [Prerequisites](#Prerequisites)
 2. [Installing](#Installing)
 3. [Content](#Content)
 4. [Usage](#Usage)
 5. [Possible improvements / Contributions](#Possible-improvements-Contributions)
 6. [Known limitations](#Known-limitations)
 7. [Examples and tests](#Examples-Tests)
 8. [History](#History)
 9. [Acknowledgments / LICENSES](#Acknowledgments-LICENSES)
 10. [Links concerning STL and GDB](#Links)

<a name="Prerequisites"></a>
# 1. Prerequisites

 - *GDB* debugger installed, ready to use.
     - Tested on ubutun x64, with python 2.7 and python 3.6:
         - GDB 7.12.1
         - GDB 8.0
         - GDB 8.0.1
         - GDB 8.1
         - GDB 8.1.1
         - GDB 8.2
         - GDB 8.2.1
         - GDB 8.3
         - GDB 8.3.1
         - GDB 9.1
     - Windows 8.3 with python 2.7.16. Given the successful tests on Ubuntu x64 with various GDB and python versions, it is likely to work for Windows too.
 - an executable to debug **with debug symbols available to GDB** which uses the [JSON lib 3.7.3][3]
 - or a core dump **with debug symbols available to GDB** (for linux users)
 - _Some [GDB commands knowledge][4] might be useful for your debug session to be successful ;)_


## Your GDB does not support python ?

You need to upgrade your GDB.

Have a look [on this wiki page](https://github.com/LoneWanderer-GH/nlohmann-json-gdb/wiki/C---build-environment-:-GDB-8.3-on-Raspberry-Pi-3--Raspbian-9.11-stretch) for an example of GDB build on raspbian 9.11


## Optional

 - a [GNAT CE 2019][2] install to compile and play with the provided test projects


<a name="Installing"></a>
# 2. Installing

Just copy the GDB and/or python script you need in a folder near your executable to debug, and of course, load it into your GDB.
See [Content](#Content) and [Usage](#Usage) sections below for more details.

<a name="Content"></a>
# 3. Content

 - [x] the *[GDB command file](scripts/nlohmann_json.gdb)* : it uses the live process under debug to call `dump()`. It implies that the executable and memory are not corrupted, variables not optimized out
 - [x] the *[GDB python pretty printer file](scripts/nlohmann_json.py)* : here, we do not rely on the existing dump() method but we explore memory using debug symbols to do it ourselves, if the inferior process is broken in some way, we may still have some means to dump a json compare to previous method.

 Additional content:
  - [x] some tests projects, see [7. Examples / Tests](#7-Examples--Tests) for further details:
    - a [c++ test project](tests/cpp_test_project)
    - a [c++ test project to bruteforcefully find relevant offets for a given platform](tests/offsets_finder)

<a name="Usage"></a>

# 4. Usage

## How to load a GDB script

in your GDB console:
```
(gdb) source some_file
```
Works for both GDB and Python scripts.
I strongly suggest you refer to GDB documentation.

## GDB pretty printer usage (the Python printer)

The GDB Pretty printer is [written in Python](scripts/nlohmann_json.py).

To load it into GDB (you may adapt path to your settings):
```
(gdb) source nlohmann_json.py
```

Then, a simple GDB command does the trick:

```
(gdb) p foo
$ 1 = {
    "flex" : 0.2,
    "awesome_str": "bleh",
    "nested": {
        "bar": "barz"
    }
}
```

## GDB script usage (the GDB command)

Here we use a kind of **GDB macro** defined in a [GDB script file](scripts/nlohmann_json.gdb)

To load it into GDB (you may adapt path to your settings):
```
(gdb) source nlohmann_json.gdb
```

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
_notice that `pjson` does not print the GDB history tag $_

## No debug symbols ?

That's a more advanced GDB technique. You should have a look at [this SO post](https://stackoverflow.com/questions/866721/how-to-generate-gcc-debug-symbol-outside-the-build-target) where pretty much everything is explained.

_The idea is to compile and extract the debug data into specific files.
Then load this files into your GDB to have all symbols at hand, even if you're working with a stripped software._

see also [this GDB doc](https://doc.ecoscentric.com/gnutools/doc/gdb/Files.html#Files) concerning `symbol-file `command.

<a name="Possible-improvements-Contributions"></a>
# 5. Possible improvements / Contributions

## Contribute

_Coding technique for the pretty printer is quite naive, but it works.
Any seasoned advice and support appreciated. Aspects I would like to improve:_
 - performance
 - code style
 - Release packaging
 - Lib version checks

## Possible TODO list

 - [ ] dont use this TODO list, but Github issues and Github project management
 - [ ] printer can be customised further to print the 0x addresses, I chose not to since the whole point for me was NOT to explore them in GDB. You would have to add few python `print` here and there
 - [ ] add the hexa value for floating point numbers, or for all numerical values
 - [ ] reduce amount of copy/pasta between [offsets_finder.py](tests/offsets_finder/offsets_finder.py) and [nlohmann_json.py](scripts/nlohmann_json.py)

 - [x] ~~the pythonGDBpretty printer core dump management is not (yet ?) done (i.e. core dump means no inferior process to call dump() in any way, and possibly less/no (debug) symbols to rely on)~~
     Core dump with debug symbols tested and should be working.
 - [x] ~~Improve method to get `std::string` `type` and `sizeof`. The current method assumes some known symbols names, that most probably depends on the compilation tools (C++11).
     Sadly, GDB command `whatis` and `ptype` cannot resolve directly and easily `std::string`~~
     Solved with the gdb type template argument type extraction feature


<a name="Known-limitations"></a>
# 6. Known limitations

 - Floating point numbers may appear differently depending on the method used. This is due to differences in float-to-string from [GDB][4] and [json c++][3].
    For more confidence, we could modify the python pretty printer to provide the exact hexadecimal memory value + the decimal one for sake of completness.
    However, the checks using python `json` module show no difference concerning floats once parsed.

 - Linux over windows (Ubuntun-windows) : `gprbuild` command on Ubuntu-windows/Debian-windows may not work correctly, so a legit Linux environment may be needed if you want to play with the tests projects on Linux.


<a name="Examples-Tests"></a>
# 7. Examples and tests


## Sample C++ project

The C++ project is located in `tests/cpp_test_project`

 1. Build [debug_printer.gpr](tests/cpp_test_project/debug_printer.gpr) with the following command

    ```
    cd tests/cpp_test_project
    gprbuild -p
    ```

    _(`-p`creates the obj/exe dirs if missing; gpr file can be deduced from current folder content)_

 2. see [main.cpp](tests/cpp_test_project/src/main.cpp) for some basic C++ JSON declarations.
    It should looke like:

    ```
    // C++ code
    ...
    json foo;
    foo["flex"] = 0.2;
    foo["bool"] = true;
    foo["int"] = 5;
    foo["float"] = 5.22;
    foo["trap "] = "you fell";
    foo["awesome_str"] = "bleh";
    foo["nested"] = {{"bar", "barz"}};
    foo["array"] = { 1, 0, 2 };
    ...
    ```

 3. Once the exe is built, launch a GDB session, either in console or using your favorite IDE.

    2 cases :

     - GDB autoloads the `.gdbinit` file located near the gpr file
     - GDb does not autoload the `.gdbinit` file. In this case type in gdb:
        ```
        (gdb) source .gdbinit
        ```

 4. Now you can use the following GDB commands:

    ```
    (gdb) pjson foo
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

    GDB python pretty printer:

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

## C++ project: awful bruteforce method to check that memory offsets are correct

This part will tell if the method to find data offsets in the proposed python script is correct.

 1. build the project [simple_offsets_finder.gpr](tests/offsets_finder/simple_offsets_finder.gpr) with the command
        `gprbuild -p -P debug_printer.gpr`

 2. Start a GDB session, here is an console output example, using this console command to launch GDB:

     ```
     gdb --se=exe/main.exe -command=find_offsets.gdb --batch
     ```
    <details>
    ```
    #
    # Force gdb to use pretty print of structures managed by default (instead of a barely flat line)
    #
    # set print pretty
    #
    #
    # load the offset finder python gdb script
    #
    source offsets_finder.py
    #
    PLATFORM_BITS 64

    Search range will be:
    MIN: 2 - MAX: 512 - STEP: 2


    -------------The researched std::string type for this executable is-------------
    std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> >-
    Using regex: ^std::__cxx.*::basic_string<char,.*>$
    --------------------------------------------------------------------------------


    --------The researched nlohmann::basic_json type for this executable is---------
    nlohmann::basic_json<std::map, std::vector, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> >, bool, long long, unsigned long long, double, std::allocator, nlohmann::adl_serializer>
    Using regex: ^nlohmann::basic_json<.*>$
    --------------------------------------------------------------------------------

    #
    # Auto setting break point before exe prints mixed_nested
    #
    Breakpoint 1 at 0x401753: file F:\DEV\Projets\nlohmann-json-gdb\offsets_finder\src\main.cpp, line 44.
    #
    # Running the exe
       THIS
        IS
       THE
       END
      (ABC)
       MY

    Breakpoint 1, main () at F:\DEV\Projets\nlohmann-json-gdb\offsets_finder\src\main.cpp:44
    44      F:\DEV\Projets\nlohmann-json-gdb\offsets_finder\src\main.cpp: No such file or directory.
    $1 = (nlohmann::basic_json<std::map, std::vector, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> >, bool, long long, unsigned long long, double, std::allocator, nlohmann::adl_serializer>::object_t *) 0x1104b90
    #
    # ### Prints using python pretty printer offsetts finder ###
    #
    # Print simple_json (python pretty printer)
    $2 = Expected pair: <key:first, value:second>
    Testing Node.Key offset 2
    Testing Node.Key offset 4
    Testing Node.Key offset 6
    Testing Node.Key offset 8
    Testing Node.Key offset 10
    Testing Node.Key offset 12
    Testing Node.Key offset 14
    Testing Node.Key offset 16
    Testing Node.Key offset 18
    Testing Node.Key offset 20
    Testing Node.Key offset 22
    Testing Node.Key offset 24
    Testing Node.Key offset 26
    Testing Node.Key offset 28
    Testing Node.Key offset 30
    Testing Node.Key offset 32
    Found the key '"first"'
    Testing Node.Value offset 2
    Testing Node.Value offset 4
    Testing Node.Value offset 6
    Testing Node.Value offset 8
    Testing Node.Value offset 10
    Testing Node.Value offset 12
    Testing Node.Value offset 14
    Testing Node.Value offset 16
    Testing Node.Value offset 18
    Testing Node.Value offset 20
    Testing Node.Value offset 22
    Testing Node.Value offset 24
    Testing Node.Value offset 26
    Testing Node.Value offset 28
    Testing Node.Value offset 30
    Testing Node.Value offset 32
    Found the value '"second"'


    Offsets for STD::MAP <key,val> exploration from a given node are:

    MAGIC_OFFSET_STD_MAP_KEY        = 32 = expected value from symbols 32
    MAGIC_OFFSET_STD_MAP_VAL        = 32 = expected value from symbols 32

     ===> Offsets for STD::MAP : [ FOUND ] <===



    #
    # Print simple_array (python pretty printer)
    #
    $3 = Trying to search array element 996699FOO at index (2)
    Testing vector value offset 2
    value: Not a valid JSON type, continuing
    Testing vector value offset 4
    value: Not a valid JSON type, continuing
    Testing vector value offset 6
    value: null
    Testing vector value offset 8
    value: 25
    Testing vector value offset 10
    value: Not a valid JSON type, continuing
    Testing vector value offset 12
    value: Not a valid JSON type, continuing
    Testing vector value offset 14
    value: null
    Testing vector value offset 16
    value: "996699FOO"


    Offsets for STD::VECTOR exploration are:

    MAGIC_OFFSET_STD_VECTOR = 16
    OFFSET expected value   = 16 (o["_M_impl"]["_M_start"], vector element size)

     ===> Offsets for STD::VECTOR : [ FOUND ] <===





    ############ FORCING A NORMAL EXIT (code 0) ############

    Errors in python should have triggered a different exit code earlier

    A debugging session is active.

            Inferior 1 [process 1320] will be killed.

    Quit anyway? (y or n) [answered Y; input not from terminal]

    ```
    </details>

## Another approach I know of
 _from a guru of my workplace_
  - simply define a single function in the program to perform the dump of a json variable, say `print()`. Then you can call it during yourGDBsession.
  This is almost exactly similar to theGDBinferior dump() call macro `pjson` presented above.

<a name="History"></a>
# 8. History

 - In March 2019, I was stuck with the lack of nlohmann json debug utilities. I could not find any support to print what the json was during a debug session. I ended up with a stack overflow post with [what I found to be revelant][1] for that matter. In addition, I was interested in playing around with GDB/memory/python, thats why I took some time to treat this matter. I ended up with the code here.
 - In 2020 a Github issue was opened with the same intent here and relies basically on the same initial solution I used: https://github.com/nlohmann/json/issues/1952

_I'm not claiming any right or precedence over the official nlohmann / json issue or the method to perform the print using dump(). I think we all did the same thing by serendipity, and I bet I am not the first one  to have taken the .dump() call approach. All in all, if everyone can ~~work~~ debug better, that all that matters to me_

<a name="Acknowledgments-LICENSES"></a>
# 9. Acknowledgments / LICENSES

## ACKNOWLEDGMENTS

 - The [GDB documentation][4] was particularly useful, in particular the [Python part][5].
 - The red black tree traversal and STL exploration in python is directly inspired from the STLGDBscripts.

A few other links were useful and are linked in the python source.
 - The python exceptions printing is [inspired from GEF][6]
 - The `std::string` print in pythonGDBis inspired from [this stackoverflow post][7]

## LICENSE
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
>    Tony Novac (PhD) / Cornell / Stanford,
>    Gilad Mishne (PhD) and Many Many Others.
>   Contact: dan_c_marinescu@yahoo.com (Subject: STL)
>
>   Modified to work with g++ 4.3 by Anders Elton
>   Also added `_member` functions, that instead of printing the entire class in map, prints a member.

<a name="Links"></a>
# 10. Links

Some useful links concerning STL and GDB

- https://sourceware.org/gdb/wiki/STLSupport
- http://www.yolinux.com/TUTORIALS/src/dbinit_stl_views-1.03.txt
- http://wiki.codeblocks.org/index.php/Pretty_Printers
- https://github.com/NREL/EnergyPlus/wiki/Debugging-STL-objects-in-GDB
- https://stackoverflow.com/questions/11606048/how-to-pretty-print-stl-containers-in-gdb
- https://gist.github.com/chaozh/9252fc01b3723f795589
- https://gist.github.com/skyscribe/3978082

[1]: https://stackoverflow.com/q/55316620/7237062
[2]: https://www.adacore.com/community
[3]: https://github.com/nlohmann/json
[4]: https://sourceware.org/gdb/current/onlinedocs/gdb/index.html
[5]: https://sourceware.org/gdb/current/onlinedocs/gdb/Python-API.html#Python-API
[6]: https://github.com/hugsy/gef/blob/dev/gef.py
[7]: https://stackoverflow.com/questions/6776961/how-to-inspect-stdstring-in-gdb-with-no-source-code
