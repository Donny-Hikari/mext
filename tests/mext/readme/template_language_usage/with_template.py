from mext import Mext

mext = Mext()
with mext.use_template(template_fn="with_template.mext"): # set the template
  with mext.use_params(name="Mike", title="AI Software Engineer"): # set the parameters for the template
    prompt = mext.compose(backend="Claude 3")
    print(prompt)
