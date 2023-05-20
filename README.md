# PyDirMap
PyDirMap does the same things as WinDirStat.

PyDirMap executes a dir /S /-C command in Windows Command Prompt via subprocess.run then parses the output to create a tree structure of files and directories.  This tree structure is then displayed in a Tkinter Treeview and a treemap using Matplotlib and Squarify with regions color-coded by file type.  For the sake of performance, files below a user-specified size are excluded from the treemap.
