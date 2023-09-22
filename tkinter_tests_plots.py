import customtkinter as ctk
from GUI_utils import plot_MUSE_spec
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from pathlib import Path
import tomlkit

# app = customtkinter.CTk()
# app.geometry("768x512")


# def button_function():
#     print("button pressed")


# button = customtkinter.CTkButton(
#     master=app,
#     text="CTkButton",
#     command=button_function,
# )
# button.place(relx=0.5, rely=0.5, anchor=customtkinter.CENTER)

# app.mainloop()


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Geometry
        # self.geometry("1280x720")
        self.geometry("1366x768")
        # self.attributes("-zoomed", True)
        self.title("GLASS-JWST Classification GUI")

        self.initialise_configuration()
        self.settings_window = None

        # Key bindings
        self.protocol("WM_DELETE_WINDOW", self.quit_gracefully)
        self.bind("<Control-q>", self.quit_gracefully)

        # configure grid system
        self.grid_rowconfigure((0, 1, 2), weight=1)
        self.grid_columnconfigure((0, 1, 2), weight=1)

        # # Setup top navigation buttons
        # self.change_appearance_menu = ctk.CTkOptionMenu(
        #     self,
        #     # text="Previous Galaxy",
        #     values=["System", "Light", "Dark"],
        #     command=self.change_appearance_menu_callback,
        # )
        # self.change_appearance_menu.grid(
        #     row=0,
        #     column=0,
        #     padx=20,
        #     pady=20,
        #     # sticky="news",
        # )
        self.open_settings_button = ctk.CTkButton(
            self,
            text="Settings",
            command=self.open_settings_callback,
        )
        self.open_settings_button.grid(
            row=0,
            column=2,
            padx=20,
            pady=20,
            # sticky="news",
        )

        # Setup bottom navigation buttons
        self.prev_gal_button = ctk.CTkButton(
            self,
            text="Previous Galaxy",
            command=self.prev_gal_button_callback,
        )
        self.prev_gal_button.grid(
            row=2,
            column=0,
            padx=20,
            pady=20,
            # sticky="news",
        )
        self.next_gal_button = ctk.CTkButton(
            self,
            text="Next Galaxy",
            command=self.next_gal_button_callback,
        )
        self.next_gal_button.grid(
            row=2,
            column=2,
            padx=20,
            pady=20,
            # sticky="news",
        )
        self.save_gal_button = ctk.CTkButton(
            self,
            text="Save Galaxy",
            command=self.save_gal_button_callback,
        )
        self.save_gal_button.grid(
            row=2,
            column=1,
            padx=20,
            pady=20,
            # sticky="news",
        )

        self.main_tabs = MyTabView(
            master=self,
            tab_names=["Redshift view", "Spec view"],
            command=self.main_tabs_update,
            # expose_bind_fns=[self._test_print_e, self._test_print_e]
        )
        self.main_tabs.grid(
            row=1, column=0, padx=20, pady=20, columnspan=3, sticky="news"
        )

        self.current_gal_id = 1864

        self.muse_spec_frame = SpecFrame(
            self.main_tabs.tab("Spec view"), self.current_gal_id
        )
        # self.muse_spec_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.muse_spec_frame.pack(fill="both", expand=1)

        # print (dir(self.main_tabs.tab("Spec view")))

    def initialise_configuration(self):
        try:
            with open(Path(__file__).parent / "base_config.toml", "rt") as fp:
                self.base_config = tomlkit.load(fp)
                assert self.base_config["files"]["full_config_path"]
        except:
            self.base_config = self.write_base_config()

        try:
            with open(
                Path(self.base_config["files"]["full_config_path"])
                .expanduser()
                .resolve(),
                "rt",
            ) as fp:
                self.full_config = tomlkit.load(fp)
                self.write_full_config(self.full_config)

        except FileNotFoundError:
            print(
                "Configuration file not found at the specified location. Creating new config from defaults."
            )
            self.full_config = self.write_full_config(self.base_config)

        ctk.set_appearance_mode(
            self.full_config["appearance"]["appearance_mode"].lower()
        )
        ctk.set_default_color_theme(self.full_config["appearance"]["theme"].lower())

    def write_base_config(self):
        doc = tomlkit.document()
        doc.add(
            tomlkit.comment(
                "This is the base configuration file, which stores the settings used previously."
            )
        )
        doc.add(tomlkit.nl())
        doc.add("title", "Base Configuration")

        files = tomlkit.table()
        files.add("full_config_path", str(Path(__file__).parent / "base_config.toml"))
        files["full_config_path"].comment(
            "The location of the primary configuration file."
        )

        doc.add("files", files)

        with open(files["full_config_path"], mode="wt", encoding="utf-8") as fp:
            tomlkit.dump(doc, fp)

        return doc

    def write_full_config(self, doc):
        # Files
        try:
            files = doc["files"]
        except:
            files_tab = tomlkit.table()
            doc.add("files", files_tab)
            files = doc["files"]

        try:
            files["temp_dir"]
        except:
            files.add("temp_dir", "~/.pyGCG_temp")
            files["temp_dir"].comment(
                "The directory in which temporary files are stored."
            )
        Path(files["temp_dir"]).expanduser().resolve().mkdir(
            exist_ok=True, parents=True
        )

        try:
            files["extractions_dir"]
        except:
            files.add("extractions_dir", "")
            files["extractions_dir"].comment(
                "The directory in which NIRISS extractions are stored."
            )

        try:
            files["cube_path"]
        except:
            files.add("cube_path", "")
            files["cube_path"].comment(
                "[optional] The file path of the corresponding MUSE datacube."
            )

        # Appearance
        try:
            appearance = doc["appearance"]
        except:
            appearance_tab = tomlkit.table()
            doc.add("appearance", appearance_tab)
            appearance = doc["appearance"]

        try:
            appearance["appearance_mode"]
        except:
            appearance.add("appearance_mode", "system")
            appearance["appearance_mode"].comment("System (default), light, or dark.")

        try:
            appearance["theme"]
        except:
            appearance.add("theme", "blue")
            appearance["theme"].comment(
                "Blue (default), dark-blue, or green. The CustomTKinter color theme. "
                + "Can also point to the location of a custom .json file describing the desired theme."
            )

        with open(
            Path(self.base_config["files"]["full_config_path"]).expanduser().resolve(),
            mode="wt",
            encoding="utf-8",
        ) as fp:
            tomlkit.dump(doc, fp)

        return doc

    def open_settings_callback(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(
                self
            )  # create window if its None or destroyed
        else:
            self.settings_window.focus()

    def save_gal_button_callback(self):
        print("Save button clicked!")

    def prev_gal_button_callback(self):
        print("Previous galaxy button clicked!")
        self.change_gal_id(relative_change=-1)

    def next_gal_button_callback(self):
        print("Next galaxy button clicked!")
        self.change_gal_id(relative_change=1)

    def change_gal_id(self, relative_change=1):
        self.current_gal_id += relative_change
        print(self.current_gal_id)

        self.main_tabs_update()

    # def _test_print_e(self, event):
    #     # print(dir(event))
    #     # print (event.widget)
    #     print("Test")

    def main_tabs_update(self):
        if self.main_tabs.get() == "Spec view":
            if not hasattr(self.muse_spec_frame, "pyplot_canvas"):
                self.muse_spec_frame.fig = Figure()
                self.muse_spec_frame.pyplot_canvas = FigureCanvasTkAgg(
                    figure=self.muse_spec_frame.fig, master=self.muse_spec_frame
                )
                plot_MUSE_spec(
                    self.muse_spec_frame,
                    gal_id=self.current_gal_id,
                )
                self.muse_spec_frame.pyplot_canvas.get_tk_widget().pack(
                    side="top", fill="both", expand=True
                )
                # self.muse_spec_frame.pyplot_canvas.get_tk_widget().grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
                # self.update()
                # print (dir(self.muse_spec_frame._canvas))
            if self.muse_spec_frame.gal_id != self.current_gal_id or not hasattr(
                self.muse_spec_frame, "pyplot_canvas"
            ):
                plot_MUSE_spec(
                    self.muse_spec_frame,
                    gal_id=self.current_gal_id,
                )

                self.muse_spec_frame.pyplot_canvas.get_tk_widget().pack(
                    side="top", fill="both", expand=True
                )
                self.update()
                # print (dir(self.muse_spec_frame))
                # print (self.muse_spec_frame.winfo_children())

    def quit_gracefully(self, event=None):
        # Put some lines here to save current output
        self.write_full_config(self.full_config)
        self.quit()


class MyTabView(ctk.CTkTabview):
    def __init__(self, master, tab_names, expose_bind_fns=None, **kwargs):
        super().__init__(master, **kwargs)

        # create tabs
        for i, name in enumerate(tab_names):
            self.add(name)
            try:
                self.tab(name).bind("<<TabChanged>>", expose_bind_fns[i])
            # print ("success")
            except:
                pass

        # add widgets on tabs
        # self.label = ctk.CTkLabel(master=self.tab("tab 1"))
        # self.label.grid(row=0, column=0, padx=20, pady=10)

    # def _test_print_current_tab(self):
    #     print (self.get())


class SpecFrame(ctk.CTkFrame):
    def __init__(self, master, gal_id, **kwargs):
        super().__init__(master, **kwargs)

        self.gal_id = gal_id


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
            self, self._root().full_config["files"][self.value_key]
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
        self._root().full_config["files"][self.value_key] = str(
            Path(self.settings_value.get()).expanduser().resolve()
        )
        self._root().write_full_config(self._root().full_config)

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
            self._root().full_config["appearance"]["appearance_mode"]
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
            self, self._root().full_config["files"]["full_config_path"]
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

    def change_appearance_menu_callback(self, choice):
        ctk.set_appearance_mode(choice.lower())
        self._root().full_config["appearance"]["appearance_mode"] = choice.lower()
        self._root().write_full_config(self._root().full_config)

    def change_config_path_callback(self, event=None):
        self._root().base_config["files"]["full_config_path"] = str(
            Path(self.config_path_value.get()).expanduser().resolve()
        )
        with open(
            Path(__file__).parent / "base_config.toml", mode="wt", encoding="utf-8"
        ) as fp:
            tomlkit.dump(self._root().base_config, fp)

        self._root().full_config["files"]["full_config_path"] = str(
            Path(self.config_path_value.get()).expanduser().resolve()
        )
        self._root().write_full_config(self._root().full_config)

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
        self._root().write_full_config(self._root().full_config)
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()

# PyCube (redshift visualisation)
# Marz (MUSE redshift fits)
# Goel Noiret (noinet)
# Bergamini (multiple images)
