import customtkinter as ctk
from pathlib import Path


class CommentsWindow(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("720x568")
        self.title("Comments")

        # Key bindings
        self.protocol("WM_DELETE_WINDOW", self.quit_comments_gracefully)
        self.bind("<Control-q>", self.quit_comments_gracefully)

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        # self.scrollable_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.pack(side="top", fill="both", expand=True)

        # self.comments_var = ctk.StringVar(
        #     self, ""
        # )
        self.comments_label = ctk.CTkLabel(
            self.main_frame, text="Insert any additional comments here:"
        )
        self.comments_label.grid(
            row=0,
            column=0,
            padx=20,
            pady=(10, 0),
        )

        self.comments_box = ctk.CTkTextbox(
            self.main_frame,
            # textvariable=self.comments_var,
        )
        if "comments" in self._root().current_gal_data.keys():
            self.comments_box.insert("1.0", self._root().current_gal_data["comments"])

        self.comments_box.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="news")
        self.comments_box.bind("<Control-s>", self.quit_comments_gracefully)
        self.comments_box.bind("<Control-Key-a>", self.select_all)
        self.comments_box.bind("<Control-Key-A>", self.select_all)

        self.comments_save_button = ctk.CTkButton(
            self.main_frame,
            text="Save",
            command=self.browse_config_path,
        )
        self.comments_save_button.grid(
            row=2,
            column=0,
            padx=20,
            pady=(5, 10),
            # sticky="",
        )

    def select_all(self, event=None):
        self.comments_box.tag_add("sel", "1.0", "end")
        self.comments_box.mark_set("insert", "1.0")
        self.comments_box.see("insert")
        return "break"

    def change_appearance_menu_callback(self, choice):
        ctk.set_appearance_mode(choice.lower())
        self._root().config["appearance"]["appearance_mode"] = choice.lower()
        self._root().write_config(self._root().config)

    def change_config_path_callback(self, event=None):
        self._root().base_config["files"]["config_path"] = str(
            Path(self.config_path_value.get()).expanduser().resolve()
        )
        with open(
            Path(__file__).parent / "base_config.toml", mode="wt", encoding="utf-8"
        ) as fp:
            tomlkit.dump(self._root().base_config, fp)

        self._root().config["files"]["config_path"] = str(
            Path(self.config_path_value.get()).expanduser().resolve()
        )
        self._root().write_config(self._root().config)

    def browse_config_path(self):
        path_output = str(
            ctk.filedialog.askopenfilename(
                parent=self,
                initialdir=Path(self.config_path_value.get())
                .expanduser()
                .resolve()
                .parent,
            )
        )
        if Path(path_output) is not None and Path(path_output).is_file():
            self.config_path_value.set(path_output)
            self.change_config_path_callback()

    def quit_comments_gracefully(self, event=None):
        # Put some lines here to save current output
        # print ("need to save comments here")
        # print (self.comments_box.get("1.0", "end"))
        self._root().current_gal_data["comments"] = self.comments_box.get("1.0", "end")
        self.destroy()
