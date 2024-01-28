import yaml
import json
from collections import namedtuple

class Dict2ObjParser:
  @classmethod
  def parse(cls, nested_dict):
    if (obj_type := type(nested_dict)) is not dict:
      raise TypeError(f"Expected 'dict' but found '{obj_type}'")
    return cls._convert_dict2namedtuples("root", nested_dict)

  @classmethod
  def _convert_dict2namedtuples(cls, tuple_name, obj):
    if type(obj) is dict:
      namedtuple_def = namedtuple(tuple_name, [*obj.keys(), 'to_dict'])
      namedtuple_obj = namedtuple_def(
        *[cls._convert_dict2namedtuples(k, v) for k, v in obj.items()],
        to_dict=lambda: obj,
      )
    elif type(obj) is list:
      namedtuple_obj = [
        cls._convert_dict2namedtuples(f"{tuple_name}_{idx}", v) for idx, v in enumerate(obj)
      ]
    else:
      namedtuple_obj = obj

    return namedtuple_obj

class CFG:
  @classmethod
  def load_config_as_obj(cls, fn, filetype='yaml'):
    configs = cls.load_config(fn, filetype)
    return Dict2ObjParser().parse(configs)

  @classmethod
  def load_config(cls, fn, filetype='yaml'):
    with open(fn) as f:
      if filetype == 'json':
        configs = json.load(f)
      else: # assume yaml
        configs = yaml.safe_load(f)
    return configs
