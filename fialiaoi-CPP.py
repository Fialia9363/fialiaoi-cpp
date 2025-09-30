import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess, os, re, sys
from pygments import lex
from pygments.lexers import CppLexer, PythonLexer
from pygments.token import Token

class IDE:
    def __init__(self, root):
        self.root = root
        self.root.title("Fialiaoi-CPP")
        self.file_path = None
        self.language = tk.StringVar(value="C++")

        menu = tk.Menu(root)
        file_menu = tk.Menu(menu, tearoff=0)
        file_menu.add_command(label="新建", command=self.new_file)
        file_menu.add_command(label="打开", command=self.open_file)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=root.quit)
        menu.add_cascade(label="文件", menu=file_menu)

        run_menu = tk.Menu(menu, tearoff=0)
        run_menu.add_command(label="运行", command=self.run_code)
        menu.add_cascade(label="运行", menu=run_menu)

        lang_menu = tk.Menu(menu, tearoff=0)
        lang_menu.add_radiobutton(label="C++", variable=self.language, value="C++")
        lang_menu.add_radiobutton(label="Python", variable=self.language, value="Python")
        menu.add_cascade(label="语言", menu=lang_menu)

        root.config(menu=menu)

        self.main_frame = tk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.main_frame.pack(fill=tk.BOTH, expand=1)

        self.file_tree = ttk.Treeview(self.main_frame, show="tree")
        self.file_tree.pack(fill=tk.Y, side=tk.LEFT)
        self.main_frame.add(self.file_tree)

        self.populate_tree()

        self.sidebar = tk.Listbox(self.main_frame, width=25, bg="#1e1e1e", fg="white")
        self.sidebar.pack(fill=tk.Y, side=tk.LEFT)
        self.main_frame.add(self.sidebar)

        self.text = tk.Text(self.main_frame, wrap="none", undo=True,
                            bg="#1e1e1e", fg="white", insertbackground="white")
        self.text.pack(fill=tk.BOTH, expand=1)
        self.text.bind("<KeyRelease>", self.on_key_release)
        self.text.bind("<Return>", self.auto_indent)
        self.text.bind("<Key>", self.auto_complete)

        self.main_frame.add(self.text)

        self.console = tk.Text(root, height=10, bg="black", fg="lime", insertbackground="white")
        self.console.pack(fill=tk.X)

        self.file_tree.bind("<<TreeviewSelect>>", self.on_file_select)

    def populate_tree(self):
        if sys.platform == "win32":
            drives = []
            for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    drives.append(drive)
            for drive in drives:
                root_node = self.file_tree.insert('', 'end', text=drive, open=True)
                self.populate_subtree(root_node, drive)
        else:
            root_node = self.file_tree.insert('', 'end', text='/', open=True)
            self.populate_subtree(root_node, '/')

    def populate_subtree(self, parent, path):
        try:
            for name in os.listdir(path):
                full_path = os.path.join(path, name)
                isdir = os.path.isdir(full_path)
                node = self.file_tree.insert(parent, 'end', text=name, open=False)
                if isdir:
                    self.file_tree.insert(node, 'end', text="dummy")
        except PermissionError:
            pass

    def on_file_select(self, event):
        selected_item = self.file_tree.selection()[0]
        selected_text = self.file_tree.item(selected_item, 'text')
        parent_path = self.get_parent_path(selected_item)

        full_path = os.path.join(parent_path, selected_text)

        if os.path.isfile(full_path):
            self.file_path = full_path
            with open(full_path, "r", encoding="utf-8") as f:
                self.text.delete(1.0, tk.END)
                self.text.insert(tk.END, f.read())
            self.update_sidebar()
            self.highlight_code()
        elif os.path.isdir(full_path):
            if self.file_tree.get_children(selected_item):
                if self.file_tree.item(selected_item, 'open'):
                    self.file_tree.delete(*self.file_tree.get_children(selected_item))
                    self.file_tree.item(selected_item, open=False)
                else:
                    self.populate_subtree(selected_item, full_path)
                    self.file_tree.item(selected_item, open=True)

    def get_parent_path(self, item):
        parent = self.file_tree.parent(item)
        if parent == '':
            if sys.platform == "win32":
                return self.file_tree.item(item, 'text')  
            else:
                return '/'  
        else:
            return os.path.join(self.get_parent_path(parent), self.file_tree.item(parent, 'text'))

    def new_file(self):
        self.text.delete(1.0, tk.END)
        self.file_path = None
        self.sidebar.delete(0, tk.END)

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("所有文件", "*.*")])
        if path:
            self.file_path = path
            with open(path, "r", encoding="utf-8") as f:
                self.text.delete(1.0, tk.END)
                self.text.insert(tk.END, f.read())
            self.update_sidebar()
            self.highlight_code()

    def save_file(self):
        if not self.file_path:
            path = filedialog.asksaveasfilename(defaultextension=".cpp")
            if not path:
                return
            self.file_path = path
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(self.text.get(1.0, tk.END))
        self.update_sidebar()

    def run_code(self):
        if not self.file_path:
            self.save_file()
        self.save_file()
        lang = self.language.get()
        output = ""
        if lang == "C++":
            exe = self.file_path.replace(".cpp", ".exe")
            try:
                subprocess.run(["g++", self.file_path, "-o", exe], check=True, capture_output=True)
                result = subprocess.run(exe, capture_output=True, text=True)
                output = result.stdout + result.stderr
            except subprocess.CalledProcessError as e:
                output = e.stderr.decode("utf-8")
        elif lang == "Python":
            result = subprocess.run(["python", self.file_path], capture_output=True, text=True)
            output = result.stdout + result.stderr
        else:
            output = "未知语言"
        self.console.delete(1.0, tk.END)
        self.console.insert(tk.END, output)

    def highlight_code(self, event=None):
        code = self.text.get(1.0, tk.END)
        lang = self.language.get()
        lexer = CppLexer() if lang == "C++" else PythonLexer()
        self.text.mark_set("range_start", "1.0")
        for token, content in lex(code, lexer):
            self.text.mark_set("range_end", "range_start + %dc" % len(content))
            self.text.tag_add(str(token), "range_start", "range_end")
            self.text.mark_set("range_start", "range_end")
        self.text.tag_configure(str(Token.Keyword), foreground="orange")
        self.text.tag_configure(str(Token.Name.Function), foreground="cyan")
        self.text.tag_configure(str(Token.Comment), foreground="green")
        self.text.tag_configure(str(Token.Literal.String), foreground="yellow")

    def update_sidebar(self):
        self.sidebar.delete(0, tk.END)
        code = self.text.get(1.0, tk.END)
        lang = self.language.get()
        if lang == "C++":
            funcs = re.findall(r"\b(\w+)\s+\w+\s*\([^)]*\)\s*\{", code)
        else:  # Python
            funcs = re.findall(r"def\s+(\w+)\s*\(", code)
        for f in funcs:
            self.sidebar.insert(tk.END, f)

    def on_key_release(self, event):
        self.highlight_code()
        self.update_sidebar()

    def auto_indent(self, event):
        line = self.text.get("insert linestart", "insert")
        indent = re.match(r"\s*", line).group(0)
        self.text.insert("insert", "\n" + indent)
        return "break"

    def auto_complete(self, event):
        pairs = {"(": ")", "[": "]", "{": "}", "\"": "\"", "'": "'"}
        if event.char in pairs:
            self.text.insert("insert", pairs[event.char])
            self.text.mark_set("insert", "insert-1c")

if __name__ == "__main__":
    root = tk.Tk()
    ide = IDE(root)
    root.mainloop()