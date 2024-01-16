import argparse
import os
import json


class Configuration(dict):
    instance = None
    def __new__(cls, *args, **kwargs):
        if not isinstance(cls.instance, cls):
            cls.instance = dict.__new__(cls)
        return cls.instance

    def __init__(self, config_name: str, arg_parser: argparse.ArgumentParser, extras_from_config = True) -> None:
        if os.path.exists(config_name):
            with open(config_name) as f:
                Configuration.config = json.load(f)
        config = Configuration.config

        parse_args, unknown_args = arg_parser.parse_known_args()
        key_values_args = vars(parse_args)

        def fill(item):
            if item[1] is not None:
                return item
            return (item[0], config.get(item[0]))
        
        def required(item):
            for action in arg_parser._actions:
                if '--'+item in action.option_strings and action.required:
                    return True
            return False


        res = [fill(item) for item in key_values_args.items()]
        first = next(filter(lambda item: item[1] is None and required(item[0]), res), None)
        if first is not None:
            #sys.stderr.write('error: %s\n' % message)
            arg_parser.print_help()
            exit(2)

        if extras_from_config:
            res_set = set(item[0] for item in res)
            config_values = [(k, v) for k, v in config.items()]
            res.extend(item for item in config_values if item[0] not in res_set)



        super().__init__(res)

    @staticmethod
    def argument_parser():
        pass