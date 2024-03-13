import yaml
import json
import os
from collections import namedtuple

from mext.libs.utils import ObjDict

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
  Extension2FileType = {
    '.json': 'json',
    '.yaml': 'yaml',
    '.yml': 'yaml',
  }
  supported_extensions = Extension2FileType.keys()

  @classmethod
  def load_config_as_objdict(cls, fn, filetype='auto'):
    configs = cls.load_config(fn, filetype)
    return ObjDict.convert_recursively(configs)

  @classmethod
  def load_config_as_obj(cls, fn, filetype='auto'):
    configs = cls.load_config(fn, filetype)
    return Dict2ObjParser().parse(configs)

  @classmethod
  def load_config(cls, fn, filetype='auto'):
    with open(fn) as f:
      if filetype == 'auto':
        _, ext = os.path.splitext(fn)
        if ext is None:
          raise RuntimeError(f'Unable to deduce file type for "{fn}"')
        if ext not in CFG.Extension2FileType:
          raise RuntimeError(f'Unknown file extension "{ext}"')
        filetype = CFG.Extension2FileType[ext]

      if filetype == 'json':
        configs = json.load(f)
      elif filetype == 'yaml':
        configs = yaml.safe_load(f)
      else:
        raise ValueError(f'Unknown file type "{filetype}"')
    return configs
