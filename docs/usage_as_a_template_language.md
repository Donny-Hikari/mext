# Usage as a template language

* [Basic usage](#basic)
* [Reuse template](#reuse)
* [Use with statement](#with_template)
* [Use custom formatters](#register_formatter)

## Basic usage <a id="basic"></a>

To compose a template with Mext, use `Mext.compose`.

Python:
```python
from mext import Mext

mext = Mext()
prompt = mext.compose(template="""
This is an example template.
{@if not undefined name}
The name is: {name}
{@endif}
""", name="Yamato")
print(prompt)
```

Output:
```plaintext
This is an example template.
The name is: Yamato
```
## Reuse template <a id="reuse"></a>

You can set a template and use different variables with it.

Given a tempalte file `reuse.mext`:
```mext
The name is: {@if not novalue name}{name}{@else}Unknown{@endif}
```

Python:
```python
from mext import Mext

mext = Mext()
mext.set_template(template_fn="reuse.mext")

prompt = mext.compose()
print(prompt)

prompt = mext.compose(name="Sydney")
print(prompt)
```

Output:
```plaintext
The name is: Unknown
The name is: Sydney
```
## Use with statement <a id="with_template"></a>

You can use `use_template` and `use_params` with the `with` statement.

Given a tempalte file `with_template.mext`:
```mext
This is the profile of {name}:
name: {name}
title: {title}
backend: {backend}
```

Python:
```python
from mext import Mext

mext = Mext()
with mext.use_template(template_fn="with_template.mext"): # set the template
  with mext.use_params(name="Mike", title="AI Software Engineer"): # set the parameters for the template
    prompt = mext.compose(backend="Claude 3")
    print(prompt)

```

Output:
```plaintext
This is the profile of Mike:
name: Mike
title: AI Software Engineer
backend: Claude 3
```
## Use custom formatters <a id="register_formatter"></a>

`register_formatter` is a powerful function that enables custom functions for text processing.

Python:
```python
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
```

Output:
```plaintext
there%20are%20some%20spaces%20in%20this%20sentence
```