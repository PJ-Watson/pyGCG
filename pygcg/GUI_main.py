import collections
import re
from pathlib import Path

import astropy.units as u
import customtkinter as ctk
import numpy as np
import tomlkit
from astropy.coordinates import SkyCoord
from astropy.table import QTable
from CTkMessagebox import CTkMessagebox
from tqdm import tqdm

from pygcg.tabs.beams import BeamFrame
from pygcg.tabs.spectrum import SpecFrame
from pygcg.windows.comments import CommentsWindow
from pygcg.windows.settings import SettingsWindow


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
        self.protocol(
            "WM_DELETE_WINDOW",
            self.quit_gracefully,
        )
        self.bind("<Control-q>", self.quit_gracefully)
        self.bind("<Left>", self.prev_gal_button_callback)
        self.bind("<Right>", self.next_gal_button_callback)

        # configure grid system
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Setup bottom navigation buttons
        nav_frame = ctk.CTkFrame(self)
        nav_frame.grid(
            column=0,
            row=2,
            # columnspan=5,
            sticky="ew",
        )
        nav_frame.grid_columnconfigure((0, 1, 3, 5, 6, 7), weight=1, uniform="blah")
        nav_frame.grid_columnconfigure((2, 4), weight=0, uniform="other")

        self.read_write_button = ctk.CTkSegmentedButton(
            nav_frame,
            values=["Read-only", "Write output"],
            selected_color="red",
            selected_hover_color="dark red",
            command=self.read_write_colour,
        )
        self.read_write_button.grid(
            row=0,
            column=1,
            padx=20,
            pady=10,
            sticky="ew",
        )
        self.read_write_button.set("Read-only")

        self.open_settings_button = ctk.CTkButton(
            nav_frame,
            text="Settings",
            command=self.open_settings_callback,
        )
        self.open_settings_button.grid(
            row=1,
            column=1,
            padx=20,
            pady=10,
            sticky="ew",
        )
        self.prev_gal_button = ctk.CTkButton(
            nav_frame,
            text="Previous",
            command=self.prev_gal_button_callback,
        )
        self.prev_gal_button.grid(
            row=0, column=0, padx=20, pady=10, rowspan=2, sticky="news"
        )
        self.next_gal_button = ctk.CTkButton(
            nav_frame,
            text="Next",
            command=self.next_gal_button_callback,
        )
        self.next_gal_button.grid(
            row=0, column=7, padx=20, pady=10, rowspan=2, sticky="news"
        )
        self.comments_button = ctk.CTkButton(
            nav_frame,
            text="Comments",
            command=self.gal_comments_button_callback,
        )
        self.comments_button.grid(
            row=0,
            column=6,
            padx=20,
            pady=10,
            sticky="ew",
        )

        self.current_gal_data = {}

        self.current_gal_id = ctk.StringVar(master=self)
        self.current_gal_coords = ctk.StringVar(master=self)
        gal_id_label = ctk.CTkLabel(
            nav_frame,
            text="Current ID:",
        )
        gal_id_label.grid(
            row=0,
            column=2,
            padx=(20, 5),
            pady=10,
            sticky="e",
        )
        gal_coord_label = ctk.CTkLabel(
            nav_frame,
            text="Location:",
        )
        gal_coord_label.grid(
            row=0,
            column=4,
            padx=(20, 5),
            pady=10,
            sticky="e",
        )
        self.current_gal_entry = ctk.CTkEntry(
            nav_frame,
            textvariable=self.current_gal_id,
        )
        self.current_gal_entry.bind(
            "<Return>",
            self.change_id_entry,
        )
        self.current_gal_entry.grid(
            row=0,
            column=3,
            padx=(5, 20),
            pady=10,
            sticky="w",
        )

        self.coord_entry = ctk.CTkEntry(
            nav_frame,
            textvariable=self.current_gal_coords,
        )
        self.coord_entry.bind(
            "<Return>",
            self.change_sky_coord,
        )
        self.coord_entry.grid(
            row=0,
            column=5,
            padx=(5, 20),
            pady=10,
            sticky="w",
        )
        self.find_coord_button = ctk.CTkButton(
            nav_frame,
            text="Sky search",
            command=self.change_sky_coord,
        )
        self.find_coord_button.grid(row=1, column=5, padx=(5, 20), pady=10, sticky="w")

        self.rescan_and_reload()

    def rescan_and_reload(self):
        try:
            assert len(self.config["files"]["out_dir"]) > 0
            # assert len(self.config["files"]["cat_path"]) > 0
            assert self.cat is not None
            assert len(self.config["files"]["extractions_dir"]) > 0

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
                        "COMMENTS",
                    ],
                    dtype=[
                        str,
                        int,
                        float,
                        float,
                        str,
                        float,
                        str,
                        float,
                        str,
                        float,
                        str,
                        float,
                        str,
                        float,
                        str,
                        float,
                        float,
                        float,
                        str,
                    ],
                )

            self.id_col = self.cat[self.config["cat"].get("id", "id")].astype(str)
            self.seg_id_col = self.cat[
                self.config["cat"].get("seg_id", self.config["cat"].get("id", "id"))
            ].astype(int)

            # Segmentation map ids must be a unique identifier!
            # If you're reading this message, something has gone horribly wrong
            self.seg_id_col, unique_idx = np.unique(self.seg_id_col, return_index=True)
            self.id_col = self.id_col[unique_idx]
            self.cat = self.cat[unique_idx]
            dir_to_chk = fpe(self.config["files"]["extractions_dir"])

            id_idx_list = []
            for i, (n, s) in tqdm(
                enumerate(zip(self.id_col, self.seg_id_col)),
                desc="Scanning directory for objects in catalogue",
                total=len(self.id_col),
            ):
                if self.config["files"].get("skip_existing", True):
                    if s in self.out_cat["SEG_ID"]:
                        continue
                if any(dir_to_chk.glob(f"*{s:0>5}.1D.fits")) and any(
                    dir_to_chk.glob(f"*{s:0>5}.stack.fits")
                ):
                    id_idx_list.append(i)
            try:
                sorted_idx = np.asarray(id_idx_list)[
                    np.argsort(self.id_col[id_idx_list].astype(float))
                ]

            except Exception as e:
                sorted_idx = id_idx_list

            self.id_col = self.id_col[sorted_idx]
            self.seg_id_col = self.seg_id_col[sorted_idx]
            self.cat = self.cat[sorted_idx]
            self.sky_coords = SkyCoord(
                self.cat[self.config["cat"].get("ra", "ra")],
                self.cat[self.config["cat"].get("dec", "dec")],
            )
            assert len(self.id_col) > 0

            self.current_gal_id.set(self.id_col[0])
            self.tab_row = self.cat[0]
            self.seg_id = self.seg_id_col[0]

            self.current_gal_data["id"] = self.current_gal_id.get()
            self.current_gal_data["seg_id"] = self.seg_id
            self.current_gal_data["ra"] = self.tab_row[
                self.config["cat"].get("ra", "ra")
            ]
            self.current_gal_data["dec"] = self.tab_row[
                self.config["cat"].get("dec", "dec")
            ]

            self.current_gal_coords.set(
                self.sky_coords[self.id_col == self.id_col[0]].to_string(
                    "decimal", precision=6
                )[0]
            )

            self.generate_tabs()
        except Exception as e:
            print(e)
            self.generate_splash()

    def generate_splash(self):
        self.splash_frame = ctk.CTkFrame(self)
        self.splash_frame.grid(row=0, column=0, rowspan=2, sticky="news")
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


        self.plot_options = {
            "cmap": "plasma",
            "stretch":"Square root",
            "limits": "grizli default"
        }

        self.tab_names = [
            f"Orientation 1: {self.PAs[0]} deg",
            f"Orientation 2: {self.PAs[1]} deg",
            f"Spectrum",
        ]

        self.main_tabs = MyTabView(
            master=self,
            tab_names=self.tab_names,
            # tab_names=["Spec view", "Beam view"],
            command=self.main_tabs_update,
        )
        self.main_tabs.grid(row=1, column=0, padx=20, pady=0, sticky="news")
        # print (dir(self.main_tabs._segmented_button))
        # self.main_tabs._segmented_button.grid(pady=0)
        # self.main_tabs._segmented_button.grid_forget(
        # self.main_tabs._top_spacing = 0
        # self.main_tabs._top_button_overhang = 0
        # self.main_tabs._segmented_button.grid_forget()
        # self.main_tabs._configure_grid()
        # print (self.main_tabs.grid_info())
        self.main_tabs._segmented_button.grid(sticky="ew")

        # self.tab_sel_button = ctk.CTkSegmentedButton(self,
        #     values=["PA 1", "PA 2", "Spec"],
        #     # selected_color="red",
        #     # selected_hover_color="dark red",
        #     # command=self.read_write_colour,
        # )
        # self.tab_sel_button.grid(row=0, column=0, columnspan=8, sticky="ew", pady=0, padx=20)

        self.full_spec_frame = SpecFrame(
            self.main_tabs.tab(self.tab_names[2]), self.current_gal_id.get()
        )
        self.full_spec_frame.pack(fill="both", expand=1)

        self.beam_frame_1 = BeamFrame(
            self.main_tabs.tab(self.tab_names[0]), self.current_gal_id.get(), self.PAs[0]
        )
        self.beam_frame_1.pack(fill="both", expand=1)
        self.beam_frame_2 = BeamFrame(
            self.main_tabs.tab(self.tab_names[1]), self.current_gal_id.get(), self.PAs[1]
        )
        self.beam_frame_2.pack(fill="both", expand=1)

        # self.main_tabs.tab("Beam view").grid_configure(row=1, rowspan=3)
        # print (self.main_tabs.tab("Beam view").grid_info())
        # print (self.main_tabs.tab("Beam view").grid_info())
        # self.full_beam_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

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

        for f in ["out_dir", "extractions_dir"]:
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
            try:
                self.cat = QTable.read(
                    [*fpe(files["extractions_dir"]).glob("*ir.cat.fits")][0]
                )
            except:
                self.cat = None

        # print (self.cat)

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
        if event.widget.winfo_class() == ("Entry" or "Textbox"):
            return
        current_tab = self.main_tabs.get()
        # if self.main_tabs.get() == "Beam view":
        #     current_PA_idx = self.full_beam_frame.PA_menu.cget("values").index(
        #         self.full_beam_frame.PA_menu.get()
        #     )
        #     if current_PA_idx == 0:
        #         self.save_current_object()
        #         current_gal_idx = (self.id_col == self.current_gal_id.get()).nonzero()[
        #             0
        #         ]
        #         self.current_gal_id.set(self.id_col[current_gal_idx - 1][0])
        #         self.main_tabs.set("Spec view")
        #         self.change_gal_id()
        #     elif current_PA_idx == 1:
        #         self.full_beam_frame.PA = self.full_beam_frame.PA_menu.cget("values")[0]
        #         self.full_beam_frame.PA_menu.set(self.full_beam_frame.PA)
        #         self.full_beam_frame.update_grid(force_update=True)
        #     elif current_PA_idx == 2:
        #         self.full_beam_frame.PA = self.full_beam_frame.PA_menu.cget("values")[1]
        #         self.full_beam_frame.PA_menu.set(self.full_beam_frame.PA)
        #         self.full_beam_frame.update_grid(force_update=True)
        # elif self.main_tabs.get() == "Spec view":
        #     self.main_tabs.set("Beam view")
        #     self.full_beam_frame.PA = self.full_beam_frame.PA_menu.cget("values")[1]
        #     self.full_beam_frame.PA_menu.set(self.full_beam_frame.PA)
        #     self.full_beam_frame.update_grid()
            # self.change_gal_id()

        
        if current_tab == self.tab_names[2]:
            self.main_tabs.set(self.tab_names[1])
            self.main_tabs_update()
            # print (dir(self.main_tabs.tab(self.tab_names[1])))
        elif current_tab == self.tab_names[1]:
            self.main_tabs.set(self.tab_names[0])
            self.main_tabs_update()
        elif current_tab == self.tab_names[0]:
            self.save_current_object()
            current_gal_idx = (self.id_col == self.current_gal_id.get()).nonzero()[0]
            self.current_gal_id.set(
                self.id_col[(current_gal_idx - 1) % len(self.id_col)][0]
            )
            self.main_tabs.set(self.tab_names[2])
            self.change_gal_id()

    def next_gal_button_callback(self, event=None):
        if event.widget.winfo_class() == ("Entry" or "Textbox"):
            return
        # print ("next")
        current_tab = self.main_tabs.get()
        if current_tab == self.tab_names[0]:
            self.main_tabs.set(self.tab_names[1])
            self.main_tabs_update()
            # print (dir(self.main_tabs.tab(self.tab_names[1])))
        elif current_tab == self.tab_names[1]:
            self.main_tabs.set(self.tab_names[2])
            self.main_tabs_update()
        elif current_tab == self.tab_names[2]:
            self.save_current_object()
            current_gal_idx = (self.id_col == self.current_gal_id.get()).nonzero()[0]
            self.current_gal_id.set(
                self.id_col[(current_gal_idx + 1) % len(self.id_col)][0]
            )
            self.main_tabs.set(self.tab_names[0])
            self.change_gal_id()
        # if self.main_tabs.get() == "Beam view":
        #     current_PA_idx = self.full_beam_frame.PA_menu.cget("values").index(
        #         self.full_beam_frame.PA_menu.get()
        #     )
        #     if current_PA_idx == 0:
        #         self.full_beam_frame.PA = self.full_beam_frame.PA_menu.cget("values")[1]
        #         self.full_beam_frame.PA_menu.set(self.full_beam_frame.PA)
        #         self.full_beam_frame.update_grid(force_update=True)
        #     elif current_PA_idx == 1 or current_PA_idx == 2:
        #         self.main_tabs.set("Spec view")
        #         self.full_spec_frame.update_plot()
        # elif self.main_tabs.get() == "Spec view":
        #     self.save_current_object()
        #     current_gal_idx = (self.id_col == self.current_gal_id.get()).nonzero()[0]
        #     self.current_gal_id.set(
        #         self.id_col[(current_gal_idx + 1) % len(self.id_col)][0]
        #     )
        #     self.main_tabs.set("Beam view")
        #     self.full_beam_frame.PA = self.full_beam_frame.PA_menu.cget("values")[0]
        #     self.full_beam_frame.PA_menu.set(self.full_beam_frame.PA)
        #     self.change_gal_id()
        #     # self.main_tabs_update()

    def save_current_object(self, event=None):
        ### This is where the logic for loading/updating the tables will go
        flattened_data = flatten_dict(self.current_gal_data)

        # # for k, v in flattened_data.items():
        # #     print (k, v, type(v))
        # print(repr(flattened_data))
        # # if len(flattened_data) == 18:
        # #     with open(fpe(self.config["files"]["out_dir"]) / f"{flattened_data['id']}_output.pkl", "wb") as fp:
        # #         pickle.dump(flattened_data, fp)

        # print(self.out_cat)
        # print(flattened_data["SEG_ID"] in self.out_cat["SEG_ID"])

        # This still needs work! Need to check columns match, and make sure I'm not overwriting existing data
        if len(flattened_data) == 19 and self.read_write_button.get() == "Write output":
            # print("Ready to write")
            if flattened_data["SEG_ID"] in self.out_cat["SEG_ID"]:
                warn_overwrite = CTkMessagebox(
                    title="Object already classified!",
                    message=(
                        "The data products for this object have already been classified. "
                        "Overwrite existing classification?\n"
                        "(This operation cannot be undone.)"
                    ),
                    icon="warning",
                    option_1="Cancel",
                    option_2="Overwrite",
                    option_focus=2,
                )
                # print (flattened_data.keys())
                # print (self.out_cat.colnames)
                # print ([n for n in flattened_data.keys() if n not in self.out_cat.colnames])
                if warn_overwrite.get() == "Cancel":
                    return
            # print("Here")
            self.out_cat.add_row(flattened_data)
            self.out_cat.write(self.out_cat_path, overwrite=True)
            # print("Written")

    def change_gal_id(self, event=None):
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
        self.current_gal_data["comments"] = ""

        self.current_gal_coords.set(
            self.sky_coords[self.seg_id_col == self.seg_id].to_string(
                "decimal", precision=6
            )[0]
        )

        self.main_tabs_update()
        self.focus()

    def change_sky_coord(self, event=None):
        new_coord = None
        try:
            new_coord = SkyCoord(self.current_gal_coords.get())
        except ValueError:
            try:
                parts = re.split("[,|;|\s]\s*", self.current_gal_coords.get())
                if len(parts) == 2:
                    new_coord = SkyCoord(
                        float(parts[0]) * u.deg, float(parts[1]) * u.deg
                    )
            except Exception as e:
                print(e)
                pass
        except Exception as e:
            print(e)
            pass

        if new_coord is None:
            error = CTkMessagebox(
                title="Error",
                message="Could not parse input as on-sky coordinates.",
                icon="cancel",
                option_focus=1,
            )
            if error.get() == "OK":
                self.focus()
                return

        sky_match_idx, dist, _ = new_coord.match_to_catalog_sky(self.sky_coords)

        self.current_gal_id.set(self.id_col[sky_match_idx])

        self.focus()
        self.save_current_object()
        self.change_gal_id()

    def change_id_entry(self, event=None):
        self.save_current_object()
        self.change_gal_id()

    def read_write_colour(self, event=None):
        if self.read_write_button.get() == "Read-only":
            self.read_write_button.configure(
                selected_color="red", selected_hover_color="dark red"
            )
        if self.read_write_button.get() == "Write output":
            self.read_write_button.configure(
                selected_color="green", selected_hover_color="dark green"
            )

    def main_tabs_update(self):
        if self.main_tabs.get() == self.tab_names[2]:
            self.full_spec_frame.update_plot()
        if self.main_tabs.get() == self.tab_names[0]:
            self.beam_frame_1.update_grid()
        if self.main_tabs.get() == self.tab_names[1]:
            self.beam_frame_2.update_grid()

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
