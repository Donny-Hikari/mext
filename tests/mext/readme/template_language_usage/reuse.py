from mext import Mext

mext = Mext()
mext.set_template(template_fn="reuse.mext")

prompt = mext.compose()
print(prompt)

prompt = mext.compose(name="Sydney")
print(prompt)