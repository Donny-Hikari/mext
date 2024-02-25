import sys
import argparse
from os import path

from mext.libs.config_loader import CFG
from mext.libs.utils import ensure_folder_exists
from mext.libs.utils import ObjDict
from mext import Mext

def parse_args(argv=sys.argv[1:]):
  parser = argparse.ArgumentParser()
  parser.add_argument(dest="mextfile", type=str, help="The mextfile to render.")
  parser.add_argument("-o", "--output", type=str, help="The destination to output the rendered file.")
  parser.add_argument("-p", "--params", action="append", type=str, default=[], help="The file that definited the parameters in the mextfile.")
  args = parser.parse_args(argv)
  return args

def render_mext():
  args = parse_args()
  context_mgr = Mext()

  params = {}
  for param_file in args.params:
    partial_params = CFG.load_config(param_file)
    params.update(ObjDict.convert_recursively(partial_params))

  prompt = context_mgr.compose(
    template_fn=args.mextfile,

    **params,
  )

  if args.output is None:
    print(prompt)
  else:
    ensure_folder_exists(args.output)
    with open(args.output, 'w') as f:
      f.write(prompt)

if __name__ == "__main__":
  render_mext()
