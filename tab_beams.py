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

from astropy.visualization import (
    MinMaxInterval,
    SqrtStretch,
    ImageNormalize,
    LinearStretch,
    LogStretch,
    ManualInterval,
)


class BeamFrame(ctk.CTkFrame):
    def __init__(self, master, gal_id, **kwargs):
        super().__init__(master, **kwargs)

        self.cmap = "plasma"
        self.ext = "SCI"
        self.stretch = "Linear"
        self.limits = "grizli default"

        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.grid(
            row=0,
            column=0,
            columnspan=3,
            sticky="ew",
        )
        ext_label = ctk.CTkLabel(self.settings_frame, text="Extension:")
        ext_label.grid(row=0, column=0, padx=(20, 5), pady=20, sticky="e")
        self.ext_menu = ctk.CTkOptionMenu(
            self.settings_frame,
            values=["SCI", "WHT", "CONTAM", "MODEL", "RESIDUALS"],
            command=self.change_ext,
        )
        self.ext_menu.grid(row=0, column=1, padx=(5, 20), pady=20, sticky="w")

        cmap_label = ctk.CTkLabel(self.settings_frame, text="Colourmap:")
        cmap_label.grid(row=0, column=2, padx=(20, 5), pady=20, sticky="e")
        self.cmap_menu = ctk.CTkOptionMenu(
            self.settings_frame,
            values=["plasma", "viridis_r", "jet", "binary"],
            command=self.change_cmap,
        )
        self.cmap_menu.grid(row=0, column=3, padx=(5, 20), pady=20, sticky="w")

        stretch_label = ctk.CTkLabel(self.settings_frame, text="Image stretch:")
        stretch_label.grid(row=0, column=4, padx=(20, 5), pady=20, sticky="e")
        self.stretch_menu = ctk.CTkOptionMenu(
            self.settings_frame,
            values=["Linear", "Square root", "Logarithmic"],
            command=self.change_stretch,
        )
        self.stretch_menu.grid(row=0, column=5, padx=(5, 20), pady=20, sticky="w")

        limits_label = ctk.CTkLabel(self.settings_frame, text="Colourmap limits:")
        limits_label.grid(row=0, column=6, padx=(20, 5), pady=20, sticky="e")
        self.limits_menu = ctk.CTkOptionMenu(
            self.settings_frame,
            values=["grizli default", "Min-max", "99.9%", "99.5%", "99%", "98%", "95%"],
            command=self.change_limits,
        )
        self.limits_menu.grid(row=0, column=7, padx=(5, 20), pady=20, sticky="w")

        self.gal_id = int(gal_id)
        try:
            self.file_path = [
                *(
                    Path(self._root().full_config["files"]["extractions_dir"])
                    .expanduser()
                    .resolve()
                ).glob(f"*{int(gal_id):0>5}.stack.fits")
            ][0]
            self.generate_grid()
        except:
            self.file_path = None

        # if not hasattr(self, "gal_id"):

    def change_ext(self, event=None):
        # print (event)
        self.ext = event
        self.update_grid(force_update=True)

    def change_cmap(self, event=None):
        # print (event)
        self.cmap = event
        self.update_grid(force_update=True)

    def change_stretch(self, event=None):
        self.stretch = event
        self.update_grid(force_update=True)

    def change_limits(self, event=None):
        self.limits = event
        self.update_grid(force_update=True)

    def update_grid(self, force_update=False):
        print ("why though")
        # if self.gal_id == int(self._root().current_gal_id.get()) and not force_update:
        #     print("No need to panic.")
        # else:
        #     self.gal_id = int(self._root().current_gal_id.get())
        #     self.file_path = [
        #         *(
        #             Path(self._root().full_config["files"]["extractions_dir"])
        #             .expanduser()
        #             .resolve()
        #         ).glob(f"*{self.gal_id:0>5}.stack.fits")
        #     ][0]
        #     with pf.open(self.file_path) as hdul:
        #         header = hdul[0].header
        #         n_grism = header["NGRISM"]
        #         n_pa = np.nanmax(
        #             [
        #                 header[f"N{header[f'GRISM{n:0>3}']}"]
        #                 for n in range(1, n_grism + 1)
        #             ]
        #         )

            # # for n in range(1,header["NGRISM"]+1):
            # #     print (n)
            # #     print (header[f"GRISM{n:0>3}"])
            # #     print (header[f"N{header[f'GRISM{n:0>3}']}"])
            # for idx, beam_sub_frame in enumerate(self.beam_frame_list):
            #     # print (beam_sub_frame.ext, beam_sub_frame.extver)
            #     beam_sub_frame.ext = self.ext
            #     beam_sub_frame.cmap = self.cmap
            #     beam_sub_frame.stretch = self.stretch
            #     beam_sub_frame.limits = self.limits
            #     beam_sub_frame.update_plots()
            # # for row, col in np.ndindex(n_pa+1, n_grism):
            # #     flat_idx = np.ravel_multi_index((row, col), (n_pa+1, n_grism))
            # #     print (flat_idx)
            # # print ("sort this out")

    def generate_grid(self):
        with pf.open(self.file_path) as hdul:
            header = hdul[0].header
            n_grism = header["NGRISM"]
            n_pa = np.nanmax(
                [header[f"N{header[f'GRISM{n:0>3}']}"] for n in range(1, n_grism + 1)]
            )
            # for n in range(1,header["NGRISM"]+1):
            #     print (n)
            #     print (header[f"GRISM{n:0>3}"])
            #     print (header[f"N{header[f'GRISM{n:0>3}']}"])
            self.beam_frame_list = []
            # for 
            # This is where I'll set which pa is being used
            row = 0
            extver_list = []
            # for row, col in np.ndindex(n_pa, n_grism):
            for i in range(n_grism):
                # flat_idx = np.ravel_multi_index((row, col), (n_pa + 1, n_grism))
                # print (flat_idx)
                # print (row, col)
                # print (header[f"GRISM{col+1:0>3}"])
                # print (header)
                # if row != n_grism - 1:
                #     # print (header[f"{header[f'{header[f"GRISM{col+1:0>3}"]}{row+1:0>2}']}"])
                #     pa = "," + str(header[f'{header[f"GRISM{col+1:0>3}"]}{row+1:0>2}'])
                # else:
                #     pa = ""
                grism_name = header[f"GRISM{i+1:0>3}"]
                pa = "," + str(header[f'{grism_name}{row+1:0>2}'])
                extver = grism_name + pa
                print (extver)
                extver_list.append(extver)
                # self.beam_frame_list.append(
                #     BeamSubFrame(
                #         self,
                #         self.gal_id,
                #         extver=extver,
                #         ext=self.ext,
                #         cmap=self.cmap,
                #         limits=self.limits,
                #         stretch=self.stretch,  # height = self.main_tabs.tab("Beam view").winfo_height()/2
                #     )
                # )
                # self.beam_frame_list[flat_idx].grid(
                #     row=row + 1, column=col, sticky="ew"
                # )
                # print (hdul["SCI", header[f"GRISM{col+1:0>3}"]+pa])
            
            print (extver_list)
            self.beam_single_PA_frame = SinglePABeamFrame(self, extvers = extver_list)
            self.beam_single_PA_frame.grid(
                row=1, column=0, sticky="news"
            )
            # self.beam_single_PA_frame.place()
            print ("no?")

            self.grid_rowconfigure(1, weight=1)
            self.grid_columnconfigure(0, weight=1)
            # self.grid_columnconfigure((0,1,2), weight=1)
        # print (self.main_tabs.tab("Beam view").winfo_height())
        # for idx, name in enumerate(["F115W", "F150W", "F200W"]):
        #     self.beam_frame = BeamSubFrame(
        #         self, self.gal_id, extver=name+",72.0", ext="MODEL", #height = self.main_tabs.tab("Beam view").winfo_height()/2
        #     )
        #     # self.muse_spec_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        #     # self.beam_frame.pack(fill="both", expand=1)
        #     self.beam_frame.grid(row=0, column=idx, sticky="ew")
        # for idx, name in enumerate(["F115W", "F150W", "F200W"]):
        #     self.beam_frame = BeamSubFrame(
        #         self, self.gal_id, extver=name+",341.0", ext="MODEL"# height = self.main_tabs.tab("Beam view").winfo_height()/2
        #     )
        #     # self.muse_spec_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        #     # self.beam_frame.pack(fill="both", expand=1)
        #     self.beam_frame.grid(row=1, column=idx, sticky="ew")
        # for idx, name in enumerate(["F115W", "F150W", "F200W"]):
        #     self.beam_frame = BeamSubFrame(
        #         self, self.gal_id, extver=name, ext="MODEL",# height = self.main_tabs.tab("Beam view").winfo_height()/2,
        #     )
        #     # self.muse_spec_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        #     # self.beam_frame.pack(fill="both", expand=1)
        #     self.beam_frame.grid(row=2, column=idx, sticky="ew")


class BeamSubFrame(ctk.CTkFrame):
    def __init__(
        self,
        master,
        gal_id,
        extver,
        ext="SCI",
        cmap="plasma",
        stretch="Logarithmic",
        limits="grizli_default",
        **kwargs,
    ):
        super().__init__(master, **kwargs)

        self.gal_id = gal_id
        self.extver = extver
        self.ext = ext
        self.cmap = cmap
        self.stretch = stretch
        self.limits = limits
        # print (self)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.columnconfigure(1, weight=1)

        # print (dir(self))
        # self.grid_columnconfigure(0, weight=1)
        # self.grid_columnconfigure(1, weight=0)

        # self.scrollable_frame = ctk.CTkScrollableFrame(self)
        # self.scrollable_frame.grid(row=0, column=1, sticky="news")

        self.label = ctk.CTkLabel(self, text="Contamination:")
        self.label.grid(row=1, column=0, padx=10, pady=(10, 10), sticky="e")

        self.cont_value = ctk.StringVar(value="None")  # set initial value
        self.cont_menu = ctk.CTkOptionMenu(
            self,
            values=["None", "Mild", "Strong", "Incomplete trace"],
            command=self.optionmenu_callback,
            variable=self.cont_value,
        )
        self.cont_menu.grid(row=1, column=1, sticky="w")

        self.file_path = [
            *(
                Path(self._root().full_config["files"]["extractions_dir"])
                .expanduser()
                .resolve()
            ).glob(f"*{gal_id:0>5}.stack.fits")
        ][0]

        self.update_plots()

    def optionmenu_callback(choice):
        print("optionmenu dropdown clicked:", choice)

    def update_plots(self):
        if not hasattr(self, "fig_axes"):
            # self.pad_frame = tk.Frame(self, width=200, height=200, borderwidth=0, background="")
            # self.pad_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")#, padx=10, pady=20)

            # self.plot_frame = tk.Frame(
            #     self,
            #     bg = "blue",
            #     width = 300,
            #     height = 300,
            #     borderwidth=0,
            # )
            # self.plot_frame.rowconfigure(0,weight=1)
            # self.plot_frame.columnconfigure(0,weight=1)
            # calls function to fix the aspect ratio
            # self.set_aspect(self.plot_frame, self.pad_frame, aspect_ratio=5)
            self.fig = Figure(
                constrained_layout=True
                # , figsize=(2,1))
                ,
                figsize=(3, 1),
            )
            # print (self.master.winfo_height()/2)
            # print (self.master.winfo_width()/3)
            # self.fig.set_figsize(5,1)
            # print (self.fig.get_size_inches())
            self.pyplot_canvas = FigureCanvasTkAgg(
                figure=self.fig,
                master=self,
            )

            if not hasattr(self, "plotted_images"):
                self.plotted_images = dict()

            # with pf.open(self.file_path) as hdul:
            #     # print (hdul["SCI","F115W"])
            #     shape_sci = hdul.info(output=False)[
            #         hdul.index_of((self.ext, self.extver))
            #     ][5][0]
            #     shape_kernel = hdul.info(output=False)[
            #         hdul.index_of(("KERNEL", self.extver))
            #     ][5][0]
            #     # idx_kernel = hdul.index_of(("KERNEL",self.extver))
            #     # print (hdul.info(output=False))
            #     # print (hdul.info(output=False)[idx_sci])
            #     # print (shape_sci)
            #     # print (hdul["SCI",self.extver].data.shape)

            # self.fig.
            self.fig_axes = self.fig.subplots(
                1,
                2,
                sharey=True,
                # aspect="auto",
                # width_ratios=[1,shape_sci/shape_kernel],
                # width_ratios=[0.5,1]
                width_ratios=[1 / 3, 1],
            )

            if self.stretch.lower() == "linear":
                self.stretch_fn = LinearStretch
            elif self.stretch.lower() == "square root":
                self.stretch_fn = SqrtStretch
            elif self.stretch.lower() == "logarithmic":
                self.stretch_fn = LogStretch

            self.plot_kernel()
            self.plot_beam()
            self.fig.canvas.draw_idle()

            self.fig.canvas.get_tk_widget().grid(
                row=0, column=0, columnspan=2, sticky="news"
            )
            # self.fig.canvas.get_tk_widget().pack()
            # print (self.fig.canvas.get_tk_widget())
            # print (self.fig.get_size_inches())
            # print (self.fig_axes[0].get_aspect())
        else:
            # if self.gal_id != self._root().current_gal_id.get() or not hasattr(
            #     self, "pyplot_canvas"
            # ):
            self.gal_id = self._root().current_gal_id.get()

            if self.stretch.lower() == "linear":
                self.stretch_fn = LinearStretch
            elif self.stretch.lower() == "square root":
                self.stretch_fn = SqrtStretch
            elif self.stretch.lower() == "logarithmic":
                self.stretch_fn = LogStretch

            self.file_path = [
                *(
                    Path(self._root().full_config["files"]["extractions_dir"])
                    .expanduser()
                    .resolve()
                ).glob(f"*{self.gal_id:0>5}.stack.fits")
            ][0]

            self.plot_kernel()
            self.plot_beam()
            self.fig.canvas.draw_idle()

            self.fig.canvas.get_tk_widget().grid(
                row=0, column=0, columnspan=2, sticky="news"
            )

            self.update()

    def plot_kernel(self):
        try:
            self.plotted_images["kernel"].remove()
            del self.plotted_images["kernel"]
        except:
            pass
        with pf.open(self.file_path) as hdul:
            try:
                # print (hdul["SCI","F115W"])
                # print (hdul.info())
                data = hdul["KERNEL", self.extver].data
                # if hasattr(self.plotted_images, "kernel"):
                #     print (self.plotted_images["kernel"])
                #     self.plotted_images["kernel"].remove()

                if self.limits == "grizli default":
                    vmax_kern = 1.1 * np.percentile(data, 99.5)
                    interval = ManualInterval(vmin=-0.1 * vmax_kern, vmax=vmax_kern)

                norm = ImageNormalize(
                    data,
                    #  interval=MinMaxInterval(),
                    stretch=self.stretch_fn(),
                )
                self.plotted_images["kernel"] = self.fig_axes[0].imshow(
                    data,
                    origin="lower",
                    cmap=self.cmap,
                    # aspect="auto"
                    norm=norm,
                )
                self.fig_axes[0].set_xticklabels("")
                self.fig_axes[0].set_yticklabels("")
                self.fig_axes[0].tick_params(direction="in")
            except Exception as e:
                print(e)
                pass

    def plot_beam(self):
        try:
            self.plotted_images["beam"].remove()
            del self.plotted_images["beam"]
        except:
            pass
        with pf.open(self.file_path) as hdul:
            try:
                # print (hdul["SCI","F115W"])
                # print (hdul.info())
                if self.ext == "RESIDUALS":
                    data = hdul["SCI", self.extver].data
                    m = hdul["MODEL", self.extver].data
                else:
                    data = hdul[self.ext, self.extver].data
                    m = 0

                if self.limits == "grizli default":
                    # print ("oh boy")
                    wht_i = hdul["WHT", self.extver]
                    clip = wht_i.data > 0
                    if clip.sum() == 0:
                        clip = np.isfinite(wht_i.data)

                    avg_rms = 1 / np.median(np.sqrt(wht_i.data[clip]))
                    vmax = np.maximum(1.1 * np.percentile(data[clip], 98), 5 * avg_rms)
                    vmin = -0.1 * vmax
                    interval = ManualInterval(vmin=vmin, vmax=vmax)

                norm = ImageNormalize(
                    data,
                    interval=interval,
                    stretch=self.stretch_fn(),
                )
                self.plotted_images["beam"] = self.fig_axes[1].imshow(
                    data - m,
                    origin="lower",
                    cmap=self.cmap,
                    aspect="auto",
                    norm=norm,
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
            except:
                pass


class SinglePABeamFrame(ctk.CTkFrame):
    def __init__(
        self,
        master,
        extvers,
        **kwargs,
    ):
        super().__init__(master, **kwargs)

        # self.gal_id = gal_id
        # self.extver = extver
        # self.ext = ext
        # self.cmap = cmap
        # self.stretch = stretch
        # self.limits = limits
        self.rowconfigure(0, weight=1)
        # self.rowconfigure(1, weight=0)
        self.columnconfigure(0, weight=1)

        # print (dir(self.place()))
        # self.grid_columnconfigure(0, weight=1)
        # self.grid_columnconfigure(1, weight=0)


        self.pad_frame = ctk.CTkFrame(self, fg_color="blue")
        self.pad_frame.grid(row=0, column=0, sticky="news")
        self.canvas_frame = ctk.CTkFrame(self.pad_frame, fg_color="red")
        self.canvas_frame.grid(row=0, column=0, sticky="news")

        self.set_aspect()

        self.fig = Figure(
            constrained_layout=True,
            # figsize=(1,1),
        )
        self.pyplot_canvas = FigureCanvasTkAgg(
            figure=self.fig,
            master=self.canvas_frame,
        )
        print ("Canvas created")

        self.extvers = extvers
        widths = [1 / 3, 1]*len(self.extvers)
        # self.fig_axes = self.fig.add_subplot(111)
        self.fig_axes = self.fig.subplots(
            4,
            2*len(self.extvers),
            sharey=True,
            # aspect="auto",
            # width_ratios=[1,shape_sci/shape_kernel],
            # width_ratios=[0.5,1]
            width_ratios=widths,
        )
        # self.extver = extvers[0]
        # print (self.extver)

        self.cont_frame = ctk.CTkFrame(self,fg_color="red")
        self.cont_frame.grid(row=1, column=0, sticky="ew")

        self.label = ctk.CTkLabel(self.cont_frame, text="Contamination:")
        self.label.grid(row=0, column=0, padx=10, pady=(10, 10), sticky="e")
        self.cont_value = ctk.StringVar(value="None")  # set initial value
        self.cont_menu = ctk.CTkOptionMenu(
            self.cont_frame,
            values=["None", "Mild", "Strong", "Incomplete trace"],
            command=self.optionmenu_callback,
            variable=self.cont_value,
        )
        self.cont_menu.grid(row=0, column=1, sticky="w")
        # print (master.file_path)
        # print (self.master)

        # self.file_path = [
        #     *(
        #         Path(self._root().full_config["files"]["extractions_dir"])
        #         .expanduser()
        #         .resolve()
        #     ).glob(f"*{gal_id:0>5}.stack.fits")
        # ][0]
        self.plotted_images = dict()
        self.update_plots()

    def set_aspect(self, aspect_ratio=3):
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
            self.canvas_frame.place(in_=self.pad_frame, x=0, y=0, 
                relwidth=desired_width/event.width, relheight=desired_height/event.height)

        self.pad_frame.bind("<Configure>", enforce_aspect_ratio)

    def optionmenu_callback(choice):
        print("optionmenu dropdown clicked:", choice)

    def update_plots(self):
        self.master.gal_id = self._root().current_gal_id.get()

        if self.master.stretch.lower() == "linear":
            self.stretch_fn = LinearStretch
        elif self.master.stretch.lower() == "square root":
            self.stretch_fn = SqrtStretch
        elif self.master.stretch.lower() == "logarithmic":
            self.stretch_fn = LogStretch
        for j, name in enumerate(["SCI", "CONTAM", "MODEL", "RESIDUALS"]):
            for i, ver in enumerate(self.extvers):
                if name+ver not in self.plotted_images.keys():
                    self.plotted_images[name+ver] = dict()
                self.plot_kernel(self.fig_axes[j,2*i], name, ver)
                # print (name)
                self.plot_beam(self.fig_axes[j,(2*i)+1], name, ver)
        self.fig.canvas.draw_idle()

        self.fig.canvas.get_tk_widget().pack(fill="both", expand=1)

        self.update()

    def plot_kernel(self, ax, ext, extver):
        try:
            self.plotted_images[ext+extver]["kernel"].remove()
            del self.plotted_images[ext+extver]["kernel"]
        except:
            pass
        with pf.open(self.master.file_path) as hdul:
            try:
                data = hdul["KERNEL", extver].data

                if self.master.limits == "grizli default":
                    vmax_kern = 1.1 * np.percentile(data, 99.5)
                    interval = ManualInterval(vmin=-0.1 * vmax_kern, vmax=vmax_kern)

                norm = ImageNormalize(
                    data,
                    #  interval=MinMaxInterval(),
                    stretch=self.stretch_fn(),
                )
                self.plotted_images[ext+extver]["kernel"] = ax.imshow(
                    data,
                    origin="lower",
                    cmap=self.master.cmap,
                    # aspect="auto"
                    norm=norm,
                )
                ax.set_xticklabels("")
                ax.set_yticklabels("")
                ax.tick_params(direction="in")
                if ax in self.fig_axes[:,0]:
                    ax.set_ylabel(ext)
            except Exception as e:
                print("error", e)
                pass

    def plot_beam(self, ax, ext, extver):
        try:
            self.plotted_images[ext+extver]["beam"].remove()
            del self.plotted_images[ext+extver]["beam"]
        except Exception as e:
            # print ("Error here", e)
            pass
        with pf.open(self.master.file_path) as hdul:
            try:
                # print (hdul["SCI","F115W"])
                # print (hdul.info())
                if ext == "RESIDUALS":
                    data = hdul["SCI", extver].data
                    m = hdul["MODEL", extver].data
                else:
                    data = hdul[ext, extver].data
                    m = 0
                
                header = hdul["SCI", extver].header
                # wavelengths = ((np.arange(data.shape[1]) + 1.0) - header["CRPIX1"]) * header["CD1_1"] + header["CRVAL1"]
                # print (wavelengths)
                extent = [header['WMIN'], header['WMAX'], 0, data.shape[0]]

                if self.master.limits == "grizli default":
                    # print ("oh boy")
                    wht_i = hdul["WHT", extver]
                    clip = wht_i.data > 0
                    if clip.sum() == 0:
                        clip = np.isfinite(wht_i.data)

                    avg_rms = 1 / np.median(np.sqrt(wht_i.data[clip]))
                    vmax = np.maximum(1.1 * np.percentile(data[clip], 98), 5 * avg_rms)
                    vmin = -0.1 * vmax
                    interval = ManualInterval(vmin=vmin, vmax=vmax)

                norm = ImageNormalize(
                    data,
                    interval=interval,
                    stretch=self.stretch_fn(),
                )
                self.plotted_images[ext+extver]["beam"] = ax.imshow(
                    data - m,
                    origin="lower",
                    cmap=self.master.cmap,
                    aspect="auto",
                    norm=norm,
                    extent=extent,
                )
                ax.tick_params(direction="in")

                if ax not in self.fig_axes[-1]:
                    ax.set_xticklabels("")
                    ax.set_yticklabels("")
                else:
                    ax.set_xlabel(r'$\lambda$ ($\mu$m) - '+extver.split(",")[0])
            except Exception as e:
                print (e)
                pass

class MultiContamFrame(customtkinter.CTkFrame):
    def __init__(self, master, values, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.values = values
        self.title = title
        self.checkboxes = []

        self.title = customtkinter.CTkLabel(self, text=self.title, fg_color="gray30", corner_radius=6)
        self.title.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")

        for i, value in enumerate(self.values):
            checkbox = customtkinter.CTkCheckBox(self, text=value)
            checkbox.grid(row=i+1, column=0, padx=10, pady=(10, 0), sticky="w")
            self.checkboxes.append(checkbox)

    def get(self):
        checked_checkboxes = []
        for checkbox in self.checkboxes:
            if checkbox.get() == 1:
                checked_checkboxes.append(checkbox.cget("text"))
        return checked_checkboxes