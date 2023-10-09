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
        self._root().write_config()

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
        self.bind("<Control-w>", self.quit_settings_gracefully)

        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.grid_columnconfigure(0, weight=0)
        self.scrollable_frame.grid_columnconfigure(1, weight=1)
        self.scrollable_frame.pack(side="top", fill="both", expand=True)

        self.rescan_button = ctk.CTkButton(
            self.scrollable_frame,
            text="Rescan directories",
            command=self._root().rescan_and_reload,
        )
        self.rescan_button.grid(
            row=0,
            column=0,
            padx=20,
            pady=20,
            sticky="we",
            columnspan=2,
        )

        self.appearance_label = ctk.CTkLabel(
            self.scrollable_frame, text="Appearance mode"
        )
        self.appearance_label.grid(
            row=1,
            column=0,
            padx=20,
            pady=20,
        )
        self.change_appearance_menu = ctk.CTkOptionMenu(
            self.scrollable_frame,
            values=["System", "Light", "Dark"],
            command=self.change_appearance_menu_callback,
        )
        self.change_appearance_menu.grid(row=1, column=1, padx=20, pady=20, sticky="w")
        self.change_appearance_menu.set(
            self._root().config["appearance"]["appearance_mode"]
        )

        proper_names = [
            "Catalogue filepath",
            "Output directory",
            "Extractions directory",
            "Prep directory",
            "Cube filepath",
            "Temporary directory",
        ]
        backend_names = [
            "cat_path",
            "out_dir",
            "extractions_dir",
            "prep_dir",
            "cube_path",
            "temp_dir",
        ]
        is_dir = [0, 1, 1, 1, 0, 1]

        additional_settings = []

        for i, (p, b, d) in enumerate(zip(proper_names, backend_names, is_dir)):
            additional_settings.append(
                SettingsSelection(
                    self.scrollable_frame,
                    row=2 * (i + 1),
                    label=p,
                    value=b,
                    setting_is_dir=d,
                )
            )

    def change_appearance_menu_callback(self, choice):
        ctk.set_appearance_mode(choice.lower())
        self._root().config["appearance"]["appearance_mode"] = choice.lower()
        self._root().write_config()

    def quit_settings_gracefully(self, event=None):
        # Put some lines here to save current output
        self._root().write_config()
        self.destroy()
