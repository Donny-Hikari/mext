import re
import json
from string import Formatter
from typing import Union, Tuple, Coroutine, Awaitable, Callable
import asyncio
from contextlib import contextmanager

from autocode.libs.config_loader import CFG
from autocode.libs.utils import auto_async
from autocode.libs.utils import ObjDict

class MextParser:
  Keywords = [
    'option',
    'set',
    'default',
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

  def __init__(self):
    self.reset()

    self.formatters = {}
    default_formattters = {
      'json': MextParser.format_json,
    }
    for format_name, formatter in default_formattters.items():
      self.register_formatter(format_name, formatter)

    self.debug_trace = False

  def reset(self):
    self.template = None
    self.entries = None
    self.pos_index = -1
    self.str_formatter = Formatter()

    self.state = ObjDict()
    self.level = 0
    self.pending_whitespaces = None

    self.constants = {
      'true': True,
      'false': False,
    }
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
      **self.constants,
      **self.params,
      **self.locals,
    }

  def load_template_file(self, fn):
    with open(fn, 'r') as f:
      lines = f.readlines()
      return ''.join(lines)

  def set_template(self, template):
    self.reset()

    self.template = template
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
        statement = parts[1] if len(parts) > 1 else None
      self.state.update({
        'literal_text': literal_text,
        'field_name': field_name,
        'format_spec': format_spec,
        'conversion': conversion,
        'keyword': keyword,
        'statement': statement,
      })
      yield self.state

  def append_text(self, text, flush_pending=True):
    text = str(text)
    if len(text) > 0:
      if flush_pending and self.pending_whitespaces is not None:
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
    raise error_type(f'Around "{self.state.field_name}": {msg}')

  def raise_syntax_error(self, msg):
    self.raise_error(SyntaxError, msg)

  def assert_missing_statement(self):
    if self.state.statement is None:
      self.raise_syntax_error(f"Missing statement after {self.state.keyword}")

  def assert_unexpected_statement(self):
    if self.state.statement is not None:
      self.raise_syntax_error(f"Unexpected statement after {self.state.keyword}")

  async def get_field_value(self, field_name):
    if re.match(r'^[-+]?\d+$', field_name):
      return int(field_name)
    if re.match(r'^[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?$', field_name):
      return float(field_name)
    field_value, _ = self.str_formatter.get_field(field_name, args=[], kwargs=self.all_variables)
    if callable(field_value):
      field_value = field_value()
      if asyncio.iscoroutine(field_value):
        field_value = await field_value
    return field_value

  @auto_async
  async def parse(self, template, params={}, callbacks={}, template_loader=None):
    self.set_template(template)
    self.params = params
    self.callbacks = callbacks
    if template_loader is not None:
      self.template_loader = template_loader

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
        await parse_fn()
      elif state.field_name is not None:
        await self.parse_field()

    return self.parsed_result

  def process_literal(self):
    whitespaces = r'[ \t]'

    text: str = self.state.literal_text

    if self.pending_whitespaces is not None:
      if (m := re.search(fr'\A{whitespaces}*\n', text)) is not None:
        text = re.sub(fr'\A{whitespaces}*\n', '', text)
        self.pending_whitespaces = re.sub(fr'{whitespaces}*\Z', '', self.pending_whitespaces)
      if self.state.keyword not in [None] and re.fullmatch(fr'({whitespaces}|\n)*', text) is not None:
        pass
      else:
        self.append_text(self.pending_whitespaces, flush_pending=False)
      self.pending_whitespaces = None

    if self.state.keyword not in [None] and ((m := re.search(fr'\n{whitespaces}*\Z', text))
      or (self.pos_index == 0 and (m := re.fullmatch(fr'{whitespaces}*', text)))):
      text = re.sub(fr'\n{whitespaces}*\Z', '', text)
      self.pending_whitespaces = m[0]

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
              if self.pending_whitespaces is not None:
                self.pending_whitespaces = self.pending_whitespaces.strip('\n')
          self.trim_newline_state.pop()
          if len(self.trim_newline_state) == 0:
            break
          last_state = self.trim_newline_state[-1]

    self.append_text(text, flush_pending=False)

  async def parse_option(self):
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

  async def parse_set(self):
    self.assert_missing_statement()

    parts = self.state.statement.split(' ', 1)
    if len(parts) != 2:
      self.raise_syntax_error('Keyword "set" requires exactly two variables.')

    var1_name = parts[0]
    var2_name = parts[1]
    var2_val = await self.get_field_value(var2_name)
    self.locals[var1_name] = var2_val

  async def parse_default(self):
    self.assert_missing_statement()

    parts = self.state.statement.split(' ', 1)
    if len(parts) != 2:
      self.raise_syntax_error('Keyword "default" requires exactly two variables.')

    var1_name = parts[0]
    var2_name = parts[1]
    if var1_name not in self.all_variables:
      var2_val = await self.get_field_value(var2_name)
      self.locals[var1_name] = var2_val

  async def parse_include(self):
    self.assert_missing_statement()

    parts = self.state.statement.split(' ', 1)
    nested_template_fn_var = parts[0]
    additional_params = {}
    if len(parts) > 1:
      clauses = parts[1].split(',')
      clauses = map(lambda p: (v.strip() for v in p.split('=', 1)), clauses)
      for key, val in clauses:
        additional_params[key] = await self.get_field_value(val)

    nested_template_fn = await self.get_field_value(nested_template_fn_var)
    nested_template = self.template_loader(nested_template_fn)
    if asyncio.iscoroutine(nested_template):
      nested_template = await nested_template

    params = {
      **self.params,
      **additional_params,
    }

    nested_parser = MextParser()
    nested_result = await nested_parser.parse(
      template=nested_template,
      params=params,
      callbacks=self.callbacks,
      template_loader=self.template_loader,
    )
    self.append_text(nested_result)

  async def parse_input(self):
    self.assert_missing_statement()

    varname = self.state.statement
    if varname not in self.callbacks:
      self.raise_error(RuntimeError, f'Missing callback for input variable "{varname}".')
    input_val = self.callbacks[varname](self.parsed_result)
    if asyncio.iscoroutine(input_val):
      input_val = await input_val

    self.append_text(input_val)
    self.locals[varname] = input_val
    self.input_results[varname] = input_val

  async def parse_import(self):
    self.assert_missing_statement()
    statement = self.state.statement

    parts = statement.split(' ', 3)
    import_fn_var = parts[0]
    import_fn = await self.get_field_value(import_fn_var)
    if len(parts) == 1:
      namespace = self.locals
    elif len(parts) == 3 and parts[1] == 'as':
      varname = parts[2]
      namespace = self.locals[varname] = ObjDict({})
    else:
      self.raise_syntax_error(f'Keyword "import" requries "@import filename_variable [as varname]" syntax')

    imported_vars = CFG.load_config(import_fn)
    imported_vars = ObjDict.convert_recursively(imported_vars)
    namespace.update(imported_vars)

  async def parse_if(self):
    self.assert_missing_statement()
    statement = self.state.statement

    parts = statement.split(' ', 1)
    inverse = False
    if parts[0] == 'not':
      if len(parts) == 1:
        self.raise_syntax_error('Missing statement after keyword "not".')
      inverse = True
      statement = parts[1]

    parts = statement.split(' ', 1)
    test_empty = False
    if parts[0] == 'empty':
      if len(parts) == 1:
        self.raise_syntax_error('Missing statement after keyword "empty".')
      test_empty = True
      statement = parts[1]

    field_name = statement
    field_value = await self.get_field_value(field_name)
    if test_empty:
      if field_value is None:
        field_value = True
      elif hasattr(field_value, '__len__'):
        field_value = len(field_value) == 0
      else:
        field_value = False
    if inverse:
      field_value = not field_value
    if not field_value:
      self.skip_until(['else', 'elif', 'endif'], ['if'], ['endif'])
      if self.state.keyword == 'elif':
        return await self.parse_if()
    else:
      return

  async def parse_elif(self):
    self.skip_until(['endif'], ['if'], ['endif'])

  async def parse_else(self):
    self.assert_unexpected_statement()

    self.skip_until(['endif'], ['if'], ['endif'])

  async def parse_endif(self):
    self.assert_unexpected_statement()

  async def parse_for(self):
    self.assert_missing_statement()

    parts = self.state.statement.split(' ', 3)
    if len(parts) != 3:
      self.raise_syntax_error('Keyword "for" requires "@for item in iterable" syntax.')

    varname = parts[0]
    iterable_name = parts[2]

    try:
      iterable = await self.get_field_value(iterable_name)
      itr = iter(iterable)
    except ValueError:
      self.raise_error(RuntimeError, f'"{iterable_name}" is not an iterable.')

    try:
      current_value = next(itr)
      context = ObjDict({
        'varname': varname,
        'current_value': current_value,
        'itr': itr,
        'index': 0,
        'entry_mark': self.pos_index,
      })
      self.for_context.append(context)
      self.locals[varname] = current_value
    except StopIteration:
      pass

  async def parse_endfor(self):
    self.assert_unexpected_statement()

    if len(self.for_context) == 0:
      self.raise_syntax_error(f'Rebundant keyword "endfor".')

    try:
      context = self.for_context[-1]
      current_value = next(context.itr)
      context.update({
        'current_value': current_value,
        'index': context.index+1,
      })
      self.locals[context.varname] = current_value
      self.pos_index = context.entry_mark
    except StopIteration:
      self.for_context.pop()

  async def parse_trim_newline(self):
    self.assert_unexpected_statement()

    self.append_text(self.pending_whitespaces, flush_pending=False)
    self.pending_whitespaces = None
    self.trim_newline_state.append(ObjDict({
      'level': self.level,
      'pos_mark': len(self.results),
    }))

  async def parse_format(self):
    self.assert_missing_statement()
    statement = self.state.statement

    parts = statement.split(' ', 1)
    format = parts[0]
    if len(parts) == 1:
      self.raise_syntax_error('Misssing statement, keyword "format" requires a format and an variable.')
    statement = parts[1]

    field_name = statement
    field_value = await self.get_field_value(field_name)

    if format not in self.formatters:
      self.raise_error(RuntimeError, f'Format "{format}" is not registered.')

    format_res = self.formatters[format](field_value)
    if asyncio.iscoroutine(format_res):
      format_res = await format_res
    self.append_text(format_res)

  async def parse_comment(self):
    self.assert_unexpected_statement()

    self.skip_until(['endcomment'], ['comment'], ['endcomment'])

  async def parse_endcomment(self):
    self.assert_unexpected_statement()

    self.raise_syntax_error(f'Rebundant keyword "endcomment".')

  async def parse_field(self):
    field_value = await self.get_field_value(self.state.field_name)
    self.append_text(field_value)

  @classmethod
  async def format_json(self, value):
    return json.dumps(value, indent=2, ensure_ascii=False)


class Mext:
  PROMPT_CACHE = {}

  def __init__(self):
    self.template = ""
    self.params = {}

  @contextmanager
  def use_template(self, template=None, template_fn=None):
    old_template = self.template

    self.set_template(template=template, template_fn=template_fn)
    yield

    self.set_template(template=old_template)

  @contextmanager
  def use_params(self, **kwargs):
    old_params = self.params

    self.set_params(**kwargs)
    yield

    self.clear_params()
    self.set_params(**old_params)

  def set_template(self, template=None, template_fn=None):
    if template is not None:
      self.template = template
    elif template_fn is not None:
      self.template = self._load_template(template_fn)

  def clear_template(self):
    self.template = ""

  def set_params(self, **kwargs):
    self.params = {**self.params, **kwargs}

  def clear_params(self):
    self.params = {}

  def has_param(self, param_name):
    return param_name in self.params

  def _load_template(self, template_fn):
    return self._load_prompt(f"{template_fn}")

  def _load_prompt(self, prompt_source, reload=False):
    if not reload and prompt_source in Mext.PROMPT_CACHE:
      return Mext.PROMPT_CACHE[prompt_source]

    with open(prompt_source) as f:
      prompt = ''.join(f.readlines())
    prompt = prompt.strip()
    Mext.PROMPT_CACHE[prompt_source] = prompt

    return prompt

  @auto_async
  async def compose(self, template=None, template_fn=None, callbacks=None,
      **kwargs) -> Union[str, Tuple[str, dict]]:
    """
    The template will be formatted using the params provided.

    Supported syntax:
    @input_{ARGNAME} Call callbacks[ARGNAME] with the string composed up to this point to get the value if ARGNAME is not provided as a param. Or else use param[ARGNAME].
    @include_{FILEARG} Compose using template_fn=params[FILEARG] first.
    """
    cur_template = self.template

    if template is not None:
      cur_template = template
    elif template_fn is not None:
      cur_template = self._load_template(template_fn)

    all_kwargs = {
      **self.params,
      **kwargs,
    }

    parser = MextParser()
    parsed_result = await parser.parse(template=cur_template, params=all_kwargs, callbacks=callbacks, template_loader=self._load_template)

    if callbacks is None:
      return parsed_result
    else:
      return parsed_result, parser.input_results
