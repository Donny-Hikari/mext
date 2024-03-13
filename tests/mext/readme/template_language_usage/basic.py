from mext import Mext

mext = Mext()
prompt = mext.compose(template="""
This is an example template.
{@if not undefined name}
The name is: {name}
{@endif}
""", name="Yamato")
print(prompt)