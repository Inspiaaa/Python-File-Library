
![Python 3.7](https://img.shields.io/badge/Python-3.7-blue.svg?style=for-the-badge&logo=python)  
# FL - Python File Library  
FL enables many **high level** operations on Files and Folders in an **OOP style**.
For example: *Flattening*, *Renaming*, *Recursively Moving* / *Copying* / *Deleting*, ...
  
## Getting Started

### Prerequisites
A working version of **Python 3.7**

---
### Example
#### Basic flattening of a folder
We create the folder structure:
```
example
├── a.txt
├── test
│   ├── b.txt
│   ├── temp
│   │   └── c.txt
```
... and want to **flatten** it to:
```
example
├── a.txt
├── b.txt
└── c.txt
```
We can achieve that with the following code:
```python
from fl import File, Folder, Example  
  
# Create the example nested folder structure with some files
Example.create_simple_nested()  
  
# Collapse (Flatten) the folder structure  
d = Folder("./example/")  
d.collapse()
```

---
### Adding the creation date to each file
Adding the **creation date** to all files in the folder:
```
example
├── a.txt
├── test
│   ├── a.txt
│   ├── b.txt
│   ├── temp
│   │   ├── a.txt
│   │   ├── b.txt
│   │   └── c.txt
```
To do this, we can run following program:
```python
from fl import File, Folder, Example

# Create the example folder structure: 
Example.create_nested_with_duplicates()

# Add the date
d = Folder("./example/")
d.rename_files("%B %TCd-%TCb-%TCY%E")
```
This program uses [special renaming commands](https://github.com/LavaAfterburner/Python-File-Library/wiki/Renaming-Commands) to add special data (e.g. Date). To **visualize** the result in the **console**, the folder class offers a method to print it:
```python
d = Folder("./example/")
d.print_beautified()
```
Console:
```
example
├── a 10-Jun-2019.txt
├── test
│   ├── a 10-Jun-2019.txt
│   ├── b 10-Jun-2019.txt
│   ├── temp
│   │   ├── a 10-Jun-2019.txt
│   │   ├── b 10-Jun-2019.txt
│   │   └── c 10-Jun-2019.txt
```

---
## Documentation
Get started with the documentation [here](https://github.com/LavaAfterburner/Python-File-Library/wiki).
