from mext import Mext, MextParser
from urllib.parse import quote

parser = MextParser()
parser.register_formatter('encode_uri_component', quote) # register a custom formatter 'encode_uri_component'

mext = Mext()
mext.set_parser(parser)
prompt = mext.compose(template="""
{@format encode_uri_component var}
""", params={
  'var': "there are some spaces in this sentence",
})
print(prompt)