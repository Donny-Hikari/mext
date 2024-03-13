from mext import Mext

mext = Mext()
with mext.use_template(template_fn="with_template.mext"):
  with mext.use_params(name="Mike", title="AI Software Engineer"):
    prompt = mext.compose(backend="Claude 3")
    print(prompt)
