import sys
from typing import Any
import os
import traceback
import re

def ensure_folder_exists(fn):
  folder = os.path.dirname(fn)
  if folder != '':
    os.makedirs(folder, exist_ok=True)

def format_exception(exc):
  return ''.join(traceback.format_exception_only(type(exc), exc)).strip()

def indent_lines(s_lines: str, indent):
  indent_spaces = ' '*indent
  s_indented, _ = re.subn(r'(^|\n)', fr'\1{indent_spaces}', s_lines)
  return s_indented

def fence_content(content, spec='', min_fence_num=3, marker='`'):
  block_fences = re.findall(r'\`{3,}', content)
  max_block_fences = max([*map(len, block_fences), min_fence_num-1])
  fence = marker*(max_block_fences+1)
  return f'{fence}{spec}\n{content}\n{fence}'

class ObjDict(dict):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  def __getattribute__(self, __name: str) -> Any:
    try:
      return super().__getattribute__(__name)
    except AttributeError:
      return self[__name]

  def __setattr__(self, __name: str, __value: Any) -> None:
    self[__name] = __value

  def __delattr__(self, __name: str) -> None:
    del self[__name]

  @classmethod
  def convert_recursively(cls, _v):
    objdict = None
    if type(_v) is dict:
      objdict = ObjDict(_v)
      for k,v in _v.items():
        objdict[k] = cls.convert_recursively(v)
    elif type(_v) is list:
      objdict = [
        cls.convert_recursively(v) for v in _v
      ]
    else:
      objdict = _v

    return objdict

  @classmethod
  def merge_recursively(cls, obj1, obj2):
    for key, value in obj2.items():
      if key in obj1 and isinstance(obj1[key], dict) and isinstance(value, dict):
        # Recursive call for nested dictionaries
        cls.merge_recursively(obj1[key], value)
      else:
        # Update or add the key-value pair
        obj1[key] = value
    return obj1

  @classmethod
  def set_defaults(cls, obj1, obj2):
    obj2 = ObjDict.convert_recursively(obj2)
    for key, value in obj2.items():
      if key in obj1:
        if isinstance(obj1[key], dict) and isinstance(value, dict):
          # Recursive call for nested dictionaries
          cls.set_defaults(obj1[key], value)
      else:
        # Update or add the key-value pair
        obj1[key] = value
    return obj1
