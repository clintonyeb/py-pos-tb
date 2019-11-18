import re


class Aspect(type):
    aspect_rules = []
    wrapped_methods = []

    def __new__(mcs, name, bases, dct):
        for key, value in dct.items():
            if hasattr(value, "__call__") and key != "__metaclass__":
                dct[key] = Aspect.wrap_method(value)
        return type.__new__(mcs, name, bases, dct)

    @classmethod
    def register(mcs, name_pattern="", in_objects=(), out_objects=(),
                 pre_function=None,
                 post_function=None):
        rule = {"name_pattern": name_pattern, "in_objects": in_objects,
                "out_objects": out_objects,
                "pre": pre_function, "post": post_function}
        mcs.aspect_rules.append(rule)

    @classmethod
    def wrap_method(mcs, method):
        def call(*args, **kw):
            pre_functions = mcs.matching_pre_functions(method, args, kw)
            for function in pre_functions:
                function(*args, **kw)
            results = method(*args, **kw)
            post_functions = mcs.matching_post_functions(method, results)
            for function in post_functions:
                function(results, *args, **kw)
            return results

        return call

    @classmethod
    def matching_names(mcs, method):
        return [rule for rule in mcs.aspect_rules
                if re.match(rule["name_pattern"], method.__name__)
                or rule["name_pattern"] == ""
                ]

    @classmethod
    def matching_pre_functions(mcs, method, args, kw):
        all_args = args + tuple(kw.values())
        return [rule["pre"] for rule in mcs.matching_names(method)
                if rule["pre"] and
                (rule["in_objects"] == () or
                 any((type(arg) in rule["in_objects"] for arg in all_args)))
                ]

    @classmethod
    def matching_post_functions(mcs, method, results):
        if type(results) != tuple:
            results = (results,)
        return [rule["post"] for rule in mcs.matching_names(method)
                if rule["post"] and
                (rule["out_objects"] == () or
                 any((type(result) in rule["out_objects"] for result in results)))
                ]


if __name__ == "__main__":
    # Testing
    class Address(object):
        def __repr__(self):
            return "Address..."


    class Person(object, metaclass=Aspect):

        def updateAddress(self, address):
            pass

        def __str__(self):
            return "person object"


    def log_update(*args, **kw):
        print("Updating object %s" % str(args[0]))


    def log_address(*args, **kw):
        addresses = [arg for arg in (args + tuple(kw.values()))
                     if type(arg) == Address]
        print(addresses)


    Aspect.register(name_pattern="^update.*", pre_function=log_update)
    Aspect.register(in_objects=(Address,), pre_function=log_address)

    p = Person()
    p.updateAddress(Address())
