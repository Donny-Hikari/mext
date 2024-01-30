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