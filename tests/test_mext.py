import unittest
import os
from os import path

from mext.libs.utils import ObjDict
from mext import MextParser

class TestMextParser(unittest.TestCase):
  dirs = ObjDict({
    'prompts': "tests/mext/prompts",
    'data': "tests/mext/data",
    'readme': "tests/mext/readme",
  })

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    def add_prefix(prefix, _dict: dict):
      return {k:path.join(prefix, v) for k,v in _dict.items()}

    self.prompts = ObjDict(add_prefix(self.dirs.prompts, {
      'empty_template': "empty.mext",
      'template1': "include1.mext",
    }))
    self.data = ObjDict(add_prefix(self.dirs.data, {
      'data1': 'data1.yaml',
    }))

  def test_var(self):
    parser = MextParser()
    res = parser.parse("""{var}""", params={
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

Empty line above.""", params={
      'var': "",
    }, use_async=False)
    self.assertEqual(res, "\nEmpty line above.")

    parser = MextParser()
    res = parser.parse("""\
{@option final_strip off}
{var}
No empty line above.""", params={
      'var': "",
    }, use_async=False)
    self.assertEqual(res, "No empty line above.")

  def test_set(self):
    parser = MextParser()
    res = parser.parse("""\
{var1}
{@set var1 var2}
{var1}""", params={
      'var1': "Val1",
      'var2': "Val2",
    }, use_async=False)
    self.assertEqual(res, "Val1\nVal2")

  def test_default(self):
    parser = MextParser()
    res = parser.parse("""\
{@default var1 var2}
{var1}""", params={
      'var2': "Val2",
    }, use_async=False)
    self.assertEqual(res, "Val2")

    res = parser.parse("""\
{@default var1 var2}
{var1}""", params={
      'var1': "Val1",
      'var2': "Val2",
    }, use_async=False)
    self.assertEqual(res, "Val1")

  def test_count(self):
    parser = MextParser()
    res = parser.parse("""\
{@option final_strip off}
{@count idx}
{idx}\
""", use_async=False)
    self.assertEqual(res, "0")

    res = parser.parse("""\
{@for item in arr}
{@count idx}
{idx}. {item}
{@endfor}\
""", params={
      'arr': [0, 1, 2, 3],
    }, use_async=False)
    self.assertEqual(res, """\
0. 0
1. 1
2. 2
3. 3\
""")

    res = parser.parse("""\
{@set idx 0}
{@for item in arr}
{@count idx}
{idx}. {item}
{@endfor}\
""", params={
      'arr': [1, 2, 3, 4],
    }, use_async=False)
    self.assertEqual(res, """\
1. 1
2. 2
3. 3
4. 4\
""")

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
{@include prompts.template1 var1 = false}
""", params={
      'prompts': self.prompts,
    }, use_async=False)
    self.assertEqual(res, "Included from template1:\nUsing additional parameter value.")

    res = parser.parse("""\
Included from template1:
{@include prompts.template1 var1 = false, var2=true}
""", params={
      'prompts': self.prompts,
    }, use_async=False)
    self.assertEqual(res, "Included from template1:\nUsing additional parameter value.\nAnother variable var2 is True.")

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

  def test_import(self):
    parser = MextParser()
    res = parser.parse("""\
{@import data.data1}
name: {name}
age: {age}
""", params={
      'data': self.data,
    }, use_async=False)
    self.assertEqual(res, """\
name: Alice
age: 19\
""")

    res = parser.parse("""\
{@import data.data1 as agent}
name: {agent[name]}
age: {agent[age]}
""", params={
      'data': self.data,
    }, use_async=False)
    self.assertEqual(res, """\
name: Alice
age: 19\
""")

    res = parser.parse("""\
{@import data.data1 as agent}
name: {agent.name}
age: {agent.age}
""", params={
      'data': self.data,
    }, use_async=False)
    self.assertEqual(res, """\
name: Alice
age: 19\
""")

    res = parser.parse("""\
{@import "tests/mext/data/data1.yaml"}
name: {name}
age: {age}
""", use_async=False)
    self.assertEqual(res, """\
name: Alice
age: 19\
""")

    res = parser.parse("""\
{@import "tests/mext/data/data1.yaml" as agent}
name: {agent.name}
age: {agent.age}
""", use_async=False)
    self.assertEqual(res, """\
name: Alice
age: 19\
""")

  def test_if(self):
    parser = MextParser()
    res = parser.parse("""{@if true}True{@else}False{@endif}""", use_async=False)
    self.assertEqual(res, "True")

    res = parser.parse("""{@if false}True{@else}False{@endif}""", use_async=False)
    self.assertEqual(res, "False")

    res = parser.parse("""{@if var_true}True{@else}False{@endif}""", params={
      'var_true': True,
    }, use_async=False)
    self.assertEqual(res, "True")

    res = parser.parse("""{@if var_true}{val_pass}{@else}Failed{@endif}""", params={
      'var_true': True,
      'val_pass': "Pass",
    }, use_async=False)
    self.assertEqual(res, "Pass")

    res = parser.parse("""{@if var_false}Failed{@else}{val_pass}{@endif}""", params={
      'var_false': False,
      'val_pass': "Pass",
    }, use_async=False)
    self.assertEqual(res, "Pass")

    res = parser.parse("""{@if not var_true}Failed{@else}{val_pass}{@endif}""", params={
      'var_true': True,
      'val_pass': "Pass",
    }, use_async=False)
    self.assertEqual(res, "Pass")

    res = parser.parse("""{@if not var_true}Failed{@else}{@if false}Nested Failed{@else}{val_pass}{@endif}{@endif}""", params={
      'var_true': True,
      'val_pass': "Pass",
    }, use_async=False)
    self.assertEqual(res, "Pass")

  def test_if_operators(self):
    parser = MextParser()
    cases = [
      ({}, True),
      ({ 'var': [] }, False),
      ({ 'var': None }, False),
    ]
    for params, expected in cases:
      res = parser.parse("""var is {@if undefined var}undefined{@else}not undefined{@endif}""", params=params, use_async=False)
      self.assertEqual(res, f'var is ' + ("undefined" if expected else "not undefined"))

      res = parser.parse("""var is {@if not undefined var}not undefined{@else}undefined{@endif}""", params=params, use_async=False)
      self.assertEqual(res, f'var is ' + ("undefined" if expected else "not undefined"))

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
      res = parser.parse(""""{var}" is {@if empty var}empty{@else}not empty{@endif}""", params={
        'var': var,
      }, use_async=False)
      self.assertEqual(res, f'"{var}" is ' + ("empty" if expected else "not empty"))

      res = parser.parse(""""{var}" is {@if not empty var}not empty{@else}empty{@endif}""", params={
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
{@for k, v in dict}
{k}: {v}
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
{@for vs in arr}
{@for v in vs}
{v}
{@endfor}
{@endfor}
""",
      params={
        'arr': [],
    }, use_async=False)
    self.assertEqual(res, "")

    parser.reset()
    parser.enable_trace(True)
    res = parser.parse("""\
{@for item in arr}
{@if item[pass]}
- {@for k,v in item}{k}: {v}
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

    res = parser.parse("""\
Start.

{@trim_newline}{@include prompts.empty_template}

{@trim_newline}{@if true}{@endif}

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

{@if false}
{@else}
A line.
{@endif}

{@trim_newline}{@include prompts.empty_template}

End.
""",
      params={
        'prompts': self.prompts,
    }, use_async=False)
    self.assertEqual(res, """\
Start.

A line.

End.\
""")

  def test_format_json(self):
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

  def test_format_repr(self):
    parser = MextParser()
    res = parser.parse("""\
var1: {@format repr var1}
""",
      params={
        'var1': """\
This is a multi-line paragraph.
"Sentences like this should be escaped."
'And this one too.'\
""",
    }, use_async=False)
    self.assertEqual(res, """var1: 'This is a multi-line paragraph.\\n"Sentences like this should be escaped."\\n\\'And this one too.\\''""")

  def test_format_escape(self):
    parser = MextParser()
    res = parser.parse("""\
var1: {@format escape var1 esc_chars="\\n"}
""",
      params={
        'var1': """\
This is a multi-line paragraph.
"Sentences like this won't be escaped."
'And this one too.'\
""",
    }, use_async=False)
    self.assertEqual(res, """var1: This is a multi-line paragraph.\\n"Sentences like this won't be escaped."\\n'And this one too.'""")

    res = parser.parse("""\
|name|desc
|---|---
{@for name, desc in table}
|{name}|{@format escape desc esc_chars = "|\\n\\\\"}
""",
      params={
        'table': {
          'why': "This is useful for making tables,\none-liner || general escaping like \\.",
        },
    }, use_async=False)
    self.assertEqual(res, """\
|name|desc
|---|---
|why|This is useful for making tables,\\none-liner \|\| general escaping like \\\\.\
""")

  def test_comment(self):
    parser = MextParser()
    res = parser.parse("""\
Comment below.
{@comment}Here are some comments.{@endcomment}
{@if true}
Comment ended.
{@endif}
""", use_async=False)
    self.assertEqual(res, """\
Comment below.
Comment ended.\
""")

    res = parser.parse("""\
Comment below.
{@comment}
Here are some comments.
{@if true}
Just some more comments.
{@endif}
{@endcomment}
{@if true}
Comment ended.
{@endif}
""", use_async=False)
    self.assertEqual(res, """\
Comment below.
Comment ended.\
""")

  def test_if_whitespaces(self):
    parser = MextParser()
    res = parser.parse("""\
{@if true}
{val_pass}
{@endif}
""", params={
      'var_true': True,
      'val_pass': "Pass",
    }, use_async=False)
    self.assertEqual(res, "Pass")

    res = parser.parse("""\
Is
{@if true}
{val_pass}
{@endif}
""", params={
      'var_true': True,
      'val_pass': "Pass",
    }, use_async=False)
    self.assertEqual(res, "Is\nPass")

    res = parser.parse("""\
Is {@if true}
{val_pass}
{@endif}
""", params={
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
""", params={
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
""", params={
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
""", params={
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
""", params={
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
""", params={
      'var_true': True,
      'val_pass': "Pass",
    }, use_async=False)
    self.assertEqual(res, "Is Pass")

    res = parser.parse("""\
Is {@if not var_true}
Failed
{@else}{@if false}Nested Failed{@else}{val_pass}{@endif}
{@endif}
""", params={
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
""", params={
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
""", params={
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
""", params={
      'var_true': True,
      'val_pass': "\nPass",
    }, use_async=False)
    self.assertEqual(res, "Is\n  \nPass")

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

  def test_readme(self):
    parser = MextParser()
    readme_files = os.listdir(self.dirs.readme)
    readme_templates = filter(lambda x: x.endswith('.mext'), readme_files)
    for tp in readme_templates:
      template_fn = path.join(self.dirs.readme, tp)
      tp_base, tp_ext = path.splitext(tp)
      expected_fn = path.join(self.dirs.readme, f'{tp_base}.md')
      with open(expected_fn, 'r') as f:
        lines = f.readlines()
        expected_result = ''.join(lines)

      res = parser.parse(template_fn=template_fn, use_async=False)
      self.assertEqual(res, expected_result)
