import re
import json
from os import path
from string import Formatter
from contextlib import contextmanager
from typing import Union, Tuple, Coroutine, Callable
import traceback

from mext.libs.config_loader import CFG
from mext.libs.utils import ObjDict
from mext.mext_parser import MextParser

class Mext:
  PROMPT_CACHE = {}

  def __init__(self):
    self.template = ""
    self.params = {}
    self.callbacks = {}

  @contextmanager
  def use_template(self, template=None, template_fn=None):
    old_template = self.template

    self.set_template(template=template, template_fn=template_fn)
    try:
      yield
    finally:
      self.set_template(template=old_template)

  @contextmanager
  def use_params(self, **kwargs):
    old_params = self.params

    self.set_params(**kwargs)
    try:
      yield
    finally:
      self.clear_params()
      self.set_params(**old_params)

  @contextmanager
  def use_callbacks(self, **kwargs):
    old_callbacks = self.callbacks

    self.set_callbacks(**kwargs)
    try:
      yield
    finally:
      self.clear_callbacks()
      self.set_callbacks(**old_callbacks)

  def set_template(self, template=None, template_fn=None):
    if template_fn is not None:
      template = self._load_template(template_fn)
    self.template = template
    self.template_fn = template_fn

  def clear_template(self):
    self.template = ""

  def set_params(self, **kwargs):
    self.params = {**self.params, **kwargs}

  def clear_params(self):
    self.params = {}

  def has_param(self, param_name):
    return param_name in self.params

  def set_callbacks(self, **kwargs):
    self.callbacks = {**self.callbacks, **kwargs}

  def clear_callbacks(self):
    self.callbacks = {}

  def has_callback(self, callback_name):
    return callback_name in self.callbacks

  def _load_template(self, template_fn):
    return self._load_prompt(f"{template_fn}")

  def _load_prompt(self, prompt_source, reload=False):
    if not reload and prompt_source in Mext.PROMPT_CACHE:
      return Mext.PROMPT_CACHE[prompt_source]

    with open(prompt_source) as f:
      prompt = ''.join(f.readlines())
    Mext.PROMPT_CACHE[prompt_source] = prompt

    return prompt

  def compose(self, template=None, template_fn=None, callbacks={},
      **kwargs) -> Union[str, Tuple[str, dict]]:
    """
    The template will be formatted using the params provided.

    Supported syntax:
    @input_{ARGNAME} Call callbacks[ARGNAME] with the string composed up to this point to get the value if ARGNAME is not provided as a param. Or else use param[ARGNAME].
    @include_{FILEARG} Compose using template_fn=params[FILEARG] first.
    """
    if template is None and template_fn is None:
      template = self.template
      template_fn = self.template_fn

    all_kwargs = {
      **self.params,
      **kwargs,
    }

    parser = MextParser()
    parsed_result = parser.parse(template=template, template_fn=template_fn, params=all_kwargs, callbacks=callbacks, template_loader=self._load_template)

    if len(callbacks) == 0:
      return parsed_result
    else:
      return parsed_result, parser.input_results
