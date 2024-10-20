# Copyright (C) 2024 Mext-lang team
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import re
import json
from os import path
from string import Formatter
from contextlib import contextmanager
from typing import Union, Tuple, Coroutine, Callable

from mext.libs.config_loader import CFG
from mext.libs.utils import format_exception, indent_lines, fence_content
from mext.libs.utils import ObjDict

class MextParser:
  Keywords = [
    'option',
    'set',
    'default',
    'count',
    'include',
    'input',
    'import',
    'if',
    'else',
    'elif',
    'endif',
    'for',
    'endfor',
    'trim_newline',
    'format',
    'comment',
    'endcomment',
  ]
  IncLevel = [
    'if',
    'for',
  ]
  DescLevel = [
    'endif',
    'endfor',
  ]

  Constants = {
    'true': True,
    'false': False,
    'none': None,
  }

  RegExps = ObjDict({
    'string': (regexp_string := r'(?:[^\"\\]|\\.)*'),
    'variable': (regexp_variable := r'[0-9a-zA-Z_\-\.\[\]]+'),
    'integer': (regexp_integer := r'[-+]?\d+'),
    'float': (regexp_float := r'[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?'),
    'number': (regexp_number := fr'(?:{regexp_integer}|{regexp_float})'),
    'quoted_string': (regexp_quoted_string := fr'"{regexp_string}"'),
    'value': (regexp_value := fr'(?:{regexp_quoted_string}|{regexp_number}|{regexp_variable})'),
  })

  def __init__(self):
    self.reset()

    self.formatters = {}
    default_formattters = {
      'json': MextParser.format_json,
      'repr': repr,
      'escape': MextParser.format_escape,
      'fenced_block': fence_content,
      'lower': str.lower,
      'upper': str.upper,
      'capitalize': str.capitalize,
    }
    for format_name, formatter in default_formattters.items():
      self.register_formatter(format_name, formatter)

    self.debug_trace = False

  def reset(self):
    self.template = None
    self.template_fn = None
    self.entries = None
    self.pos_index = -1
    self.str_formatter = Formatter()

    self.state = ObjDict()
    self.linenumbers = [1]
    self.level = 0
    self.pending_whitespaces = None

    self.params = {}
    self.callbacks = {}
    self.template_loader = self.load_template_file
    self.locals = {}

    self.options = {
      'final_strip': True,
    }
    self.for_context = []
    self.trim_newline_state = []
    self.results = []
    self.input_results = {}

  def register_formatter(self, format_name, formatter):
    self.formatters[format_name] = formatter

  def remove_formatter(self, format_name):
    del self.formatters[format_name]

  def enable_trace(self, enable):
    if enable:
      assert len(self.results) == 0
    self.debug_trace = enable
    if self.debug_trace:
      self.trace = []
    elif hasattr(self, 'trace'):
      del self.trace

  @property
  def all_variables(self):
    return {
      **MextParser.Constants,
      **self.params,
      **self.locals,
    }

  def load_template_file(self, fn):
    with open(fn, 'r') as f:
      lines = f.readlines()
      return ''.join(lines)

  def set_template(self, template=None, template_fn=None):
    if template is None:
      if template_fn is not None:
        template = self.template_loader(template_fn)
      else:
        raise ValueError('One of "template" or "template_fn" must not be None.')

    self.reset()

    self.template = template
    self.template_fn = template_fn
    entries = self.str_formatter.parse(self.template)
    self.entries = list(entries)

  def next_component(self):
    while self.pos_index+1 < len(self.entries):
      self.pos_index += 1
      literal_text, field_name, format_spec, conversion = self.entries[self.pos_index]

      keyword = None
      statement = field_name
      if field_name is not None and field_name.startswith("@"):
        parts = field_name[1:].split(' ', 1)
        keyword = parts[0]
        statement = parts[1].strip() if len(parts) > 1 else None

      self.linenumbers.append(self.linenumbers[-1] + literal_text.count('\n'))
      self.state.update({
        'literal_text': literal_text,
        'field_name': field_name,
        'format_spec': format_spec,
        'conversion': conversion,
        'keyword': keyword,
        'statement': statement,
      })

      yield self.state

  def seek(self, to_pos=None, delta=None):
    if to_pos is not None:
      delta = to_pos - self.pos_index
    if delta is not None:
      if delta > 0:
        raise ValueError('Cannot seek forward.')
      self.pos_index += delta
      self.linenumbers = self.linenumbers[:delta]
    else:
      raise ValueError('One of "to_pos" or "delta" must not be None.')

  def append_text(self, text, flush_pending=True):
    text = str(text)
    if len(text) > 0:
      if flush_pending and self.pending_whitespaces is not None:
        if len(self.pending_whitespaces) != 0:
          self.results.append(self.pending_whitespaces)
        self.pending_whitespaces = None
      self.results.append(str(text))
      if self.debug_trace:
        self.trace.append((self.pos_index, self.state.copy()))

  @property
  def parsed_result(self):
    parsed_result = ''.join(self.results)
    if self.options['final_strip']:
      parsed_result = parsed_result.strip()
    return parsed_result

  def skip_until(self, target_keywords=[], inc_level=[], desc_level=[]):
    target_level = self.level
    for state in self.next_component():
      if state.keyword in inc_level:
        self.level += 1
      elif state.keyword in desc_level:
        self.level -= 1
        if self.level == target_level-1 and state.keyword in target_keywords:
          return
      elif self.level == target_level and state.keyword in target_keywords:
        return

  def raise_error(self, error_type, msg):
    error_msg = ""
    if self.template_fn is not None:
      error_msg += f'In file "{self.template_fn}", line {self.linenumbers[-1]}, around "{self.state.field_name}".'
    else:
      error_msg += f'Line {self.linenumbers[-1]}, around "{self.state.field_name}".'
    error_msg += f'\n{indent_lines(msg, indent=2)}'
    raise error_type(error_msg)

  def raise_syntax_error(self, msg):
    self.raise_error(SyntaxError, msg)

  def assert_missing_statement(self):
    if self.state.statement is None:
      self.raise_syntax_error(f"Missing statement after {self.state.keyword}")

  def assert_unexpected_statement(self):
    if self.state.statement is not None:
      self.raise_syntax_error(f"Unexpected statement after {self.state.keyword}")

  def get_field_value(self, field_name):
    reg = MextParser.RegExps
    if re.match(fr'^{reg.integer}$', field_name):
      return int(field_name)
    if re.match(fr'^{reg.float}$', field_name):
      return float(field_name)
    if re.match(fr'^{reg.quoted_string}$', field_name):
      return str(field_name[1:-1])
    try:
      field_value, _ = self.str_formatter.get_field(field_name, args=[], kwargs=self.all_variables)
    except Exception as e:
      self.raise_error(RuntimeError, format_exception(e))
    return field_value

  def parse(self, template=None, params={}, callbacks={}, template_fn=None, template_loader=None):
    self.set_template(template=template, template_fn=template_fn) # this will reset all state
    if template_loader is not None:
      self.template_loader = template_loader
    self.params = params
    self.callbacks = callbacks

    for state in self.next_component():
      self.process_literal()

      if state.keyword is not None:
        if state.keyword not in self.Keywords:
          self.raise_syntax_error(f'"{state.keyword}" is not a valid keyword.')
        if state.keyword in self.IncLevel:
          self.level += 1
        elif state.keyword in self.DescLevel:
          self.level -= 1

        parse_fn = getattr(self, f"parse_{state.keyword}")
        parse_fn()
      elif state.field_name is not None:
        self.parse_field()

    return self.parsed_result

  def process_literal(self):
    whitespaces = r'[ \t]'

    text: str = self.state.literal_text
    pending_whitespaces = None

    if self.pending_whitespaces is not None:
      if (m := re.search(fr'\A{whitespaces}*\n', text)) is not None:
        text = text[len(m[0]):]
        self.pending_whitespaces = re.sub(fr'{whitespaces}*\Z', '', self.pending_whitespaces)
        if self.pending_whitespaces.endswith('\n'):
          text = '\n' + text
          self.pending_whitespaces = self.pending_whitespaces[:-1]

    if len(self.trim_newline_state) > 0:
      if len(text) > 0:
        # activate upon non empty literal text (that is at the same level)
        last_state = self.trim_newline_state[-1]
        while last_state.level >= self.level:
          if last_state.level == self.level:
            if last_state.pos_mark == len(self.results):
              # if the block after '@trim_newline' produces empty,
              # trim the new lines after the block
              text = re.sub(r'\A\n*', '', text)
              if len(text) == 0:
                # continue to trim new lines
                break
          self.trim_newline_state.pop()
          if len(self.trim_newline_state) == 0:
            break
          last_state = self.trim_newline_state[-1]

    if self.pos_index != 0 and len(text) == 0:
      pending_whitespaces = self.pending_whitespaces
      self.pending_whitespaces = None
    elif self.state.field_name is not None and ((m := re.search(fr'\n{whitespaces}*\Z', text))
          or ((self.pos_index == 0 or self.pending_whitespaces == '') and (m := re.fullmatch(fr'{whitespaces}*', text)))):
      text = text[:-len(m[0])]
      pending_whitespaces = m[0]

    self.append_text(text)
    self.pending_whitespaces = pending_whitespaces

  def parse_option(self):
    self.assert_missing_statement()

    parts = self.state.statement.split(' ', 1)
    if len(parts) != 2:
      self.raise_syntax_error('Keyword "option" requries "@option option_name (on|off)" syntax.')

    opt_name = parts[0]
    val = parts[1]
    if val == "on":
      val = True
    elif val == "off":
      val = False
    else:
      self.raise_syntax_error('The second parameter for keyword "option" should be "on" or "off".')

    self.options[opt_name] = val

  def parse_set(self):
    self.assert_missing_statement()

    parts = self.state.statement.split(' ', 1)
    if len(parts) != 2:
      self.raise_syntax_error('Keyword "set" requires exactly two variables.')

    var1_name = parts[0]
    var2_name = parts[1]
    var2_val = self.get_field_value(var2_name)
    self.locals[var1_name] = var2_val

  def parse_default(self):
    self.assert_missing_statement()

    parts = self.state.statement.split(' ', 1)
    if len(parts) != 2:
      self.raise_syntax_error('Keyword "default" requires exactly two variables.')

    var1_name = parts[0]
    var2_name = parts[1]
    if var1_name not in self.all_variables:
      var2_val = self.get_field_value(var2_name)
      self.locals[var1_name] = var2_val

  def parse_count(self):
    self.assert_missing_statement()

    varname = self.state.statement
    try:
      varvalue = self.get_field_value(varname)
      varvalue += 1
    except Exception:
      varvalue = 0

    self.locals[varname] = varvalue

  def parse_include(self):
    self.assert_missing_statement()
    statement = self.state.statement

    reg = MextParser.RegExps
    parts = re.match(fr'^(?:\"(?P<filepath>{reg.string})\"|(?P<filepath_var>{reg.variable}))(?:\s+(?P<params>(?:{reg.variable}\s*=\s*{reg.variable})(?:,\s*{reg.variable}\s*=\s*{reg.variable})*))?$', statement)
    if parts is None:
      self.raise_syntax_error(f'Keyword "include" requries \'@include ("filename"|filename_variable) [param=var,...]\' syntax.')

    nested_template_fn = None
    if parts['filepath'] is not None:
      nested_template_fn = parts['filepath']
    elif parts['filepath_var'] is not None:
      nested_template_fn_var = parts['filepath_var']
      nested_template_fn = self.get_field_value(nested_template_fn_var)
    else:
      self.raise_error(RuntimeError, "Failed to identify include target.")

    if nested_template_fn is None:
      self.raise_error(RuntimeError, f'Filepath cannot be None.')
    nested_template_fn = str(nested_template_fn)
    ogn_nested_fn = nested_template_fn
    if not path.exists(nested_template_fn):
      file_found = False
      if not nested_template_fn.endswith('.mext') and path.exists(nested_template_fn+'.mext'):
          nested_template_fn += '.mext'
          file_found = True
      if not file_found and self.template_fn is not None:
        nested_template_fn = path.join(path.dirname(self.template_fn), nested_template_fn)
        if path.exists(nested_template_fn):
          file_found = True
        else:
          if not nested_template_fn.endswith('.mext') and path.exists(nested_template_fn+'.mext'):
            nested_template_fn += '.mext'
            file_found = True
      if not file_found:
        self.raise_error(FileNotFoundError, f'File not found: "{ogn_nested_fn}".')

    additional_params = {}
    if parts['params'] is not None:
      clauses = parts['params'].split(',')
      clauses = map(lambda p: (v.strip() for v in p.split('=', 1)), clauses)
      for key, val in clauses:
        additional_params[key] = self.get_field_value(val)

    try:
      nested_template = self.template_loader(nested_template_fn)
    except Exception as e:
      self.raise_error(RuntimeError, f'Failed to include file "{parts["filepath"]}".\n{format_exception(e)}')

    params = {
      **self.params,
      **additional_params,
    }

    nested_parser = MextParser()
    nested_result = nested_parser.parse(
      template=nested_template,
      template_fn=nested_template_fn,
      params=params,
      callbacks=self.callbacks,
      template_loader=self.template_loader,
    )
    self.append_text(nested_result)

  def parse_input(self):
    self.assert_missing_statement()

    varname = self.state.statement
    if varname not in self.callbacks:
      self.raise_error(RuntimeError, f'Missing callback for input variable "{varname}".')
    input_val = self.callbacks[varname](self.parsed_result)

    self.append_text(input_val)
    self.locals[varname] = input_val
    self.input_results[varname] = input_val

  def parse_import(self):
    self.assert_missing_statement()
    statement = self.state.statement

    reg = MextParser.RegExps
    parts = re.match(fr'^(?:\"(?P<filepath>{reg.string})\"|(?P<filepath_var>{reg.variable}))(?:\s+as\s+(?P<namespace>{reg.variable}))?$', statement)
    if parts is None:
      self.raise_syntax_error(f'Keyword "import" requries \'@import ("filename"|filename_variable) [as varname]\' syntax.')

    import_fn = None
    if parts['filepath'] is not None:
      import_fn = parts['filepath']
    elif parts['filepath_var'] is not None:
      import_fn_var = parts['filepath_var']
      import_fn = self.get_field_value(import_fn_var)
    else:
      self.raise_error(RuntimeError, "Failed to identify import target.")

    if import_fn is None:
      self.raise_error(RuntimeError, f'Filepath cannot be None.')
    import_fn = str(import_fn)
    if not path.exists(import_fn):
      file_found = False
      if self.template_fn is not None:
        import_fn = path.join(path.dirname(self.template_fn), import_fn)
        if path.exists(import_fn):
          file_found = True
      if not file_found:
        self.raise_error(FileNotFoundError, f'File not found: "{parts["filepath"] or import_fn}".')

    varname = parts['namespace']

    if path.splitext(import_fn)[1] in CFG.supported_extensions:
      try:
        imported_vars = CFG.load_config(import_fn)
        imported_vars = ObjDict.convert_recursively(imported_vars)
        if imported_vars is None:
          imported_vars = {}

        if varname is None:
          self.locals.update(imported_vars)
        else:
          self.locals[varname] = imported_vars
      except Exception as e:
        self.raise_error(RuntimeError, f'Failed to import file "{parts["filepath"]}".\n{format_exception(e)}')
    else:
      if varname is None:
        self.raise_syntax_error(f'Trying to import file "{parts["filepath"]}" as text but missing the as clause. Usage: \'@import "text_file" as varname\'.')

      try:
        with open(import_fn, 'r') as f:
          lines = f.readlines()
          imported_content = ''.join(lines)
          self.locals[varname] = imported_content
      except Exception as e:
        self.raise_error(RuntimeError, f'Failed to import file "{parts["filepath"]}".\n{format_exception(e)}')

  def test_statement(self, statement):
    reg = MextParser.RegExps
    parts = re.match(fr'(?P<operators>(not\s+)?((?:empty|undefined|novalue)\s+)?)(?P<varname>{reg.variable})', statement)
    if parts is None:
      self.raise_syntax_error(f'Keyword "if" requires "@if [not] [empty|undefined|novalue] varname" syntax.')

    operators = parts['operators']
    operators = re.split(r'\s+', operators)
    inverse = 'not' in operators
    test_empty = 'empty' in operators
    test_undefined = 'undefined' in operators
    test_novalue = 'novalue' in operators

    field_name = parts['varname']
    eval_result = None
    field_value = None

    if test_undefined or test_novalue:
      try:
        field_value = self.get_field_value(field_name)
        if test_undefined:
          eval_result = False
      except RuntimeError as e:
        eval_result = True
    else:
      field_value = self.get_field_value(field_name)

    if eval_result is None and (test_empty or test_novalue):
      if field_value is None:
        eval_result = True
      elif hasattr(field_value, '__len__'):
        eval_result = len(field_value) == 0
      else:
        eval_result = False

    if eval_result is None:
      eval_result = bool(field_value)

    if inverse:
      eval_result = not eval_result

    return eval_result

  def parse_if(self):
    self.assert_missing_statement()
    statement = self.state.statement

    eval_result = self.test_statement(statement)
    if not eval_result:
      self.skip_until(['else', 'elif', 'endif'], ['if'], ['endif'])
      if self.state.keyword == 'elif':
        return self.parse_if()
    else:
      return

  def parse_elif(self):
    self.skip_until(['endif'], ['if'], ['endif'])

  def parse_else(self):
    self.assert_unexpected_statement()

    self.skip_until(['endif'], ['if'], ['endif'])

  def parse_endif(self):
    self.assert_unexpected_statement()

  def parse_for(self):
    self.assert_missing_statement()
    statement = self.state.statement

    reg = MextParser.RegExps
    parts = re.match(fr'(?P<varnames>{reg.variable}(,\s*{reg.variable})*)\s+in\s+(?P<iterable_name>{reg.variable})', statement)
    if parts is None:
      self.raise_syntax_error('Keyword "for" requires "@for item in iterable" syntax.')

    varnames = parts['varnames']
    varnames = list(map(lambda x: x.strip(), varnames.split(',')))
    iterable_name = parts['iterable_name']

    try:
      iterable = self.get_field_value(iterable_name)
      if isinstance(iterable, dict):
        itr = iter(iterable.items())
      else:
        itr = iter(iterable)
    except TypeError:
      self.raise_error(RuntimeError, f'"{iterable_name}" is not an iterable.')

    try:
      current_value = next(itr)
      context = ObjDict({
        'varnames': varnames,
        'current_value': current_value,
        'itr': itr,
        'index': 0,
        'entry_mark': self.pos_index,
      })
      self.for_context.append(context)
      if len(varnames) == 1:
        self.locals[varnames[0]] = current_value
      else:
        _ = iter(current_value)
        for varname,value in zip(varnames, current_value):
          self.locals[varname] = value
    except StopIteration:
      self.skip_until(['endfor'], ['for'], ['endfor'])

  def parse_endfor(self):
    self.assert_unexpected_statement()

    if len(self.for_context) == 0:
      self.raise_syntax_error(f'Rebundant keyword "endfor".')

    try:
      context = self.for_context[-1]
      varnames = context.varnames
      current_value = next(context.itr)
      context.update({
        'current_value': current_value,
        'index': context.index+1,
      })
      if len(varnames) == 1:
        self.locals[varnames[0]] = current_value
      else:
        _ = iter(current_value)
        for varname,value in zip(varnames, current_value):
          self.locals[varname] = value
      self.seek(to_pos=context.entry_mark)
    except StopIteration:
      self.for_context.pop()

  def parse_trim_newline(self):
    self.assert_unexpected_statement()

    if self.pending_whitespaces is None:
      self.pending_whitespaces = ''
    elif (m := re.match(r'\A\n*', self.pending_whitespaces)) is not None:
      self.append_text(m[0], flush_pending=False)
      self.pending_whitespaces = self.pending_whitespaces[len(m[0]):]

    self.trim_newline_state.append(ObjDict({
      'level': self.level,
      'pos_mark': len(self.results),
    }))

  def parse_format(self):
    self.assert_missing_statement()
    statement = self.state.statement

    reg = MextParser.RegExps
    parts = re.match(fr'^(?P<format>{reg.string})\s+(?P<varname>{reg.variable})(?:\s+(?P<params>(?:{reg.variable}\s*=\s*{reg.value})(?:,\s*{reg.variable}\s*=\s*{reg.value})*))?$', statement)
    if parts is None:
      self.raise_syntax_error(f'Keyword "format" requries \'@format "format" variable [param=var,...]\' syntax.')

    format = parts['format']
    field_name = parts['varname']
    field_value = self.get_field_value(field_name)

    if format not in self.formatters:
      self.raise_error(RuntimeError, f'Format "{format}" is not registered.')

    formatter_params = {}
    if parts['params'] is not None:
      clauses = parts['params'].split(',')
      formatter_params = { k.strip(): v.strip() for k, v in map(lambda p: p.split('=', 1), clauses) }
      for k, v in formatter_params.items():
        formatter_params[k] = self.get_field_value(v)

    format_res = self.formatters[format](field_value, **formatter_params)
    self.append_text(format_res)

  def parse_comment(self):
    self.assert_unexpected_statement()

    self.skip_until(['endcomment'], ['comment'], ['endcomment'])

  def parse_endcomment(self):
    self.assert_unexpected_statement()

    self.raise_syntax_error(f'Rebundant keyword "endcomment".')

  def parse_field(self):
    field_value = self.get_field_value(self.state.field_name)
    field_value = self.str_formatter.convert_field(field_value, self.state.conversion)
    field_value = self.str_formatter.format_field(field_value, self.state.format_spec)
    self.append_text(field_value)

  @classmethod
  def format_json(self, value):
    return json.dumps(value, indent=2, ensure_ascii=False)

  @classmethod
  def format_escape(self, value: str, esc_chars: str="\\n"):
    value = str(value)
    esc_chars = esc_chars.encode().decode('unicode_escape')
    esc_chars = set(esc_chars)

    if '\\' in esc_chars:
      esc_chars.remove('\\')
      esc_chars = ['\\'] + list(esc_chars)
    for char in esc_chars:
      escaped_chr = char.encode('unicode_escape').decode()
      if escaped_chr == char:
        escaped_chr = '\\' + char
      value = value.replace(char, escaped_chr)
    return value
