import sys
import argparse

from autocode.libs.config_loader import CFG
from autocode.libs.utils import setupLogging, LOG_VERBOSE
from autocode.libs.utils import ensure_folder_exists
from autocode.libs.utils import ObjDict
from autocode.libs.mext import Mext

def parse_args(argv=sys.argv[1:]):
  parser = argparse.ArgumentParser()
  parser.add_argument(dest="mextfile", type=str, help="The mextfile to render.")
  parser.add_argument("-o", "--output", type=str, help="The destination to output the rendered file.")
  parser.add_argument("-p", "--params", action="append", type=str, help="The file that definited the parameters in the mextfile.")
  args = parser.parse_args(argv)
  return args

def main():
  args = parse_args()
  context_mgr = Mext()

  params = {}
  for param_file in args.params:
    partial_params = CFG.load_config(param_file)
    params.update(ObjDict.convert_recursively(partial_params))

  prompt = context_mgr.compose(
    template_fn=args.mextfile,
    use_async=False,

    **params,
  )

  ensure_folder_exists(args.output)
  with open(args.output, 'w') as f:
    f.write(prompt)

if __name__ == "__main__":
  main()
