# PyDirMap
PyDirMap does the same things as WinDirStat.  
Maps your drive, any size.  
Free up space, find large files.  
Check out this sweet tool: PyDirMap  

PyDirMap executes a `dir /S /-C` command in Windows Command Prompt in a user-specified directory via `subprocess.run` then parses the output to create a tree structure of files and directories.  This tree structure is then displayed in a `Tkinter Treeview` and an interactive treemap using `Matplotlib` and `Squarify` with regions color-coded by file type.  For the sake of performance, files below a user-specified size are excluded from the treemap.

There's just the one file, so install the imported modules and run it in Python3.  
Windows only.
