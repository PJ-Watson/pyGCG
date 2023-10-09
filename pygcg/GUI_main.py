import customtkinter as ctk
from pathlib import Path
import tomlkit
from astropy.table import QTable
from pygcg.tabs.spectrum import SpecFrame
from pygcg.tabs.beams import BeamFrame
from pygcg.windows.settings import SettingsWindow
from pygcg.windows.comments import CommentsWindow
import numpy as np
from tqdm import tqdm
import collections
import pickle


class GCG(ctk.CTk):
    def __init__(self, config_file=None):
        super().__init__()

        # Geometry
        self.geometry("1366x768")
        self.minsize(1280, 720)
        # self.attributes("-zoomed", True)
        self.title("GLASS-JWST Classification GUI")

        self.initialise_configuration(config_file)
        self.settings_window = None
        self.comments_window = None

        # Key bindings
        self.protocol("WM_DELETE_WINDOW", self.quit_gracefully)
        self.bind("<Control-q>", self.quit_gracefully)
        self.bind("<Left>", self.prev_gal_button_callback)
        self.bind("<Right>", self.next_gal_button_callback)

        # configure grid system
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        # Setup bottom navigation buttons
        self.open_settings_button = ctk.CTkButton(
            self,
            text="Settings",
            command=self.open_settings_callback,
        )
        self.open_settings_button.grid(
            row=1,
            column=1,
            padx=20,
            pady=20,
            sticky="ew",
        )
        self.prev_gal_button = ctk.CTkButton(
            self,
            text="Previous",
            command=self.prev_gal_button_callback,
        )
        self.prev_gal_button.grid(
            row=1,
            column=0,
            padx=20,
            pady=20,
        )
        self.next_gal_button = ctk.CTkButton(
            self,
            text="Next",
            command=self.next_gal_button_callback,
        )
        self.next_gal_button.grid(
            row=1,
            column=5,
            padx=20,
            pady=20,
        )
        self.comments_button = ctk.CTkButton(
            self,
            text="Comments",
            command=self.gal_comments_button_callback,
        )
        self.comments_button.grid(
            row=1,
            column=4,
            padx=20,
            pady=20,
            sticky="ew",
        )

        self.current_gal_data = {}

        self.current_gal_id = ctk.StringVar(
            master=self,
        )
        self.current_gal_label = ctk.CTkLabel(
            self,
            text="Current ID:",
        )
        self.current_gal_label.grid(
            row=1,
            column=2,
            padx=(20, 5),
            pady=20,
            sticky="e",
        )
        self.current_gal_entry = ctk.CTkEntry(
            self,
            textvariable=self.current_gal_id,
        )
        self.current_gal_entry.grid(
            row=1,
            column=3,
            padx=(5, 20),
            pady=20,
            sticky="w",
        )
        self.current_gal_entry.bind(
            "<Return>",
            self.change_gal_id,
        )

        self.rescan_and_reload()

    def rescan_and_reload(self):
        try:
            assert len(self.config["files"]["out_dir"]) > 0
            assert len(self.config["files"]["cat_path"]) > 0
            assert len(self.config["files"]["extractions_dir"]) > 0

            self.id_col = (
                self._root().cat[self.config["cat"].get("id", "id")].astype(str)
            )
            self.seg_id_col = (
                self._root()
                .cat[
                    self.config["cat"].get("seg_id", self.config["cat"].get("id", "id"))
                ]
                .astype(int)
            )

            # Segmentation map ids must be a unique identifier!
            # If you're reading this message, something has gone horribly wrong
            self.seg_id_col, unique_idx = np.unique(self.seg_id_col, return_index=True)
            self.id_col = self.id_col[unique_idx]
            self.cat = self.cat[unique_idx]
            dir_to_chk = fpe(self.config["files"]["extractions_dir"])

            id_list_unsorted = [
                i
                for i, s in tqdm(
                    zip(self.id_col, self.seg_id_col),
                    desc="Scanning directory for objects in catalogue",
                    total=len(self.id_col),
                )
                if any(dir_to_chk.glob(f"*{s:0>5}.1D.fits"))
                and any(dir_to_chk.glob(f"*{s:0>5}.stack.fits"))
            ]
            try:
                self.id_list = np.array(sorted(id_list_unsorted, key=float))
            except:
                self.id_list = np.array([id_list_unsorted])

            assert len(self.id_list) > 0

            self.out_cat_path = (
                fpe(self.config["files"]["out_dir"]) / "pyGCG_output.fits"
            )

            try:
                self.out_cat = QTable.read(self.out_cat_path)
            except:
                self.out_cat = QTable(
                    names=[
                        "ID",
                        "SEG_ID",
                        "RA",
                        "DEC",
                        f"{self.filter_names[2]},{self.PAs[0]}_QUALITY",
                        f"{self.filter_names[2]},{self.PAs[0]}_COVERAGE",
                        f"{self.filter_names[1]},{self.PAs[0]}_QUALITY",
                        f"{self.filter_names[1]},{self.PAs[0]}_COVERAGE",
                        f"{self.filter_names[0]},{self.PAs[0]}_QUALITY",
                        f"{self.filter_names[0]},{self.PAs[0]}_COVERAGE",
                        f"{self.filter_names[2]},{self.PAs[1]}_QUALITY",
                        f"{self.filter_names[2]},{self.PAs[1]}_COVERAGE",
                        f"{self.filter_names[1]},{self.PAs[1]}_QUALITY",
                        f"{self.filter_names[1]},{self.PAs[1]}_COVERAGE",
                        f"{self.filter_names[0]},{self.PAs[1]}_QUALITY",
                        f"{self.filter_names[0]},{self.PAs[1]}_COVERAGE",
                        "GRIZLI_REDSHIFT",
                        "ESTIMATED_REDSHIFT",
                    ],
                    dtype=[
                        str,
                        int,
                        float,
                        float,
                        str,
                        str,
                        str,
                        str,
                        str,
                        str,
                        str,
                        str,
                        str,
                        str,
                        str,
                        str,
                        float,
                        float,
                    ],
                )
            self.current_gal_id.set(self.id_list[0])
            self.tab_row = self.cat[self.id_col == self.id_list[0]]
            self.seg_id = self.seg_id_col[self.id_col == self.id_list[0]][0]

            self.current_gal_data["id"] = self.current_gal_id.get()
            self.current_gal_data["seg_id"] = self.seg_id
            self.current_gal_data["ra"] = self.tab_row[
                self.config["cat"].get("ra", "ra")
            ]
            self.current_gal_data["dec"] = self.tab_row[
                self.config["cat"].get("dec", "dec")
            ]

            self.generate_tabs()
        except Exception as e:
            print(e)
            self.generate_splash()

    def generate_splash(self):
        self.splash_frame = ctk.CTkFrame(self)
        self.splash_frame.grid(row=0, column=0, columnspan=6, sticky="news")
        self.splash_frame.columnconfigure(0, weight=1)
        self.splash_frame.rowconfigure(0, weight=1)
        main_label = ctk.CTkLabel(
            self.splash_frame,
            text=(
                "No objects found. Check the supplied directories, \n"
                "or rescan the current directory in the settings menu."
            ),
            font=ctk.CTkFont(family="", size=20),
        )
        main_label.grid(row=0, column=0, sticky="news")

    def generate_tabs(self):
        if hasattr(self, "splash_frame"):
            self.splash_frame.destroy()
            del self.splash_frame
        self.main_tabs = MyTabView(
            master=self,
            tab_names=["Beam view", "Spec view"],
            # tab_names=["Spec view", "Beam view"],
            command=self.main_tabs_update,
        )
        self.main_tabs.grid(
            row=0, column=0, padx=20, pady=0, columnspan=6, sticky="news"
        )

        self.muse_spec_frame = SpecFrame(
            self.main_tabs.tab("Spec view"), self.current_gal_id.get()
        )
        # self.muse_spec_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.muse_spec_frame.pack(fill="both", expand=1)

        self.full_beam_frame = BeamFrame(
            self.main_tabs.tab("Beam view"), self.current_gal_id.get()
        )
        # self.muse_spec_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.full_beam_frame.pack(fill="both", expand=1)

    def initialise_configuration(self, config_file=None):
        try:
            assert config_file is not None
            self.config_file_path = config_file
            with open(config_file, "rt") as fp:
                self.config = tomlkit.load(fp)
            self.write_config()
        except Exception as e:
            print(e)
            print(
                "No valid config file supplied. Creating config.toml in the current working directory."
            )
            example_path = Path(__file__).parent / "example_config.toml"
            with open(example_path, "rt") as fp:
                self.config = tomlkit.load(fp)
            self.config_file_path = fpe(Path.cwd() / "config.toml")
            with open(
                self.config_file_path,
                mode="wt",
                encoding="utf-8",
            ) as fp:
                tomlkit.dump(self.config, fp)

        ctk.set_appearance_mode(self.config["appearance"]["appearance_mode"].lower())
        ctk.set_default_color_theme(self.config["appearance"]["theme"].lower())

    def write_config(self):
        try:
            files = self.config["files"]
        except:
            files_tab = tomlkit.table()
            self.config.add("files", files_tab)
            files = self.config["files"]

        for f in ["out_dir", "extractions_dir", "cat_path"]:
            try:
                files[f]
            except:
                files.add(f, "")

        if len(files["out_dir"]) > 0:
            try:
                fpe(files["out_dir"]).mkdir(exist_ok=True, parents=True)
                self.out_dir = fpe(files["out_dir"])
                if len(files["temp_dir"]) > 0:
                    fpe(files["temp_dir"]).mkdir(exist_ok=True, parents=True)
                    self.temp_dir = fpe(files["temp_dir"])
                else:
                    self.temp_dir = self.out_dir / ".temp"
                    self.temp_dir.mkdir(exist_ok=True)
            except:
                print("Could not find or create output directory.")

        try:
            self.cat = QTable.read(fpe(files["cat_path"]))
        except:
            self.cat = None

        # Catalogue
        try:
            cat = self.config["cat"]
        except:
            cat_tab = tomlkit.table()
            self.config.add("cat", cat_tab)

        # Grisms
        try:
            grisms = self.config["grisms"]
        except:
            grism_tab = tomlkit.table()
            self.config.add("grisms", grism_tab)

        self.filter_names = [
            self.config["grisms"].get("R", "F200W"),
            self.config["grisms"].get("G", "F150W"),
            self.config["grisms"].get("B", "F115W"),
        ]
        self.PAs = [
            str(self.config["grisms"].get("PA1", 72.0)),
            str(self.config["grisms"].get("PA2", 341.0)),
        ]

        # Appearance
        try:
            appearance = self.config["appearance"]
        except:
            appearance_tab = tomlkit.table()
            self.config.add("appearance", appearance_tab)
            appearance = self.config["appearance"]

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
            lines = self.config["lines"]
        except:
            lines_tab = tomlkit.table()
            lines_tab.add(
                tomlkit.comment(
                    "These tables define the lines shown in the redshift tab."
                )
            )
            lines_tab.add(tomlkit.nl())
            self.config.add(tomlkit.nl())
            self.config.add("lines", lines_tab)
            lines = self.config["lines"]

        try:
            emission = lines["emission"]
        except:
            lines.add("emission", tomlkit.table().indent(4))
            emission = lines["emission"]
            emission.add(tomlkit.comment("These are the emission lines."))
            emission.add(tomlkit.nl())

        em_lines = {
            "Lyman_alpha": {
                "latex_name": r"Ly$\alpha$",
                "centre": 1215.24,
            },
            "H_alpha": {
                "latex_name": r"H$\alpha$",
                "centre": 6564.61,
            },
        }

        for line_name, line_data in em_lines.items():
            try:
                emission[line_name]
                for key in line_data.keys():
                    emission[line_name][key]
            except:
                emission.add(line_name, tomlkit.table().indent(4))
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

        with open(
            fpe(self.config_file_path),
            mode="wt",
            encoding="utf-8",
        ) as fp:
            tomlkit.dump(self.config, fp)

        return self.config

    def open_settings_callback(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self)
        else:
            self.settings_window.focus()

    def gal_comments_button_callback(self):
        if self.comments_window is None or not self.comments_window.winfo_exists():
            self.comments_window = CommentsWindow(self)
        else:
            self.comments_window.focus()

    def prev_gal_button_callback(self, event=None):
        if self.main_tabs.get() == "Beam view":
            current_PA_idx = self.full_beam_frame.PA_menu.cget("values").index(
                self.full_beam_frame.PA_menu.get()
            )
            if current_PA_idx == 0:
                current_gal_idx = (self.id_list == self.current_gal_id.get()).nonzero()[
                    0
                ]
                self.current_gal_id.set(self.id_list[current_gal_idx - 1][0])
                self.main_tabs.set("Spec view")
                self.change_gal_id()
            elif current_PA_idx == 1:
                self.full_beam_frame.PA = self.full_beam_frame.PA_menu.cget("values")[0]
                self.full_beam_frame.PA_menu.set(self.full_beam_frame.PA)
                self.full_beam_frame.update_grid(force_update=True)
            elif current_PA_idx == 2:
                self.full_beam_frame.PA = self.full_beam_frame.PA_menu.cget("values")[1]
                self.full_beam_frame.PA_menu.set(self.full_beam_frame.PA)
                self.full_beam_frame.update_grid(force_update=True)
        elif self.main_tabs.get() == "Spec view":
            self.main_tabs.set("Beam view")
            self.full_beam_frame.PA = self.full_beam_frame.PA_menu.cget("values")[1]
            self.full_beam_frame.PA_menu.set(self.full_beam_frame.PA)
            self.full_beam_frame.update_grid()
            # self.change_gal_id()

    def next_gal_button_callback(self, event=None):
        if self.main_tabs.get() == "Beam view":
            current_PA_idx = self.full_beam_frame.PA_menu.cget("values").index(
                self.full_beam_frame.PA_menu.get()
            )
            if current_PA_idx == 0:
                self.full_beam_frame.PA = self.full_beam_frame.PA_menu.cget("values")[1]
                self.full_beam_frame.PA_menu.set(self.full_beam_frame.PA)
                self.full_beam_frame.update_grid(force_update=True)
            elif current_PA_idx == 1 or current_PA_idx == 2:
                self.main_tabs.set("Spec view")
                self.muse_spec_frame.update_plot()
        elif self.main_tabs.get() == "Spec view":
            current_gal_idx = (self.id_list == self.current_gal_id.get()).nonzero()[0]
            self.current_gal_id.set(
                self.id_list[(current_gal_idx + 1) % len(self.id_list)][0]
            )
            self.main_tabs.set("Beam view")
            self.full_beam_frame.PA = self.full_beam_frame.PA_menu.cget("values")[0]
            self.full_beam_frame.PA_menu.set(self.full_beam_frame.PA)
            self.change_gal_id()

    def change_gal_id(self, event=None):
        ### This is where the logic for loading/updating the tables will go
        flattened_data = flatten_dict(self.current_gal_data)

        # for k, v in flattened_data.items():
        #     print (k, v, type(v))
        # print (repr(flattened_data))
        # if len(flattened_data) == 18:
        #     with open(fpe(self.config["files"]["out_dir"]) / f"{flattened_data['id']}_output.pkl", "wb") as fp:
        #         pickle.dump(flattened_data, fp)

        # This still needs work! Need to check columns match, and make sure I'm not overwriting existing data
        if len(flattened_data) == 18:
            # print (flattened_data.keys())
            # print (self.out_cat.colnames)
            # print ([n for n in flattened_data.keys() if n not in self.out_cat.colnames])
            self.out_cat.add_row(flattened_data)
            self.out_cat.write(self.out_cat_path, overwrite=True)

        # print("Changing galaxy id!")

        self.tab_row = self.cat[self.id_col == self.current_gal_id.get()]
        if len(self.tab_row) > 1:
            self.tab_row = self.tab_row[0]
        self.seg_id = self.seg_id_col[self.id_col == self.current_gal_id.get()][0]

        self.current_gal_data = {}
        self.current_gal_data["id"] = self.current_gal_id.get()
        self.current_gal_data["seg_id"] = self.seg_id
        self.current_gal_data["ra"] = self.tab_row[self.config["cat"].get("ra", "ra")]
        self.current_gal_data["dec"] = self.tab_row[
            self.config["cat"].get("dec", "dec")
        ]

        self.main_tabs_update()

    def main_tabs_update(self):
        if self.main_tabs.get() == "Spec view":
            self.muse_spec_frame.update_plot()
        if self.main_tabs.get() == "Beam view":
            self.full_beam_frame.update_grid()

    def quit_gracefully(self, event=None):
        # Put some lines here to save current output
        self.write_config()
        self.quit()


class MyTabView(ctk.CTkTabview):
    def __init__(self, master, tab_names, expose_bind_fns=None, **kwargs):
        super().__init__(master, **kwargs)

        # create tabs
        for i, name in enumerate(tab_names):
            self.add(name)
            try:
                self.tab(name).bind("<<TabChanged>>", expose_bind_fns[i])
            except:
                pass


def fpe(filepath):
    return Path(filepath).expanduser().resolve()


def flatten_dict(input_dict, parent_key=False, separator="_"):
    items = []
    for key, value in input_dict.items():
        new_key = str(parent_key) + separator + key if parent_key else key
        if isinstance(value, collections.abc.MutableMapping):
            items.extend(flatten_dict(value, new_key, separator).items())
        elif isinstance(value, list):
            for k, v in enumerate(value):
                items.extend(flatten_dict({str(k): v}, new_key).items())
        else:
            items.append((new_key.upper(), value))
    return dict(items)


def run_app(**kwargs):
    app = GCG(**kwargs)
    app.mainloop()
    app.withdraw()
