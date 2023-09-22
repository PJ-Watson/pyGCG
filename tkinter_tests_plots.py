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
        self.geometry("1280x720")
        # self.geometry("1366x768")
        # self.attributes("-zoomed", True)
        self.title("GLASS-JWST Classification GUI")

        self.initialise_configuration()

        # Key bindings
        self.protocol("WM_DELETE_WINDOW", self.quit_gracefully)
        self.bind("<Control-q>", self.quit_gracefully)

        # configure grid system
        self.grid_rowconfigure((0, 1, 2), weight=1)
        self.grid_columnconfigure((0, 1, 2), weight=1)

        # Setup top navigation buttons
        self.change_appearance_menu = ctk.CTkOptionMenu(
            self,
            # text="Previous Galaxy",
            values=["System", "Light", "Dark"],
            command=self.change_appearance_menu_callback,
        )
        self.change_appearance_menu.grid(
            row=0,
            column=0,
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
                Path(self.base_config["files"]["full_config_path"]).expanduser().resolve(), "rt"
            ) as fp:
                self.full_config = tomlkit.load(fp)
                print(self.full_config)
            

        except FileNotFoundError:
            print(
                "Configuration file not found at the specified location. Creating new config from defaults."
            )
            self.full_config = self.write_full_config(self.base_config)

        ctk.set_appearance_mode(self.full_config["appearance"]["appearance_mode"].lower())
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
        Path(files['temp_dir']).expanduser().resolve().mkdir(exist_ok=True, parents=True)

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
                "Blue (default), dark-blue, or green. The CustomTKinter color theme. "+
                "Can also point to the location of a custom .json file describing the desired theme."
            )
        
        with open(Path(self.base_config["files"]["full_config_path"]).expanduser().resolve(), mode="wt", encoding="utf-8") as fp:
            tomlkit.dump(doc, fp)

        return doc

    def change_appearance_menu_callback(self, choice):
        ctk.set_appearance_mode(choice.lower())

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

        # add widgets onto the frame...
        # self.label = ctk.CTkLabel(self)
        # self.label.grid(row=0, column=0, padx=20)


if __name__ == "__main__":
    app = App()
    app.mainloop()

# PyCube (redshift visualisation)
# Marz (MUSE redshift fits)
# Goel Noiret (noinet)
# Bergamini (multiple images)
