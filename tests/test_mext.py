
import unittest
from os import path

from autocode.libs.utils import ObjDict
from autocode.libs.mext import MextParser

class TestMextParser(unittest.TestCase):
  dirs = ObjDict({
    'prompts': "tests/mext_prompts",
  })

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    self.prompts = ObjDict({
      'empty_template': path.join(self.dirs.prompts, "empty.mext"),
      'template1': path.join(self.dirs.prompts, "include1.mext"),
    })

  def test_var(self):
    parser = MextParser()
    res = parser.parse("""{var}""", {
      'var': "Pass",
    }, use_async=False)
    self.assertEqual(res, "Pass")

  def test_option(self):
    parser = MextParser()

    parser.reset()
    parser.enable_trace(True)
    res = parser.parse("""\
{@option final_strip off}
Empty line at the end.
""", use_async=False)
    self.assertEqual(res, "Empty line at the end.\n")

    parser = MextParser()
    res = parser.parse("""\
{@option final_strip off}
{var}
Empty line above.""", {
      'var': "",
    }, use_async=False)
    self.assertEqual(res, "\nEmpty line above.")

  def test_set(self):
    parser = MextParser()
    res = parser.parse("""\
{var1}
{@set var1 var2}
{var1}""", {
      'var1': "Val1",
      'var2': "Val2",
    }, use_async=False)
    self.assertEqual(res, "Val1\nVal2")

  def test_default(self):
    parser = MextParser()
    res = parser.parse("""\
{@default var1 var2}
{var1}""", {
      'var2': "Val2",
    }, use_async=False)
    self.assertEqual(res, "Val2")

    res = parser.parse("""\
{@default var1 var2}
{var1}""", {
      'var1': "Val1",
      'var2': "Val2",
    }, use_async=False)
    self.assertEqual(res, "Val1")

  def test_number(self):
    parser = MextParser()
    res = parser.parse("""\
{@set var1 100}
{var1}""", use_async=False)
    self.assertEqual(res, "100")

    res = parser.parse("""\
{@set var1 100.01}
{var1}""", use_async=False)
    self.assertAlmostEqual(float(res), 100.01)

    res = parser.parse("""\
{@set var1 98765.43210}
{var1}""", use_async=False)
    self.assertAlmostEqual(float(res), 98765.43210)

    res = parser.parse("""\
{@set var1 1e2}
{var1}""", use_async=False)
    self.assertAlmostEqual(float(res), 100.0)

    res = parser.parse("""\
{@set var1 1.0e2}
{var1}""", use_async=False)
    self.assertAlmostEqual(float(res), 100.0)

  def test_include(self):
    parser = MextParser()
    res = parser.parse("""{@include prompts.empty_template}""", params={
      'prompts': self.prompts,
    }, use_async=False)
    self.assertEqual(res, "")

    res = parser.parse("""{@include prompts.template1}""", params={
      'prompts': self.prompts,
    }, use_async=False)
    self.assertEqual(res, "Using default value.")

    res = parser.parse("""{@include prompts.template1}""", params={
      'prompts': self.prompts,
      'var1': False,
    }, use_async=False)
    self.assertEqual(res, "Using additional parameter value.")

    res = parser.parse("""{@include prompts.template1 var1=false}""", params={
      'prompts': self.prompts,
    }, use_async=False)
    self.assertEqual(res, "Using additional parameter value.")

    res = parser.parse("""\
Included from template1:
{@include prompts.template1 var1=false}
""", params={
      'prompts': self.prompts,
    }, use_async=False)
    self.assertEqual(res, "Included from template1:\nUsing additional parameter value.")

  def test_input(self):
    parser = MextParser()
    res = parser.parse("""\
name: {@input name}
age: {@input age}
We now know that {name} is {age} year old.
""",
      callbacks={
        'name': lambda x: "Alice",
        'age': lambda x: 19,
    }, use_async=False)
    self.assertEqual(res, """\
name: Alice
age: 19
We now know that Alice is 19 year old.\
""")
    self.assertDictEqual(parser.input_results, {
      'name': "Alice",
      'age': 19,
    })

  def test_if(self):
    parser = MextParser()
    res = parser.parse("""{@if true}True{@else}False{@endif}""", use_async=False)
    self.assertEqual(res, "True")

    res = parser.parse("""{@if false}True{@else}False{@endif}""", use_async=False)
    self.assertEqual(res, "False")

    res = parser.parse("""{@if var_true}True{@else}False{@endif}""", {
      'var_true': True,
    }, use_async=False)
    self.assertEqual(res, "True")

    res = parser.parse("""{@if var_true}{val_pass}{@else}Failed{@endif}""", {
      'var_true': True,
      'val_pass': "Pass",
    }, use_async=False)
    self.assertEqual(res, "Pass")

    res = parser.parse("""{@if var_false}Failed{@else}{val_pass}{@endif}""", {
      'var_false': False,
      'val_pass': "Pass",
    }, use_async=False)
    self.assertEqual(res, "Pass")

    res = parser.parse("""{@if not var_true}Failed{@else}{val_pass}{@endif}""", {
      'var_true': True,
      'val_pass': "Pass",
    }, use_async=False)
    self.assertEqual(res, "Pass")

    res = parser.parse("""{@if not var_true}Failed{@else}{@if false}Nested Failed{@else}{val_pass}{@endif}{@endif}""", {
      'var_true': True,
      'val_pass': "Pass",
    }, use_async=False)
    self.assertEqual(res, "Pass")

  def test_if_empty(self):
    parser = MextParser()
    cases = [
      ([], True),
      ({}, True),
      (None, True),
      ([1], False),
      ({'a': 1}, False),
      (0, False),
      ('a', False),
    ]
    for var, expected in cases:
      res = parser.parse(""""{var}" is {@if empty var}empty{@else}not empty{@endif}""", {
        'var': var,
      }, use_async=False)
      self.assertEqual(res, f'"{var}" is ' + ("empty" if expected else "not empty"))

  def test_elif(self):
    parser = MextParser()
    res = parser.parse("""\
{@if false}
{@elif var1}
Pass
{@else}
Failed
{@endif}
""",
      params = {
        'var1': True,
    }, use_async=False)
    self.assertEqual(res, "Pass")

    res = parser.parse("""\
{@if false}
{@else}
Pass
{@elif var1}
Failed
{@endif}
""",
      params = {
        'var1': True,
    }, use_async=False)
    self.assertEqual(res, "Pass")

    res = parser.parse("""\
{@if false}
{@elif false}
Failed
{@elif true}
Pass
{@elif false}
Failed
{@else}
Failed
{@endif}
""", use_async=False)
    self.assertEqual(res, "Pass")

  def test_for(self):
    parser = MextParser()
    res = parser.parse("""\
List of fruits:
{@for item in arr}
- {item}
{@endfor}
Purchase them in the store.
""",
      params={
        'arr': ["Apple", "Banana", "Pear"],
    }, use_async=False)
    self.assertEqual(res, """\
List of fruits:
- Apple
- Banana
- Pear
Purchase them in the store.\
""")

    res = parser.parse("""\
{@for item in dict.items}
{item[0]}: {item[1]}
{@endfor}
""",
      params={
        'dict': {
          "name": "Alice",
          "favorite": "Apple",
          "Age": 19,
        },
    }, use_async=False)
    self.assertEqual(res, """\
name: Alice
favorite: Apple
Age: 19\
""")

    res = parser.parse("""\
Two
{@if false}
{@endif}
{@if false}
{@endif}
{@if true}
awesome
{@endif}
lines
""", use_async=False)
    self.assertEqual(res, """\
Two
awesome
lines\
""")

    parser.reset()
    parser.enable_trace(True)
    res = parser.parse("""\
{@for item in arr}
{@if item[pass]}
- {@for v in item.items}{v[0]}: {v[1]}
  {@endfor}
{@endif}
{@endfor}
""",
      params={
        'arr': [
          { 'name': "Alice", 'pass': True, },
          { 'name': "Bob", 'pass': False, },
          { 'name': "Alex", 'pass': True, },
        ],
    }, use_async=False)
    self.assertEqual(res, """\
- name: Alice
  pass: True
- name: Alex
  pass: True\
""")

  def test_trim_newline(self):
    parser = MextParser()
    res = parser.parse("""\
Start.

{@trim_newline}{@if true}{@endif}

End.
""", use_async=False)
    self.assertEqual(res, """\
Start.

End.\
""")

    res = parser.parse("""\
Start.

{@if true}
Some text.
{@endif}

End.
""", use_async=False)
    self.assertEqual(res, """\
Start.

Some text.

End.\
""")

    res = parser.parse("""\
Start.

{@trim_newline}{@if false}
Failed
{@endif}

End.
""", use_async=False)
    self.assertEqual(res, """\
Start.

End.\
""")

    res = parser.parse("""\
Start.

{@trim_newline}{@include prompts.empty_template}

End.
""",
      params={
        'prompts': self.prompts,
    }, use_async=False)
    self.assertEqual(res, """\
Start.

End.\
""")

    res = parser.parse("""\
Start.

{@trim_newline}{@include prompts.template1}

End.
""",
      params={
        'prompts': self.prompts,
    }, use_async=False)
    self.assertEqual(res, """\
Start.

Using default value.

End.\
""")

  def test_format(self):
    parser = MextParser()
    res = parser.parse("""\
{@format json var1}
""",
      params={
        'var1': [
          { 'name': "Alice", 'favorite': "Apple", },
          { 'name': "Bob", 'favorite': "Banana", },
        ],
    }, use_async=False)
    self.assertEqual(res, """\
[
  {
    "name": "Alice",
    "favorite": "Apple"
  },
  {
    "name": "Bob",
    "favorite": "Banana"
  }
]\
""")

  def test_if_whitespaces(self):
    parser = MextParser()
    res = parser.parse("""\
{@if true}
{val_pass}
{@endif}
""", {
      'var_true': True,
      'val_pass': "Pass",
    }, use_async=False)
    self.assertEqual(res, "Pass")

    res = parser.parse("""\
Is
{@if true}
{val_pass}
{@endif}
""", {
      'var_true': True,
      'val_pass': "Pass",
    }, use_async=False)
    self.assertEqual(res, "Is\nPass")

    res = parser.parse("""\
Is {@if true}
{val_pass}
{@endif}
""", {
      'var_true': True,
      'val_pass': "Pass",
    }, use_async=False)
    self.assertEqual(res, "Is \nPass")

    res = parser.parse("""\
Is {@if not var_true}
Failed
{@else}{@if false}
Nested Failed
  {@else}{val_pass}
  {@endif}
{@endif}
""", {
      'var_true': True,
      'val_pass': "Pass",
    }, use_async=False)
    self.assertEqual(res, "Is Pass")

    res = parser.parse("""\
Is{@if not var_true}
Failed
{@else}
  {@if false}
Nested Failed
  {@else}{val_pass}
  {@endif}
{@endif}
""", {
      'var_true': True,
      'val_pass': "Pass",
    }, use_async=False)
    self.assertEqual(res, "Is\n  Pass")

    res = parser.parse("""\
Is{@if not var_true}
Failed
{@else}
  {@if false}Nested Failed
  {@else}{val_pass}
  {@endif}
{@endif}
""", {
      'var_true': True,
      'val_pass': "Pass",
    }, use_async=False)
    self.assertEqual(res, "Is\n  Pass")

    res = parser.parse("""\
Is{@if not var_true}
Failed
{@else}
  {@if false}Nested Failed{@else}
  {val_pass}
  {@endif}
{@endif}
""", {
      'var_true': True,
      'val_pass': "Pass",
    }, use_async=False)
    self.assertEqual(res, "Is\n  Pass")

    res = parser.parse("""\
Is {@if not var_true}
Failed
{@else}{@if false}
Nested Failed{@else}{val_pass}
  {@endif}
{@endif}
""", {
      'var_true': True,
      'val_pass': "Pass",
    }, use_async=False)
    self.assertEqual(res, "Is Pass")

    res = parser.parse("""\
Is {@if not var_true}
Failed
{@else}{@if false}Nested Failed{@else}{val_pass}{@endif}
{@endif}
""", {
      'var_true': True,
      'val_pass': "Pass",
    }, use_async=False)
    self.assertEqual(res, "Is Pass")

    res = parser.parse("""\
Is{@if not var_true}
Failed
{@else}{@if false}
  Nested Failed
  {@else}
  {val_pass}
  {@endif}
{@endif}
""", {
      'var_true': True,
      'val_pass': "Pass",
    }, use_async=False)
    self.assertEqual(res, "Is\n  Pass")

    res = parser.parse("""\
Is{@if not var_true}
Failed
{@else}
  {@if false}
    Nested Failed
  {@else}
    {val_pass}
  {@endif}
{@endif}
""", {
      'var_true': True,
      'val_pass': "Pass",
    }, use_async=False)
    self.assertEqual(res, "Is\n    Pass")

    res = parser.parse("""\
Is{@if not var_true}
Failed
{@else}
  {@if false}Nested Failed{@else}{val_pass}{@endif}
{@endif}
""", {
      'var_true': True,
      'val_pass': "\nPass",
    }, use_async=False)
    self.assertEqual(res, "Is\n  \nPass")

  def test_clauses_whitespaces(self):
    parser = MextParser()
    res = parser.parse("""\
Include an empty template:
{@if false}
{@include prompts.empty_template}
{@endif}
End of the empty template.
""", params={
      'prompts': self.prompts,
    }, use_async=False)
    self.assertEqual(res, """\
Include an empty template:
End of the empty template.\
""")

    res = parser.parse("""\
Include an empty template:
{@if true}
{@endif}
End of the empty template.
""", params={
      'prompts': self.prompts,
    }, use_async=False)
    self.assertEqual(res, """\
Include an empty template:
End of the empty template.\
""")

    res = parser.parse("""\
Include an empty template:
{@if true}
{@include prompts.empty_template}
{@endif}
End of the empty template.
""", params={
      'prompts': self.prompts,
    }, use_async=False)
    self.assertEqual(res, """\
Include an empty template:
End of the empty template.\
""")
