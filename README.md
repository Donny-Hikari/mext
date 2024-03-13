# Mext

Mext is a text template language that is useful for creating prompts for LLM.

The main target of Mext is to enable readable and powerful prompt templates for LLM (large language model).
But it is not limited to LLM. Mext also provide human friendly but powerful templates to producing texts.

This README is written with Mext. Source file: [readme_src/README.mext](readme_src/README.mext).

## Early Stage

The Mext language is still in its early stage.
New syntaxes may be introduced and broken changes might be made.

## Installation

Use the following command to install mext.

```bash
$ pip install mext-lang
```

To build and install mext from source, clone this repository and use make.

The default target of make will perform testing, cleanup previous build, and install Mext.

```bash
$ make
```

You may as well use pip to install an editable version directly:

```bash
$ pip install -e .
```

## Render Mext file

You can render a Mext file handly with [mext/script/render_mext.py](mext/script/render_mext.py).

Usage:

```bash
$ python -m mext.scripts.render_mext readme_src/README.mext -o README.md
```

Or, if you installed mext, the render script will be installed automatically:

```bash
$ render-mext readme_src/README.mext -o README.md
```

To render this README.md with make:

```bash
$ make README.md
```

This will also render the data file [readme_src/README.yaml](readme_src/README.yaml) from [readme_src/README-yaml.mext](readme_src/README-yaml.mext) and [readme_src/README-yaml.yaml](readme_src/README-yaml.yaml).

## Usage as a template language

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

## Syntax

Note although the @import syntax is used in most of the examples in this section, in production it is more often that variables are passed to `Mext.compose` as parameters directly. Check out the section [Usage as a template language](#Usage%20as%20a%20template%20language) as well.

### if

Template:
````mext
{@import "if.yaml"}

{@if true}
This will be shown.
{@elif false}
This will not be shown.
{@else}
This will not be shown, either.
{@endif}

{@if not empty var}
{var}
{@endif}

{@if not undefined var}
var is defined.
{@endif}
{@if undefined var2}
var2 is undefined.
{@endif}

{@if novalue var2}
var2 has no value.
{@endif}
````

Given params:
````json
{
  "var": "Text from variable."
}
````

Produce:
````markdown
This will be shown.

Text from variable.

var is defined.
var2 is undefined.

var2 has no value.
````

### for

Template:
````mext
{@import "for.yaml"}

## Array
{@for item in arr}
- name: {item[name]}
  content: {item[content]}
{@endfor}

## Dictionary
{@for item_key, item_val in dict}
- key: {item_key}
  val: {item_val}
{@endfor}
````

Given params:
````json
{
  "arr": [
    {
      "name": "Item 1",
      "content": "Content 1"
    },
    {
      "name": "Item 2",
      "content": "Content 2"
    }
  ],
  "dict": {
    "key1": "Value 1",
    "key2": "Value 2"
  }
}
````

Produce:
````markdown
## Array
- name: Item 1
  content: Content 1
- name: Item 2
  content: Content 2

## Dictionary
- key: key1
  val: Value 1
- key: key2
  val: Value 2
````

### trim_newline

Template:
````mext
@trim_newline if the following next blocks produce empty result until it meets a non-empty block.
{@trim_newline}
{@if false}
This will be ignored.
{@endif}

{@trim_newline}
{@if true}
This will be shown right after the line above.
{@endif}

{@trim_newline}
The above and the next new line will not be trimed.

The end.
````

Produce:
````markdown
@trim_newline if the following next blocks produce empty result until it meets a non-empty block.
This will be shown right after the line above.

The above and the next new line will not be trimed.

The end.
````

### format

Template:
````mext
{@import "format.yaml"}
@format a variable using given format. Formatters can be registered with `parser.register_formatter`.
{@format json var}
````

Given params:
````json
{
  "var": {
    "abstract": "List of fruits to purchase.",
    "fruits": [
      "apple",
      "banana",
      "pear"
    ]
  }
}
````

Produce:
````markdown
@format a variable using given format. Formatters can be registered with `parser.register_formatter`.
{
  "abstract": "List of fruits to purchase.",
  "fruits": [
    "apple",
    "banana",
    "pear"
  ]
}
````

### import

Template:
````mext
@import variables from a file.
File ends with 'yaml' or 'json' will automatically be loaded as an object. When 'as' clause is present, the object will be loaded as a variable.
```
{@import "import.yaml" as imported}
{@format json imported}
```

If no 'as' clause is given, first level members of the object will be loaded into the local namespace.
```
{@import "import.yaml"}
{imported_var}
```

Other file type will be loaded as a string variable. Note you must specify the 'as' clause in this case.
Loaded from "default.mext":
```
{@import "default.mext" as default_mext}
{default_mext}
```

Using variable as filename is also possible.
Loaded from "set.mext":
```
{@import imported.set_mext_fn as set_mext}
{set_mext}
```
````

Given params:
````json
{
  "imported_var": "This variable is imported from a yaml file.",
  "set_mext_fn": "set.mext"
}
````

Produce:
````markdown
@import variables from a file.
File ends with 'yaml' or 'json' will automatically be loaded as an object. When 'as' clause is present, the object will be loaded as a variable.
```
{
  "imported_var": "This variable is imported from a yaml file.",
  "set_mext_fn": "set.mext"
}
```

If no 'as' clause is given, first level members of the object will be loaded into the local namespace.
```
This variable is imported from a yaml file.
```

Other file type will be loaded as a string variable. Note you must specify the 'as' clause in this case.
Loaded from "default.mext":
```
@default will not overwrite the variable.
{@default var false}
{@if var}
var is true.
{@else}
var is false.
{@endif}

When the variable exists:
{@import "default.yaml"}
{@default var false}
{@if var}
var is true.
{@else}
var is false.
{@endif}
```

Using variable as filename is also possible.
Loaded from "set.mext":
```
{@import "set.yaml"}
@set will overwrite the variable.
{@set var false}
{@if var}
var is true.
{@else}
var is false.
{@endif}
```
````

### include

Template:
````mext
@include content from "default.mext" file:
```
{@include "default.mext"}
```

With parameters:
```
{@include "default.mext" var=true}
```
````

Produce:
````markdown
@include content from "default.mext" file:
```
@default will not overwrite the variable.
var is false.

When the variable exists:
var is true.
```

With parameters:
```
@default will not overwrite the variable.
var is true.

When the variable exists:
var is true.
```
````

### input

Template:
````mext
@input set a variable by calling a provided callback.
{@input var}

Use the `callbacks` parameter to definite a callback dictionary when calling `parser.parse`.
```
parser.parse(
  template=template,
  template_fn=template_fn,
  callbacks={{
    'var': lambda x: 'any function',
  }},
)
```
````

Produce:
````markdown
@input set a variable by calling a provided callback.
any function

Use the `callbacks` parameter to definite a callback dictionary when calling `parser.parse`.
```
parser.parse(
  template=template,
  template_fn=template_fn,
  callbacks={
    'var': lambda x: 'any function',
  },
)
```
````

### option

Template:
````mext
@option controls the behavior of the parser.
{@option final_strip off}
This will keep the empty line below.

````

Produce:
````markdown
@option controls the behavior of the parser.
This will keep the empty line below.

````

### set

Template:
````mext
{@import "set.yaml"}
@set will overwrite the variable.
{@set var false}
{@if var}
var is true.
{@else}
var is false.
{@endif}
````

Given params:
````json
{
  "var": true
}
````

Produce:
````markdown
@set will overwrite the variable.
var is false.
````

### default

Template:
````mext
@default will not overwrite the variable.
{@default var false}
{@if var}
var is true.
{@else}
var is false.
{@endif}

When the variable exists:
{@import "default.yaml"}
{@default var false}
{@if var}
var is true.
{@else}
var is false.
{@endif}
````

Given params:
````json
{
  "var": true
}
````

Produce:
````markdown
@default will not overwrite the variable.
var is false.

When the variable exists:
var is true.
````

### count

Template:
````mext
{@import "count.yaml"}

{@set idx 0}
{@for item in items}
{@count idx}
{idx}. {item}
{@endfor}
````

Given params:
````json
{
  "items": [
    "Item 1",
    "Item 2",
    "Item 3"
  ]
}
````

Produce:
````markdown
1. Item 1
2. Item 2
3. Item 3
````

### comment

Template:
````mext
@comment will not be shown in the result.
{@comment}
This will be ignored.
{@endcomment}
````

Produce:
````markdown
@comment will not be shown in the result.
````