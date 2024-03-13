# Usage as a template language

## Basic usage

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
## Reuse template

You can set a template and use different variables with it.

Given a tempalte file:
```mext
The name is: {@if not novalue name}{name}{@else}Unknown{@endif}
```

Python:
```python
import Mext

mext = Mext()
mext.set_template(template_fn="template1.mext")

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