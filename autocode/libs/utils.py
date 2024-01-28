import logging
import sys
from typing import Any
import asyncio

LOG_STATS = 11
LOG_VERBOSE = 15

def setupLogging(logger: logging.Logger, log_level=logging.INFO, format='[%(levelname)-s %(asctime)s]: %(message)s'):
  logging.addLevelName(LOG_STATS, 'STATS')
  logging.addLevelName(LOG_VERBOSE, 'VERBOSE')

  herr = logging.StreamHandler(sys.stderr)
  herr.setLevel(logging.ERROR)
  herr.setFormatter(logging.Formatter(format))
  logger.addHandler(herr)

  hout = logging.StreamHandler(sys.stdout)
  hout.addFilter(lambda record: record.levelno < logging.ERROR)
  hout.setFormatter(logging.Formatter(format))
  logger.addHandler(hout)

  logger.setLevel(log_level)

def auto_async(func):
  def wrapper(*args, **kwargs):
    use_async = True
    if 'use_async' in kwargs:
      use_async = kwargs.pop('use_async')

    routine = func(*args, **kwargs)
    if use_async:
      return routine
    else:
      loop = asyncio.get_event_loop()
      return loop.run_until_complete(asyncio.ensure_future(routine))
  return wrapper

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
