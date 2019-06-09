![Python 3.7](https://img.shields.io/badge/Python-3.7-blue.svg)
# FL - Python File Library
FL enables many high level operations on Files and Folders in an OOP style.

## Examples

### Basic flattening of a folder

We create the folder structure:
```
example
├── a.txt
├── test
│   ├── b.txt
│   ├── temp
│   │   └── c.txt
```
... and want to flatten it to:
```
example
├── a.txt
├── b.txt
└── c.txt
```

We can achieve that with  the following code:

```python
from lf import File, Folder


# Create the nested folder structure with some files in it
File("./example/a.txt").create()
File("./example/test/b.txt").create()
File("./example/test/temp/c.txt").create()

# Collapse the folder structure (flatten)
d = Folder("./example/")
d.collapse()

```

### Flattening a folder with a rename

Now we have this folder structure:

```
example
├── a.txt
├── test
│   ├── a.txt
│   ├── b.txt
│   ├── temp
│   │   └── c.txt
```

Flattening it normally will not work, because the file `a.txt` would exist twice in the same folder. So to avoid that, the collapse method can take an optional renaming function:

```python
from lf import File, Folder


File("./example/a.txt").create()
File("./example/test/a.txt").create()
File("./example/test/b.txt").create()
File("./example/test/temp/c.txt").create()

# Collapse the folder structure (flatten)
d = Folder("./example/")
d.collapse(rename_func="%B %C[-]%E")

```
This code will result in:
```
example
├── a test.txt
├── a.txt
├── b test.txt
└── c test-temp.txt
```

The magic happens here: ```rename_func="%B %C[-]%E```
FL is able to execute special commands on a string renaming function:

 - `%B` - Name of the file (without extension type) or folder
 - `%E` - Extension type of the file (with .)
 - `%C[...]` - Collapsed folder names joined with the given sequence between `[` and `]`
 - `%T` - Time
   - `%TC` - Creation Time
   - `%TM` - Modified Time
   - `%TA` - Access Time
   - `%TL` - "Least Time" minimum time of Creation Time, Modified Time, Access Time, in case a file is corrupt

To use the Time commands you have to add a [datetime formatting code](http://strftime.org/). 
E.g.
```python
"%TCf-TCm-TCY" # "09-06-2019"
"%B %TMY" # "MyFile 2019"
```

### Printing a folder structure
```python
File("./example/a.txt").create()
File("./example/test/a.txt").create()
File("./example/test/b.txt").create()
File("./example/test/temp/c.txt").create()

d = Folder("./example/")
print(d.beautify())
```

Output:
```
example
├── a.txt
├── test
│   ├── a.txt
│   ├── b.txt
│   ├── temp
│   │   └── c.txt
```
