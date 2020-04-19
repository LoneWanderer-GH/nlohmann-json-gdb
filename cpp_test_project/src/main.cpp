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
  json fooz;
  fooz = 0.7;

  json arr = {3, "25", 0.5};

  json one;
  one["first"] = "second";

  json foo;
  foo["flex"] = 0.2;
  foo["bool"] = true;
  foo["int"] = 5;
  foo["float"] = 5.22;
  foo["trap "] = "you fell";
  foo["awesome_str"] = "bleh";
  foo["nested"] = {{"bar", "barz"}};
  foo["array"] = { 1, 0, 2 };

  std::cout << "fooz" << std::endl;
  std::cout << fooz.dump(4) << std::endl << std::endl;

  std::cout << "arr" << std::endl;
  std::cout << arr.dump(4) << std::endl << std::endl;

  std::cout << "one" << std::endl;
  std::cout << one.dump(4) << std::endl << std::endl;

  std::cout << "foo" << std::endl;
  std::cout << foo.dump(4) << std::endl << std::endl;

  json mixed_nested;

  mixed_nested["Jean"] = fooz;
  mixed_nested["Baptiste"] = one;
  mixed_nested["Emmanuel"] = arr;
  mixed_nested["Zorg"] = foo;

  std::cout << "5th element" << std::endl;
  std::cout << mixed_nested.dump(4) << std::endl << std::endl;

  std::cout << "END" << std::endl;

  return 0;
}
