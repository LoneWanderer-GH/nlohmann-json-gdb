# A simplistic nlohmann-json-gdb pretty printer

Provides gdb script and python gdb script to pretty print a  nlohmann / json  (https://github.com/nlohmann/json)

# History /Reasons this exists

In March 2019, I was stuck with the lack of nlohmann json debug utilities. I could not find any support to print what was in memory
I ended up with a stack overflow post with [what I found to be revelant][1] for that matter. _If something was indeed broadly available, weel, I'm sorry_

In 2020 github issue was opened with the same intent here and relies basically the same initial solution I used: https://github.com/nlohmann/json/issues/1952

_I'm not claiming any right or precedence over the official nlohmann / json issue or the method to perform the print using dump(). I think we all did the same thing by serendipity, and I bet I am not the first one  to have taken the .dump() call approach. All in all, if everyone can ~~work~~ debug better, that all that matters to me_

Plus, I was interested in playing around with GDB/memory/python, thats why I took some time to treat this matter.
I ended up with the code here.

# What is provided here

 - [x] a sample GPR project file + sources to be built using gprbuild
 - [x] the *gdb script* trick to use the inferior process to perform the json dump for us. It implies that the executable and memory are not corrupted, and variables not optimized out
   (see"gdb_script\simple_gdb_method.gdb")
 - [x] the *python gdb pretty printer code* to walk inside memory (of a live inferior process) to perform the same json dump. Here, we do not rely on the existing dump() method but we explore memory to do it ourselves (see "gdb_python_pretty_printer\load_pretty_printer.gdb" and "gdb_python_pretty_printer\printer.py")

 _the gdb defined command and the gdb pretty printer should probably be 2 mutually exclusive methods_

 It is confirmed working on w10 x64 with:

 - https://github.com/nlohmann/json version 3.7.3
 - GNU gdb (GDB) 8.3 for GNAT Community 2019 [rev=gdb-8.3-ref-194-g3fc1095]
 - c++ project built with GPRBUILD/ GNAT Community 2019 (20190517) (x86_64-pc-mingw32)

 Other plaforms should work too, but I can't test that.

 ## Load a GDB script

 in your gdb console:
 ```
 (gdb) source some_file
 ```

 ## GDB pretty printer usage

 The GDB Pretty printer is written in Python. Once loaded, you should not notice anything python related in your gdb usage.
 See here to load the pretty printer : https://github.com/LoneWanderer-GH/nlohmann-json-gdb/blob/master/.gdbinit

once loaded, its just a regular GDB variable print !

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

 ## GDB script usage

Here we use a kind of GDB macro defined in a gdb script file https://github.com/LoneWanderer-GH/nlohmann-json-gdb/blob/master/.gdbinit

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

## possible improvements
 - [ ] the python gdb pretty printer core dump management is not (yet ?) done (i.e. core dump means no inferior process to call dump() in any way, and possibly less/no (debug) symbols to rely on)
 - [ ] printer can be customised further to print the 0x addresses, I chose not to since the whole point for me was NOT to explore them in gdb. You would have to add few python `print` here and there

 # Another approach I know of
 _from a guru of my workplace_
  - simply define a single function in the program to perform the dump of a json variable. This is almost exactly similar to the gdb inferior dump() call

 # Examples / Tests

 see https://github.com/LoneWanderer-GH/nlohmann-json-gdb/blob/master/src/main.cpp for some basic C++ JSON declarations.

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

# LICENSES


## nlohmann JSON for Modern C++

as per the file content:

>     __ _____ _____ _____
>  __|  |   __|     |   | |  JSON for Modern C++
> |  |  |__   |  |  | | | |  version 3.7.3
> |_____|_____|_____|_|___|  https://github.com/nlohmann/json
>
> Licensed under the MIT License <http://opensource.org/licenses/MIT>.
> SPDX-License-Identifier: MIT
> Copyright (c) 2013-2019 Niels Lohmann <http://nlohmann.me>.

## STL GDB evaluators/views/utilities - 1.03

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
