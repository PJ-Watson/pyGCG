import customtkinter as ctk
from pathlib import Path

class SettingsSelection(ctk.CTkFrame):
    def __init__(
        self, master, row, label, value, setting_is_dir=False, *args, **kwargs
    ):
        super().__init__(master, *args, **kwargs)

        self.value_key = value
        self.setting_is_dir = setting_is_dir

        self.settings_label = ctk.CTkLabel(
            master,
            text=label,
        )
        self.settings_label.grid(
            row=row,
            column=0,
            padx=20,
            pady=(10, 0),
        )
        self.settings_value = ctk.StringVar(
            self, self._root().config["files"][self.value_key]
        )
        self.settings_entry = ctk.CTkEntry(
            master,
            textvariable=self.settings_value,
        )
        self.settings_entry.grid(
            row=row,
            column=1,
            padx=20,
            pady=(10, 0),
            sticky="we",
        )
        self.settings_entry.bind(
            "<Return>",
            self.change_settings_callback,
        )
        self.open_browse_dir_button = ctk.CTkButton(
            master,
            text="Browse",
            command=self.browse_dir if self.setting_is_dir else self.browse_file,
        )
        self.open_browse_dir_button.grid(
            row=row + 1,
            column=1,
            padx=20,
            pady=(5, 10),
            sticky="we",
            columnspan=2,
        )

    def change_settings_callback(self, event=None):
        self._root().config["files"][self.value_key] = str(
            Path(self.settings_value.get()).expanduser().resolve()
        )
        self._root().write_config(self._root().config)

    def browse_dir(self):
        dir_output = ctk.filedialog.askdirectory(
            parent=self,
            initialdir=Path(self.settings_value.get()).expanduser().resolve(),
        )
        self.settings_value.set(dir_output)
        self.change_settings_callback()

    def browse_file(self):
        path_output = str(
            ctk.filedialog.askopenfilename(
                parent=self,
                initialdir=Path(self.settings_value.get())
                .expanduser()
                .resolve()
                .parent,
            )
        )
        if Path(path_output) is not None and Path(path_output).is_file():
            self.settings_value.set(path_output)
            self.change_settings_callback()


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("720x568")
        self.title("Settings")

        # Key bindings
        self.protocol("WM_DELETE_WINDOW", self.quit_settings_gracefully)
        self.bind("<Control-q>", self.quit_settings_gracefully)

        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.grid_columnconfigure(0, weight=0)
        self.scrollable_frame.grid_columnconfigure(1, weight=1)
        self.scrollable_frame.pack(side="top", fill="both", expand=True)

        self.appearance_label = ctk.CTkLabel(
            self.scrollable_frame, text="Appearance mode"
        )
        self.appearance_label.grid(
            row=0,
            column=0,
            padx=20,
            pady=20,
        )
        self.change_appearance_menu = ctk.CTkOptionMenu(
            self.scrollable_frame,
            values=["System", "Light", "Dark"],
            command=self.change_appearance_menu_callback,
        )
        self.change_appearance_menu.grid(row=0, column=1, padx=20, pady=20, sticky="w")
        self.change_appearance_menu.set(
            self._root().config["appearance"]["appearance_mode"]
        )

        self.config_path_label = ctk.CTkLabel(
            self.scrollable_frame, text="Full config path"
        )
        self.config_path_label.grid(
            row=1,
            column=0,
            padx=20,
            pady=(10, 0),
        )

        self.config_path_value = ctk.StringVar(
            self, self._root().config["files"]["config_path"]
        )
        self.config_path_entry = ctk.CTkEntry(
            self.scrollable_frame,
            textvariable=self.config_path_value,
        )
        self.config_path_entry.grid(row=1, column=1, padx=20, pady=(10, 0), sticky="we")
        self.config_path_entry.bind("<Return>", self.change_config_path_callback)
        self.open_config_path_button = ctk.CTkButton(
            self.scrollable_frame,
            text="Browse",
            command=self.browse_config_path,
        )
        self.open_config_path_button.grid(
            row=2,
            column=1,
            padx=20,
            pady=(5, 10),
            sticky="we",
        )

        temp_settings = SettingsSelection(
            self.scrollable_frame,
            3,
            "Temporary directory",
            "temp_dir",
            setting_is_dir=True,
        )

        cube_settings = SettingsSelection(
            self.scrollable_frame,
            5,
            "Cube filepath",
            "cube_path",
            setting_is_dir=False,
        )

        extractions_settings = SettingsSelection(
            self.scrollable_frame,
            7,
            "Extractions directory",
            "extractions_dir",
            setting_is_dir=True,
        )

        prep_settings = SettingsSelection(
            self.scrollable_frame,
            9,
            "Prep directory",
            "prep_dir",
            setting_is_dir=True,
        )

        cat_settings = SettingsSelection(
            self.scrollable_frame,
            11,
            "Catalogue filepath",
            "cat_path",
            setting_is_dir=False,
        )

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

    def quit_settings_gracefully(self, event=None):
        # Put some lines here to save current output
        self._root().write_config(self._root().config)
        self.destroy()