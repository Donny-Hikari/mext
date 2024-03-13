import unittest
import os
import subprocess
from pathlib import Path
from functools import partial

from mext import Mext
from mext.libs.utils import ObjDict

class TestMext(unittest.TestCase):
  dirs = ObjDict({
    'template_language_usage': Path("tests/mext/readme/template_language_usage"),
  })

  def test_template_language_usage(self):
    template_language_usage: Path = self.dirs.template_language_usage

    # make sure to use the developing version
    env = os.environ.copy()
    if "PYTHONPATH" not in env:
      env["PYTHONPATH"] = os.getcwd()
    else:
      env["PYTHONPATH"] = os.getcwd() + os.pathsep + env["PYTHONPATH"]

    for pyfn in template_language_usage.glob("*.py"):
      expected_fn = pyfn.parent / f'{pyfn.stem}.out'
      with self.subTest(f'File "{pyfn}"'):
        with open(expected_fn, 'r') as f:
          lines = f.readlines()
          expected_result = ''.join(lines)
        proc = subprocess.run(["python3", pyfn.name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, text=True, cwd=pyfn.parent, env=env)
        stdout = proc.stdout
        if proc.stdout.endswith('\n'):
          stdout = proc.stdout[:-1]
        self.assertEqual(stdout, expected_result, msg=proc.stderr or None)
