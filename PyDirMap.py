# Build a tree of the directories and files in a user-specified directory
# Display that tree in a tkinter treeview
# Plot selected directory in treemap using matplotlib and squarify
# Click on a square to see the path and size
# Right click to open that square in a new window

import subprocess
import random
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import squarify
from collections import Counter


DIR = '<DIR>'  # Directory constant

# Set defined colors for file extensions.
# Extensions do not include the '.'
# If no preset color, a random color will be assigned
COLORS = {
    DIR: (.2, )*3  # the color assigned to directories
          }


class FileObject:
    # File object is a class containing
    # a parent,
    # a dictionary of children,
    # a total file size,
    def __init__(self, path, parent, size=0):
        self.path = path
        self.size = size
        self.parent = parent
        if self.parent is not None:
            self.parent.children[path] = self
        self.children = {}
        self.label = ''
        dot = self.path[::-1].find('.')
        self.extension = self.path[-dot:].lower() if 0 <= dot <= 5 else '<DIR>'

    def rollup(self):
        # Recursively calculate the total size of this object and all children
        for child in self.children.values():
            child.rollup()
            self.size += child.size
        self.label = self.path + ' | ' + str(self.size//1024**2) + ' MB'


class DirectoryMap:
    def __init__(self, root_directory, resolution=10000):
        self.root_directory = root_directory
        self.resolution = resolution
        # initialize plot
        dx, dy = 1, 1
        fig, self.ax = plt.subplots()
        fig.canvas.manager.set_window_title(self.root_directory.path)
        self.ax.set_ylim([0, dy])
        self.ax.set_xlim([0, dx])
        # set up variables
        self.colors = COLORS
        self.legend = {}  # file extension: example artist / color
        self.extension_count = []  # list of file extensions for counting
        self.patch_dict = {}
        rect = {'x': 0, 'y': 0, 'dx': dx, 'dy': dy}
        self.minsize = self.root_directory.size // resolution
        # plot rectangles
        self.draw(self.root_directory, rect)
        self.make_legend()
        print('rectangles complete  ')
        # set up interactive events
        fig.canvas.mpl_connect("pick_event", self.onpick)
        self.click_list = []
        timer = fig.canvas.new_timer(interval=100)
        timer.add_callback(self.ontime)
        timer.start()
        plt.show()

    def draw(self, file, rect):
        # Draw file and rect then recursively call children of file
        # get extension and color
        extension = file.extension
        color = self.get_color(extension)
        # plot rectangle for object
        x, y, dx, dy = (rect[i] for i in ('x', 'y', 'dx', 'dy'))
        rect_patch = patches.Rectangle((x, y), dx, dy,
                                       facecolor=color,
                                       linewidth=1,
                                       linestyle='-',
                                       edgecolor=(0, )*3,
                                       picker=True)
        self.patch_dict[rect_patch] = file
        artist = self.ax.add_patch(rect_patch)
        # record extension:artist to legend
        if extension not in self.legend:
            self.legend[extension] = artist
            self.colors[extension] = color

        # get sizes of children and calculate treemap
        children = [child for child in file.children.values()
                    if child.size >= self.minsize]
        if not children:  # if no children
            return
        children.sort(key=lambda x: x.size, reverse=True)
        total_size = dx * dy
        scaled_sizes = [child.size / file.size * total_size
                        for child in children]
        rectangles = squarify.squarify(scaled_sizes, x, y, dx, dy)
        for child, rect in zip(children, rectangles):
            self.draw(child, rect)

    def make_legend(self):
        extension_count = Counter(self.extension_count)
        extensions = sorted(self.legend.keys(),
                            key=lambda x: extension_count[x],
                            reverse=True)
        artists = [self.legend[ext] for ext in extensions]
        self.ax.legend(artists, extensions,
                       bbox_to_anchor=(1.0, 1.0),
                       loc='upper left')

    def onpick(self, event):
        # on pick event, add picked artist(s) to list
        if isinstance(event.artist, patches.Rectangle):
            object = self.patch_dict[event.artist]
            self.click_list.append((object, event.mouseevent.button))

    def ontime(self):
        # every 100ms, choose the longest path from the pick list
        # set title to path
        # if right click, open new window to explore
        if not self.click_list:
            return
        object, button = max(self.click_list, key=lambda x: len(x[0].path))
        self.click_list[:] = []
        self.ax.set_title(object.label)
        plt.show(block=False)
        if button == 3:
            DirectoryMap(object, self.resolution)
        if button == 2:
            DirectoryTree(object)

    def get_color(self, extension):
        if extension not in self.colors:
            self.colors[extension] = get_random_color()
        self.extension_count.append(extension)
        return self.colors[extension]


class DirectoryTree:
    def __init__(self, root_directory):
        self.root_directory = root_directory
        self.directory_dict = {}
        # Build Tk window
        self.root = tk.Tk()
        self.root.title(self.root_directory.path)
        self.root.state('zoomed')
        tree_frame = tk.Frame(self.root)
        tree_frame.pack(side='top', expand=True, fill='both')
        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack(side='top')
        tk.Button(buttons_frame, text='Make Treemap',
                  command=self.make_treemap).pack(side='left')
        map_res_label = tk.Label(buttons_frame, text='Map Resolution:')
        map_res_label.pack(side='left')
        self.map_resolution = tk.Entry(buttons_frame)
        self.map_resolution.insert(0, '10000')
        self.map_resolution.pack(side='left')
        tk.Button(buttons_frame, text='View Parent',
                  command=self.map_parent).pack(side='left')
        tk.Button(buttons_frame, text='Instructions',
                  command=self.instructions).pack(side='left')
        self.tree = ttk.Treeview(tree_frame, columns=('size',))
        self.tree.column('size', width=200)
        self.tree.heading('size', text='Size [MB]')
        self.tree.pack(side='top', expand=True, fill='both')
        # add items to tree recursively
        self.build_tree(self.root_directory)
        # expand and focus top level
        self.tree.item(self.root_directory.path, open=True)
        self.tree.focus(self.root_directory.path)
        self.root.mainloop()

    def build_tree(self, file, parent=''):
        # add self to tree under parent
        id = self.tree.insert(parent, 'end', file.path, text=file.path,
                              values=str(file.size//1024**2))
        self.directory_dict[id] = file
        child_directories = sorted((child for child in file.children.values()
                                    if child.children), key=lambda x: x.size,
                                   reverse=True)
        child_files = sorted((child for child in file.children.values()
                              if not child.children), key=lambda x: x.size,
                             reverse=True)
        for child in child_directories + child_files:
            self.build_tree(child, id)

    def make_treemap(self):
        id = self.tree.focus()
        if id == '':
            return
        resolution = int(self.map_resolution.get())
        DirectoryMap(self.directory_dict[id], resolution)

    def map_parent(self):
        parent = self.root_directory.parent
        DirectoryTree(parent)

    def instructions(self):
        inst = tk.Toplevel(self.root)
        inst_text = 'Make Treemap will show a graphical view of selection\n' +\
                    'Left click on a map area to view details.\n' +\
                    'Right click to open a new map of that item\n' +\
                    'Middle click to open a tree view of that item\n' +\
                    'View Parent to see a tree of the parent directory.\n' +\
                    'Resolution controls the minimum file size rendered.\n' +\
                    'Higher resolution will display smaller files.'
        label = tk.Label(inst, text=inst_text)
        label.pack(side='top')


def get_random_color():
    return tuple([random.randint(0, 255)/256 for _ in range(3)])


def create_parents(directory_path, directory_dict):
    # split directory path on '\\' and create file objects for
    # all parents as needed
    dps = directory_path.split('\\')
    directory_object = None
    for i in range(1, len(dps)+1):
        new_directory = '\\'.join(dps[:i])
        if new_directory not in directory_dict:
            directory_object = FileObject(new_directory, directory_object)
            directory_dict[new_directory] = directory_object
        else:
            directory_object = directory_dict[new_directory]
    return directory_object


def get_file_list(path_to_scan):
    # scan path using windows dir command
    print('scanning ' + path_to_scan)
    file_listing = subprocess.run(('dir', path_to_scan+'\\', '/S', '/-C'),
                                  shell=True,
                                  check=False,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE
                                  ).stdout.decode('utf-8', errors='ignore')
    print('dir command complete')
    # parse dir command output
    no_total = file_listing.split('Total Files')[0]
    directory_dict = {}
    for directory in no_total.split('Directory of ')[1:]:
        directory = directory.split('\n')
        directory_path = directory[0].strip().rstrip('\\')
        directory_object = create_parents(directory_path, directory_dict)
        # assign files to directory
        for file in directory[4:-3]:
            file_size = file[22:39].strip()
            if not file_size.isnumeric():
                continue
            file_name = file[39:].strip()
            fo = FileObject(directory_path + '\\' + file_name,
                            directory_object, int(file_size))
            directory_dict[fo.path] = fo
    print('parse complete')
    while directory_object.parent is not None:
        directory_object = directory_object.parent
    directory_object.rollup()
    print('rollup complete')
    return directory_dict[path_to_scan]


def main():
    # ask user for path
    prompt = "Please select the directory to scan."
    path_to_scan = filedialog.askdirectory(title=prompt)
    path_to_scan = path_to_scan.replace('/', '\\').rstrip('\\')
    root_directory = get_file_list(path_to_scan)
    DirectoryTree(root_directory)


main()
