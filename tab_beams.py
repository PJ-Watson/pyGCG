import customtkinter as ctk
import tkinter as tk
from matplotlib.figure import Figure
import matplotlib.colors as colors
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
from pathlib import Path
import astropy.io.fits as pf
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u
from tqdm import tqdm
import numpy as np
from astropy.table import Table

class BeamFrame(ctk.CTkFrame):
    def __init__(self, master, gal_id, extver, ext="SCI", **kwargs):
        super().__init__(master, **kwargs)

        self.gal_id = gal_id
        self.extver = extver
        self.ext=ext
        self.cmap="plasma"
        print (self)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.columnconfigure(1, weight=1)
        # self.grid_columnconfigure(0, weight=1)
        # self.grid_columnconfigure(1, weight=0)

        # self.scrollable_frame = ctk.CTkScrollableFrame(self)
        # self.scrollable_frame.grid(row=0, column=1, sticky="news")

        self.label = ctk.CTkLabel(
            self, text="Contamination:"
        )
        self.label.grid(row=1, column=0, padx=10, pady=(10, 10), sticky="e")

        self.cont_value = ctk.StringVar(value="None")  # set initial value
        self.cont_menu = ctk.CTkOptionMenu(self,
                                       values=["None", "Mild", "Strong", "Incomplete trace"],
                                       command=self.optionmenu_callback,
                                       variable=self.cont_value)
        self.cont_menu.grid(row=1, column=1, sticky="w")

        self.file_path = [*(
            Path(self._root().full_config["files"]["extractions_dir"]).expanduser().resolve()
        ).glob(f"*{gal_id:0>5}.stack.fits")][0]

        self.update_plots()

    def optionmenu_callback(choice):
        print("optionmenu dropdown clicked:", choice)

    def update_plots(self):
        if not hasattr(self, "fig_axes"):


            self.pad_frame = tk.Frame(self, width=200, height=200, borderwidth=0, background="")
            self.pad_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")#, padx=10, pady=20)

            self.plot_frame = tk.Frame(
                self,
                bg = "blue",
                width = 300,
                height = 300,
                borderwidth=0,
            )
            self.plot_frame.rowconfigure(0,weight=1)
            self.plot_frame.columnconfigure(0,weight=1)
            # calls function to fix the aspect ratio
            self.set_aspect(self.plot_frame, self.pad_frame, aspect_ratio=5) 
            self.fig = Figure(constrained_layout=True
            # , figsize=(2,1))
            , figsize=(4,1),
            )
            print (self.master.winfo_height()/2)
            print (self.master.winfo_width()/3)
            # self.fig.set_figsize(5,1)
            print (self.fig.get_size_inches())
            self.pyplot_canvas = FigureCanvasTkAgg(
                figure=self.fig,
                master=self.plot_frame,
            )

            if not hasattr(self, "plotted_images"):
                self.plotted_images = dict()

            with pf.open(self.file_path) as hdul:
                # print (hdul["SCI","F115W"])
                shape_sci = hdul.info(output=False)[hdul.index_of((self.ext,self.extver))][5][0]
                shape_kernel = hdul.info(output=False)[hdul.index_of(("KERNEL",self.extver))][5][0]
                # idx_kernel = hdul.index_of(("KERNEL",self.extver))
                # print (hdul.info(output=False))
                # print (hdul.info(output=False)[idx_sci])
                # print (shape_sci)
                # print (hdul["SCI",self.extver].data.shape)

            # self.fig.
            self.fig_axes = self.fig.subplots(1,2,sharey=True,
                # aspect="auto", 
                # width_ratios=[1,shape_sci/shape_kernel],
                # width_ratios=[0.5,1]
                width_ratios=[0.25,1]
            )

            self.plot_kernel()
            self.plot_beam()
            self.fig.canvas.draw_idle()

            self.fig.canvas.get_tk_widget().grid(row=0, column=0,sticky="news")
            # self.fig.canvas.get_tk_widget().pack()
            print (self.fig.canvas.get_tk_widget())
            print (self.fig.get_size_inches())
            print (self.fig_axes[0].get_aspect())

    def plot_kernel(self):
        
        with pf.open(self.file_path) as hdul:
            # print (hdul["SCI","F115W"])
            # print (hdul.info())
            data = hdul["KERNEL",self.extver].data

            self.plotted_images["kernel"] = self.fig_axes[0].imshow(
                data,
                origin="lower",
                cmap=self.cmap,
                # aspect="auto"
            )
            self.fig_axes[0].set_xticklabels("")
            self.fig_axes[0].set_yticklabels("")
            self.fig_axes[0].tick_params(direction="in")

    def plot_beam(self):

        with pf.open(self.file_path) as hdul:
            # print (hdul["SCI","F115W"])
            # print (hdul.info())
            data = hdul[self.ext,self.extver].data

            self.plotted_images["beam"] = self.fig_axes[1].imshow(
                data,
                origin="lower",
                cmap=self.cmap,
                aspect="auto",
            )
            self.fig_axes[1].tick_params(direction="in")
            # self.fig_axes[0].plot([1,2],[3,4])
            # self.update()
            # self.fig_axes.imshow(
            #     data
            # )
            # self.fig_axes[0].plot([1,2],[3,4])
            # self.update()
            # print 

    def set_aspect(self, content_frame, pad_frame, aspect_ratio):
        # a function which places a frame within a containing frame, and
        # then forces the inner frame to keep a specific aspect ratio

        def enforce_aspect_ratio(event):
            # when the pad window resizes, fit the content into it,
            # either by fixing the width or the height and then
            # adjusting the height or width based on the aspect ratio.

            # start by using the width as the controlling dimension
            desired_width = event.width
            desired_height = int(event.width / aspect_ratio)

            # if the window is too tall to fit, use the height as
            # the controlling dimension
            if desired_height > event.height:
                desired_height = event.height
                desired_width = int(event.height * aspect_ratio)

            # place the window, giving it an explicit size
            content_frame.place(in_=pad_frame, x=0, y=0, 
                width=desired_width, height=desired_height)

        pad_frame.bind("<Configure>", enforce_aspect_ratio)

        # AANTAL = [(1,"1"),(2,"2"),(3,"3"),(4,"4"),(5,"5"),(6,"6"),]
        # self.buttons = []
        # self.button_vars = []
        # for idx, (text, mode) in enumerate(AANTAL):
        #     self.button_vars.append(ctk.StringVar(value="1"))
        #     self.buttons.append(ctk.CTkRadioButton(self, text=text, variable=self.button_vars[-1], value=mode))
        #     self.buttons[-1].grid(row=0, column=idx) 


        # status_options = ["Student", "Staff", "Both"]
        # x = ctk.IntVar()
        # for index in range(len(status_options)):
        #     _button = ctk.CTkRadioButton(self,text=status_options[index],variable=x,value=index)
        #     _button.grid(row=1, column=index)
            # .pack(side="left")
        # self.emission_checkbox = ctk.CTkCheckBox(
        #     self.scrollable_frame, text="Emission", command=self.change_lines
        # )
        # self.emission_checkbox.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")
        # self.absorption_checkbox = ctk.CTkCheckBox(
        #     self.scrollable_frame, text="Absorption", command=self.change_lines
        # )
        # self.absorption_checkbox.grid(
        #     row=2, column=0, padx=20, pady=(10, 0), sticky="w"
        # )

        # self.redshift_label = ctk.CTkLabel(self.scrollable_frame, text="Redshift:")
        # self.redshift_label.grid(row=3, padx=10, pady=(10, 0), sticky="w")
        # self.current_redshift = ctk.DoubleVar(
        #     master=self,
        #     value=0,
        # )

        # self.redshift_entry = ctk.CTkEntry(
        #     self.scrollable_frame,
        #     textvariable=self.current_redshift,
        # )
        # self.redshift_entry.grid(
        #     row=4,
        #     column=0,
        #     padx=20,
        #     pady=(10, 0),
        #     sticky="we",
        # )
        # self.redshift_entry.bind(
        #     "<Return>",
        #     self.update_lines,
        # )
        # self.redshift_slider = ctk.CTkSlider(
        #     self.scrollable_frame,
        #     variable=self.current_redshift,
        #     from_=0,
        #     to=2,
        #     orientation="horizontal",
        #     command=self.update_lines,
        # )
        # self.redshift_slider.grid(
        #     row=5,
        #     padx=20,
        #     pady=20,
        # )

    # def change_lines(self):
    #     if self.emission_checkbox.get() and len(self.plotted_lines["emission"]) == 0:
    #         self.add_lines(line_type="emission")
    #         self.update_lines()
    #     elif (
    #         not self.emission_checkbox.get() and len(self.plotted_lines["emission"]) > 0
    #     ):
    #         for line in self.fig_axes.get_lines():
    #             if line in self.plotted_lines["emission"].values():
    #                 line.remove()
    #         for line_key, line_data in (
    #             self._root().full_config["lines"]["emission"].items()
    #         ):
    #             del self.plotted_lines["emission"][line_key]

    #     if (
    #         self.absorption_checkbox.get()
    #         and len(self.plotted_lines["absorption"]) == 0
    #     ):
    #         self.add_lines(line_type="absorption")
    #         self.update_lines()
    #     elif (
    #         not self.absorption_checkbox.get()
    #         and len(self.plotted_lines["absorption"]) > 0
    #     ):
    #         for line in self.fig_axes.get_lines():
    #             if line in self.plotted_lines["absorption"].values():
    #                 line.remove()
    #         for line_key, line_data in (
    #             self._root().full_config["lines"]["absorption"].items()
    #         ):
    #             del self.plotted_lines["absorption"][line_key]

    #     self.pyplot_canvas.draw()
    #     self.update()

    # def update_plot(self):
    #     if not hasattr(self, "pyplot_canvas"):
    #         self.fig = Figure(constrained_layout=True)
    #         self.pyplot_canvas = FigureCanvasTkAgg(
    #             figure=self.fig,
    #             master=self,
    #         )

    #         if not hasattr(self, "plotted_lines"):
    #             self.plotted_lines = dict(emission={}, absorption={})

    #         self.fig_axes = self.fig.add_subplot(111)

    #         self.fig.canvas.mpl_connect("motion_notify_event", self.hover)

    #         self.fig_axes.set_xlabel(r"Wavelength (\AA)")
    #         self.fig_axes.set_ylabel("Flux")

    #         self.custom_annotation = self.fig_axes.annotate(
    #             "", xy=(0, 0), xytext=(0, 0), textcoords="offset points"
    #         )
    #         self.custom_annotation.set_visible(False)

    #         self.plot_grizli(
    #             gal_id=self._root().current_gal_id,
    #         )
    #         self.plot_MUSE_spec(
    #             gal_id=self._root().current_gal_id,
    #         )
    #         self.add_lines()

    #         self.gal_id = self._root().current_gal_id
    #         self.pyplot_canvas.draw_idle()

    #         self.pyplot_canvas.get_tk_widget().grid(row=0, column=0, sticky="news")

    #     if self.gal_id != self._root().current_gal_id or not hasattr(
    #         self, "pyplot_canvas"
    #     ):
    #         self.gal_id = self._root().current_gal_id
    #         self.plot_MUSE_spec(
    #             gal_id=self._root().current_gal_id,
    #         )
    #         self.plot_grizli(
    #             gal_id=self._root().current_gal_id,
    #         )
    #         self.pyplot_canvas.draw_idle()

    #         self.update()

if __name__=="__main__":
    import tkinter as tk

    def center(win, w = None, h = None):
        # sets the window's minimal size and centers it.
        win.update() # updates the window to get it's minimum working size

        # if no size is given, keep the minimum size
        width = w if w else win.winfo_width()
        height = h if h else win.winfo_height()

        # compute position for the window to be central
        x = (win.winfo_screenwidth() - width) // 2
        y = (win.winfo_screenheight() - height) // 2

        # set geomet and minimum size
        win.geometry("{}x{}+{}+{}".format(width, height, x, y))
        win.minsize(width, height)

    def set_aspect(content_frame, pad_frame, aspect_ratio):
        # a function which places a frame within a containing frame, and
        # then forces the inner frame to keep a specific aspect ratio

        def enforce_aspect_ratio(event):
            # when the pad window resizes, fit the content into it,
            # either by fixing the width or the height and then
            # adjusting the height or width based on the aspect ratio.

            # start by using the width as the controlling dimension
            desired_width = event.width
            desired_height = int(event.width / aspect_ratio)

            # if the window is too tall to fit, use the height as
            # the controlling dimension
            if desired_height > event.height:
                desired_height = event.height
                desired_width = int(event.height * aspect_ratio)

            # place the window, giving it an explicit size
            content_frame.place(in_=pad_frame, x=0, y=0, 
                width=desired_width, height=desired_height)

        pad_frame.bind("<Configure>", enforce_aspect_ratio)

    window = tk.Tk()

    window.columnconfigure(0, weight=1, minsize=300)
    window.rowconfigure(0, weight=1, minsize=300)

    # Frame with the main content.
    content = tk.Frame(
        window,
    )
    content.grid(row=0, column=0, padx=5, pady=5, sticky="nesw")

    # Frame for padding apparently necessary to have the resized Frame
    pad_frame = tk.Frame(content, borderwidth=0, background="bisque", width=200, height=200)
    pad_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=20)
    # Frame with the plot. It lays inside the "content" Frame
    plot_frame = tk.Frame(
        content,
        bg = "blue",
        width = 300,
        height = 300
    )
    tk.Label(plot_frame,text='Some Plot').pack()
    # calls function to fix the aspect ratio
    set_aspect(plot_frame, pad_frame, aspect_ratio=16/9) 
    content.rowconfigure(0, weight=1)
    content.columnconfigure(0, weight=1)

    # Frame containing the setting controls
    window.columnconfigure(1, weight=0, minsize=200)
    settings = tk.Frame(
        window,
        bg = "red"
    )
    settings.grid(row=0, column=1, padx=5, pady=5, sticky="nesw")

    # usual Tkinter stuff
    center(window)
    window.title("Some Program")
    window.mainloop()