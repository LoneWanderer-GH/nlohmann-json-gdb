#include <json.hpp>
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

  return 0;
}
