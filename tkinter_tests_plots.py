import customtkinter as ctk
from pathlib import Path
import tomlkit
from astropy.table import Table
from tab_spectrum import SpecFrame
from tab_beams import BeamFrame

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
        self.minsize(1280,720)
        # self.attributes("-zoomed", True)
        self.title("GLASS-JWST Classification GUI")

        self.initialise_configuration()
        self.settings_window = None

        # Key bindings
        self.protocol("WM_DELETE_WINDOW", self.quit_gracefully)
        self.bind("<Control-q>", self.quit_gracefully)

        # configure grid system
        self.grid_rowconfigure(1, weight=1)
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
            sticky="ns",
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
            tab_names=["Beam view", "Spec view"],
            command=self.main_tabs_update,
            # expose_bind_fns=[self._test_pr
            # int_e, self._test_print_e]
        )
        self.main_tabs.grid(
            row=1, column=0, padx=20, pady=20, columnspan=3, sticky="news"
        )

        self.current_gal_id = 3927
        self.current_gal_id = 1864
        # self.current_gal_id = 1494
        # self.current_gal_id = 1338

        self.muse_spec_frame = SpecFrame(
            self.main_tabs.tab("Spec view"), self.current_gal_id
        )
        # self.muse_spec_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.muse_spec_frame.pack(fill="both", expand=1)


        self.main_tabs.tab("Beam view").grid_rowconfigure((0,1,2), weight=1)
        self.main_tabs.tab("Beam view").grid_columnconfigure((0,1,2), weight=1)
        print (self.main_tabs.tab("Beam view").winfo_height())
        for idx, name in enumerate(["F115W", "F150W", "F200W"]):
            self.beam_frame = BeamFrame(
                self.main_tabs.tab("Beam view"), self.current_gal_id, extver=name+",72.0", ext="MODEL", #height = self.main_tabs.tab("Beam view").winfo_height()/2
            )
            # self.muse_spec_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
            # self.beam_frame.pack(fill="both", expand=1)
            self.beam_frame.grid(row=0, column=idx, sticky="ew")
        for idx, name in enumerate(["F115W", "F150W", "F200W"]):
            self.beam_frame = BeamFrame(
                self.main_tabs.tab("Beam view"), self.current_gal_id, extver=name+",341.0", ext="MODEL"# height = self.main_tabs.tab("Beam view").winfo_height()/2
            )
            # self.muse_spec_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
            # self.beam_frame.pack(fill="both", expand=1)
            self.beam_frame.grid(row=1, column=idx, sticky="ew")
        for idx, name in enumerate(["F115W", "F150W", "F200W"]):
            self.beam_frame = BeamFrame(
                self.main_tabs.tab("Beam view"), self.current_gal_id, extver=name, ext="MODEL",# height = self.main_tabs.tab("Beam view").winfo_height()/2,
            )
            # self.muse_spec_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
            # self.beam_frame.pack(fill="both", expand=1)
            self.beam_frame.grid(row=2, column=idx, sticky="ew")

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

        try:
            files["cat_path"]
        except Exception as e:
            print(e)
            self.cat = None
            files.add("cat_path", "")
            files["cat_path"].comment(
                "[optional] The file path of the NIRISS catalogue (FINISH DESCRIPTION LATER)."
            )
        try:
            self.cat = Table.read(Path(files["cat_path"]).expanduser().resolve())
        except:
            self.cat = None

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

        # Lines
        try:
            lines = doc["lines"]
        except:
            lines_tab = tomlkit.table()
            lines_tab.add(
                tomlkit.comment(
                    "These tables define the lines shown in the redshift tab."
                )
            )
            lines_tab.add(tomlkit.nl())
            doc.add(tomlkit.nl())
            doc.add("lines", lines_tab)
            lines = doc["lines"]

        try:
            emission = lines["emission"]
        except:
            lines.add("emission", tomlkit.table().indent(4))
            emission = lines["emission"]
            emission.add(tomlkit.comment("These are the emission lines."))
            emission.add(tomlkit.nl())
            # appearance["appearance_mode"].comment("System (default), light, or dark.")

        em_lines = {
            "Lyman_alpha": {
                "latex_name": r"Ly$\alpha$",
                "centre": 1215.24,
            },
            "CIV_1549": {
                "latex_name": r"C IV",
                "centre": 1549.48,
            },
            "H_delta": {
                "latex_name": r"H$\delta$",
                "centre": 4102.89,
            },
            "OIII_4364": {
                "latex_name": r"OIII",
                "centre": 4364.436,
            },
            "H_gamma": {
                "latex_name": r"H$\gamma$",
                "centre": 4341.68,
            },
            "H_beta": {
                "latex_name": r"H$\beta$",
                "centre": 4862.68,
            },
            "NII_6550": {
                "latex_name": r"NII",
                "centre": 6549.86,
            },
            "H_alpha": {
                "latex_name": r"H$\alpha$",
                "centre": 6564.61,
            },
            "NII_6585": {
                "latex_name": r"NII",
                "centre": 6585.27,
            },
            "PaE": {
                "latex_name": r"Pa-$\eta$",
                "centre": 9548.6,
            },
            "PaD": {
                "latex_name": r"Pa-$\delta$",
                "centre": 10052.1,
            },
            "PaG": {
                "latex_name": r"Pa-$\gamma$",
                "centre": 10941.1,
            },
            "PaB": {
                "latex_name": r"Pa-$\beta$",
                "centre": 12821.6,
            },
            "PaA": {
                "latex_name": r"Pa-$\alpha$",
                "centre": 18756.1,
            },
            "SII_6718": {
                "latex_name": r"SII",
                "centre": 6718.29,
            },
            "SII_6733": {
                "latex_name": r"SII",
                "centre": 6732.67,
            },
            "SIII_9069": {
                "latex_name": r"SIII",
                "centre": 9068.6,
            },
        }

        for line_name, line_data in em_lines.items():
            try:
                emission[line_name]
                for key in line_data.keys():
                    emission[line_name][key]
            except:
                emission.add(line_name, tomlkit.table().indent(8))
                for key, value in line_data.items():
                    emission[line_name].add(key, value)
                emission.add(tomlkit.nl())

        try:
            absorption = lines["absorption"]
        except:
            lines.add("absorption", tomlkit.table().indent(4))
            absorption = lines["absorption"]
            absorption.add(tomlkit.comment("These are the absorption lines."))
            absorption.add(tomlkit.nl())
            # appearance["appearance_mode"].comment("System (default), light, or dark.")

        ab_lines = {
            "K_3935": {
                "latex_name": r"K",
                "centre": 3934.777,
            },
            "H_3970": {
                "latex_name": r"H",
                "centre": 3969.588,
            },
            "G_4306": {
                "latex_name": r"G",
                "centre": 4305.61,
            },
            "Mg_5177": {
                "latex_name": r"Mg",
                "centre": 5176.7,
            },
            "Na_5896": {
                "latex_name": r"Na",
                "centre": 5895.6,
            },
            "Ca_8500": {
                "latex_name": r"CaII",
                "centre": 8500.36,
            },
            "Ca_8544": {
                "latex_name": r"CaII",
                "centre": 8544.44,
            },
            "Ca_8564": {
                "latex_name": r"CaII",
                "centre": 8564.52,
            },
        }

        for line_name, line_data in ab_lines.items():
            try:
                absorption[line_name]
                for key in line_data.keys():
                    absorption[line_name][key]
            except:
                absorption.add(line_name, tomlkit.table().indent(8))
                for key, value in line_data.items():
                    absorption[line_name].add(key, value)
                absorption.add(tomlkit.nl())
        # try:
        #     emission["Halpha"]
        # except:
        #     emission.add("Halpha", "test")
        #     # appearance["theme"].comment(
        #     #     "Blue (default), dark-blue, or green. The CustomTKinter color theme. "
        #     #     + "Can also point to the location of a custom .json file describing the desired theme."
        #     # )

        # print (doc)
        # print (self.base_config["files"]["full_config_path"])

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

    def main_tabs_update(self):
        if self.main_tabs.get() == "Spec view":
            self.muse_spec_frame.update_plot()

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

        cat_settings = SettingsSelection(
            self.scrollable_frame,
            9,
            "Catalogue filepath",
            "cat_path",
            setting_is_dir=False,
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
