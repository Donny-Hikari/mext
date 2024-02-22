import unittest

from mext.libs.utils import ObjDict

class TestObjDict(unittest.TestCase):
  def test_merge_recursively(self):
    a = ObjDict({
      'a': 1,
      'b': {
        'c': 2,
        'f': {
          'g': 4,
        }
      },
      'h': {
        'i': 5,
      },
      'd': 3,
    })
    b = ObjDict({
      'a': 10,
      'b': {
        'e': 9,
        'f': {
          'j': 8,
        },
      },
      'h': {
        'i': 7,
      },
    })
    ObjDict.merge_recursively(a, b)
    self.assertDictEqual(a, {
      'a': 10,
      'b': {
        'c': 2,
        'e': 9,
        'f': {
          'g': 4,
          'j': 8,
        },
      },
      'h': {
        'i': 7,
      },
      'd': 3,
    })

  def test_set_defaults(self):
    a = ObjDict({
      'a': 1,
      'b': {
        'c': 2,
        'f': {
          'g': 4,
        }
      },
      'h': {
        'i': 5,
      },
      'd': 3,
    })
    b = ObjDict({
      'a': 10,
      'b': {
        'e': 9,
        'f': {
          'j': 8,
        },
      },
      'h': {
        'i': 7,
      },
    })
    ObjDict.set_defaults(a, b)
    self.assertDictEqual(a, {
      'a': 1,
      'b': {
        'c': 2,
        'e': 9,
        'f': {
          'g': 4,
          'j': 8,
        },
      },
      'h': {
        'i': 5,
      },
      'd': 3,
    })
