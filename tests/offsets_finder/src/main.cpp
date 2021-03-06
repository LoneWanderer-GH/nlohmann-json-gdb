/*
   Licensed under the MIT License <http://opensource.org/licenses/MIT>.
   SPDX-License-Identifier: MIT
   Copyright (c) 2020 LoneWanderer-GH https://github.com/LoneWanderer-GH

   Permission is hereby  granted, free of charge, to any  person obtaining a copy
   of this software and associated  documentation files (the "Software"), to deal
   in the Software  without restriction, including without  limitation the rights
   to  use, copy,  modify, merge,  publish, distribute,  sublicense, and/or  sell
   copies  of  the Software,  and  to  permit persons  to  whom  the Software  is
   furnished to do so, subject to the following conditions:

   The above copyright notice and this permission notice shall be included in all
   copies or substantial portions of the Software.

   THE SOFTWARE  IS PROVIDED "AS  IS", WITHOUT WARRANTY  OF ANY KIND,  EXPRESS OR
   IMPLIED,  INCLUDING BUT  NOT  LIMITED TO  THE  WARRANTIES OF  MERCHANTABILITY,
   FITNESS FOR  A PARTICULAR PURPOSE AND  NONINFRINGEMENT. IN NO EVENT  SHALL THE
   AUTHORS  OR COPYRIGHT  HOLDERS  BE  LIABLE FOR  ANY  CLAIM,  DAMAGES OR  OTHER
   LIABILITY, WHETHER IN AN ACTION OF  CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   OUT OF OR IN CONNECTION WITH THE SOFTWARE  OR THE USE OR OTHER DEALINGS IN THE
   SOFTWARE.
 */

#include "json.hpp"
#include <iostream>


using json = nlohmann::json;

int main() {

  json simple_array = {"azd", 25, "996699FOO"};

  json simple_json;
  simple_json["first"] = "second";

  std::cout << "   THIS  " << std::endl;
  std::cout << "    IS   " << std::endl;
  std::cout << "   THE   " << std::endl;
  std::cout << "   END   " << std::endl;
  std::cout << "  (ABC)  " << std::endl;
  std::cout << "   MY    " << std::endl;
  std::cout << "  ONLY   " << std::endl;
  std::cout << " FRIEND  " << std::endl;

  return 0;
}
