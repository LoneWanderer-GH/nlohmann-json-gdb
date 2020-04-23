import json
import gdb
import re

# matcher = re.compile("\$\d+ = (.*)")
matcher = re.compile("\$\d+ = ")


# from https://stackoverflow.com/questions/25851183/how-to-compare-two-json-objects-with-the-same-elements-in-a-different-order-equa
def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj

def perform(methods, variables):
    fancy_print("Perform tests")
    results = dict()
    for v in variables:
        results[v] = dict()
        for m in methods:
            # pjson_str = gdb.execute("pjson mixed_nested", to_string=True)
            # p_str = gdb.execute("p ")
            cmd = "{} {}".format(m, v)
            r = gdb.execute(cmd, to_string=True)
            # print("---")
            # print("CMD {} => {}".format(cmd, r))
            #print(len(r))
            if r[0] == "$":
                # r = r.replace("\\n", " ")
                # probably a real GDB command history
                # we should get rid of '$5 = '
                matches = matcher.split(r, maxsplit=1)
                # print("matches {}".format(matches))
                # r = matches.group(1)
                r = matches[-1]
            as_dict = json.loads(r)
            results[v][m] = as_dict
    return results

def check_result(results):
    fancy_print("Check results")
    count = 1
    passed_var_count = 0
    total_var_count = len(results.keys())
    status = True
    print_format = "{} {:<25} [{:^8s}]"
    for k, v in results.items():
        keys_list = list(v.keys())
        nb_jsons = len(keys_list)
        print_prefix = "Checking variable [{:02d}/{:02d}]: {:<15}".format(count, total_var_count, k)
        print("{} has {:02d} associated JSON{}".format(print_prefix, nb_jsons, "s" if nb_jsons > 1 else ""))
        i = 0
        global_compare = True
        while i <= nb_jsons - 2:
            m1 = keys_list[i]
            m2 = keys_list[i + 1]
            first  = v[m1]
            second = v[m2]
            # print("Checking {} vs {}".format(first, second))
            compare = (ordered(first) == ordered(second))
            if not compare:
                # print("Methods differ: {} != {} for '{}'".format(first, second, v))
                middle = "Method {} vs {}".format(m1,m2)
                print(print_format.format(print_prefix, middle, "FAILED"))
                status &= False
            # else:
            #     print("{} [{:^10s}]".format(print_prefix, "OK"))
                # print("Methods equals:{} != {} for '{}'".format(first, second, v))
                # dont alter status
            i += 2
            global_compare &= compare
        if global_compare:
            middle = "All methods"
            print(print_format.format(print_prefix, middle, "OK"))
            passed_var_count += 1
        # else:
        #     print("WTF ?!")
        count += 1
        print("")

    # status = (passed_var_count == total_var_count)

    return status, passed_var_count,total_var_count

STATUS_DICT = {True : "Passed", False: "Failed"}

def fancy_print(s):
    print("")
    print("")
    print("".center(80, "-"))
    print(" {} ".format(s).center(80, "-"))
    print("".center(80, "-"))
    print("")
    print("")

def test_suite():
    fancy_print("START TEST SUITE")
    methods = ["p", "pjson"]
    variables = ["fooz", "arr", "one", "mixed_nested"]

    results = perform(methods, variables)

    # check test suite is ok
    # results["toto"] = {"p": json.loads("{}"),
    #                    "pjson": json.loads("5")}

    status, passed, total = check_result(results)

    fancy_print("TEST SUITE STATUS: [{:^8} ({:02d}/{:02d} passed)]".format(STATUS_DICT[status], passed, total))

    if status:
        gdb.execute("q 0")
    else:
        gdb.execute("q 127")


test_suite()
