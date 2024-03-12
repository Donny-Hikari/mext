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