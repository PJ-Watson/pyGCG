import customtkinter as ctk
from GUI_utils import plot_MUSE_spec
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

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

        # Key bindings
        self.protocol("WM_DELETE_WINDOW", self.quit_gracefully)
        self.bind("<Control-q>", self.quit_gracefully)

        # configure grid system
        self.grid_rowconfigure((0, 1), weight=1)
        self.grid_columnconfigure((0, 1, 2), weight=1)

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
            row=0, column=0, padx=20, pady=20, columnspan=3, sticky="news"
        )

        self.current_gal_id = 1864

        self.muse_spec_frame = SpecFrame(
            self.main_tabs.tab("Spec view"), self.current_gal_id
        )
        # self.muse_spec_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.muse_spec_frame.pack(fill="both", expand=1)

        # print (dir(self.main_tabs.tab("Spec view")))

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
                # for v in dir(self):
                #     if "scal" in str(v):
                #         print(v, self)
                # print(self._get_window_scaling())
                # plotwidth = self.frame2_fileplot.winfo_width() / dpi
                # plotheight = self.frame2_fileplot.winfo_height() / dpi
                self.muse_spec_frame.fig = Figure()
                self.muse_spec_frame.pyplot_canvas = FigureCanvasTkAgg(
                    figure=self.muse_spec_frame.fig, master=self.muse_spec_frame
                )  # A tk.DrawingArea.
                # self.muse_spec_frame.pyplot_canvas.get_tk_widget().pack(fill=ctk.BOTH, expand=True)
                # self.muse_spec_frame.pyplot_canvas.get_tk_widget().grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
                # self.muse_spec_frame.pyplot_canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
                # fig = Figure(figsize=(5, 4), dpi=100)
                # canvas = FigureCanvasTkAgg(fig, master=self.muse_spec_frame)  # A tk.DrawingArea.
                # canvas.draw()
                plot_MUSE_spec(
                    self.muse_spec_frame,
                    figure=self.muse_spec_frame.fig,
                    parent_canvas=self.muse_spec_frame.pyplot_canvas,
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
                    figure=self.muse_spec_frame.fig,
                    parent_canvas=self.muse_spec_frame.pyplot_canvas,
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