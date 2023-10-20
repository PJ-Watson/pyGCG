import tkinter as tk
from pathlib import Path

import astropy.io.fits as pf
import astropy.units as u
import customtkinter as ctk
import matplotlib as mpl
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.table import Table
from astropy.visualization import (
    ImageNormalize,
    LinearStretch,
    LogStretch,
    ManualInterval,
    MinMaxInterval,
    PercentileInterval,
    SqrtStretch,
)
from astropy.wcs import WCS
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from tqdm import tqdm


class BeamFrame(ctk.CTkFrame):
    def __init__(self, master, gal_id, PA, **kwargs):
        super().__init__(master, **kwargs)

        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.grid(
            row=0,
            column=0,
            columnspan=3,
            sticky="ew",
        )
        self.PA = PA

        cmap_label = ctk.CTkLabel(self.settings_frame, text="Colourmap:")
        cmap_label.grid(row=0, column=2, padx=(20, 5), pady=10, sticky="e")
        self.cmap_menu = ctk.CTkOptionMenu(
            self.settings_frame,
            values=[
                "plasma",
                "plasma_r",
                "viridis",
                "viridis_r",
                "jet",
                "binary",
                "binary_r",
            ],
            command=self.change_cmap,
        )
        self.cmap_menu.grid(row=0, column=3, padx=(5, 20), pady=10, sticky="w")
        self.cmap_menu.set(self._root().plot_options["cmap"])

        stretch_label = ctk.CTkLabel(self.settings_frame, text="Image stretch:")
        stretch_label.grid(row=0, column=4, padx=(20, 5), pady=10, sticky="e")
        self.stretch_menu = ctk.CTkOptionMenu(
            self.settings_frame,
            values=["Linear", "Square root", "Logarithmic"],
            command=self.change_stretch,
        )
        self.stretch_menu.set(self._root().plot_options["cmap"])
        self.stretch_menu.grid(row=0, column=5, padx=(5, 20), pady=10, sticky="w")

        limits_label = ctk.CTkLabel(self.settings_frame, text="Colourmap limits:")
        limits_label.grid(row=0, column=6, padx=(20, 5), pady=10, sticky="e")
        self.limits_menu = ctk.CTkOptionMenu(
            self.settings_frame,
            values=[
                "grizli default",
                "Min-max",
                "99.9%",
                "99.5%",
                "99%",
                "98%",
                "95%",
                "90%",
            ],
            command=self.change_limits,
        )
        self.limits_menu.set(self._root().plot_options["limits"])
        self.limits_menu.grid(row=0, column=7, padx=(5, 20), pady=10, sticky="w")

        self.gal_id = gal_id
        try:
            pad = self._root().config.get("catalogue", {}).get("seg_id_length", 5)
            self.file_path = [
                *(
                    Path(self._root().config["files"]["extractions_dir"])
                    .expanduser()
                    .resolve()
                ).glob(f"*{self._root().seg_id:0>{pad}}.stack.fits")
            ][0]
        except:
            self.file_path = None

        # print (self.master)
        # if self._root().main_tabs.get() in self._root().tab_names[0:2]:
        # print ("yes")
        self.generate_grid()

    def change_cmap(self, event=None):
        self._root().plot_options["cmap"] = event
        self.update_grid(force_update=True)

    def change_stretch(self, event=None):
        self._root().plot_options["stretch"] = event
        self.update_grid(force_update=True)

    def change_limits(self, event=None):
        self._root().plot_options["limits"] = event
        self.update_grid(force_update=True)

    def update_grid(self, force_update=False):
        if self.gal_id == self._root().current_gal_id.get() and not force_update:
            self.beam_single_PA_frame.quality_frame.save_current()
            for k, v in self.beam_single_PA_frame.coverage.items():
                self._root().current_gal_data[k]["coverage"] = v
            pass
        else:
            self.gal_id = self._root().current_gal_id.get()
            pad = self._root().config.get("catalogue", {}).get("seg_id_length", 5)
            self.file_path = [
                *(
                    Path(self._root().config["files"]["extractions_dir"])
                    .expanduser()
                    .resolve()
                ).glob(f"*{self._root().seg_id:0>{pad}}.stack.fits")
            ][0]
            with pf.open(self.file_path) as hdul:
                header = hdul[0].header
                n_grism = len(self._root().filter_names)
                n_pa = len(self._root().PAs)
                self.beam_frame_list = []
                extver_list = []
                for i in range(n_grism):
                    try:
                        grism_name = self._root().filter_names[::-1][i]
                        extver = grism_name + f",{self.PA}"
                    except:
                        extver = "none"
                    extver_list.append(extver)
                self.beam_single_PA_frame.update_plots(extvers=extver_list)

            self.update()

    def generate_grid(self):
        with pf.open(self.file_path) as hdul:
            header = hdul[0].header
            n_grism = header["NGRISM"]
            n_pa = np.nanmax(
                [header[f"N{header[f'GRISM{n:0>3}']}"] for n in range(1, n_grism + 1)]
            )
            self.beam_frame_list = []
            row = 0
            extver_list = []
            for i in range(n_grism):
                grism_name = header[f"GRISM{i+1:0>3}"]
                pa = "," + str(header[f"{grism_name}{row+1:0>2}"])
                extver = grism_name + pa
                extver = grism_name + f",{self.PA}"
                extver_list.append(extver)
            self.beam_single_PA_frame = SinglePABeamFrame(self, extvers=extver_list)
            self.beam_single_PA_frame.grid(row=1, column=0, sticky="news")

            self.grid_rowconfigure(1, weight=1)
            self.grid_columnconfigure(0, weight=1)


class SinglePABeamFrame(ctk.CTkFrame):
    def __init__(
        self,
        master,
        extvers,
        **kwargs,
    ):
        super().__init__(master, **kwargs)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.pad_frame = ctk.CTkFrame(self)  # , fg_color="red")
        self.pad_frame.grid(row=0, column=0, sticky="news")
        self.canvas_frame = ctk.CTkFrame(self.pad_frame)  # , fg_color="blue")
        self.canvas_frame.grid(row=0, column=0, sticky="news")
        self.canvas_frame.rowconfigure(0, weight=1)
        self.canvas_frame.columnconfigure(0, weight=1)

        self.fig = Figure(
            constrained_layout=True,
        )
        self.pyplot_canvas = FigureCanvasTkAgg(
            figure=self.fig,
            master=self.canvas_frame,
        )

        self.check_axes_colours()

        # plt.style.use("dark_background")

        self.extvers = extvers
        self.coverage = {}
        widths = [1 / 3, 1] * len(self.extvers)
        self.fig_axes = self.fig.subplots(
            4,
            2 * len(self.extvers),
            sharey=True,
            width_ratios=widths,
        )

        self.quality_frame = MultiQualityFrame(self.canvas_frame, extvers=self.extvers)
        self.quality_frame.grid(row=1, column=0, sticky="ew")

        self.set_aspect()
        self.plotted_images = dict()
        self.update_plots()

    def check_axes_colours(self):
        self.fig.set_facecolor("none")
        if ctk.get_appearance_mode() == "Dark":
            self.fig.canvas.get_tk_widget().config(bg=self.cget("bg_color")[-1])
            fg_colour = [
                a / 65535
                for a in self._root().winfo_rgb(
                    self._root().progress_status.cget("text_color")[-1]
                )
            ]
        if ctk.get_appearance_mode() == "Light":
            self.fig.canvas.get_tk_widget().config(bg=self.cget("bg_color")[0])
            fg_colour = [
                a / 65535
                for a in self._root().winfo_rgb(
                    self._root().progress_status.cget("text_color")[0]
                )
            ]

        mpl.rcParams["text.color"] = fg_colour
        mpl.rcParams["axes.labelcolor"] = fg_colour
        mpl.rcParams["xtick.color"] = fg_colour
        mpl.rcParams["ytick.color"] = fg_colour
        mpl.rcParams["axes.edgecolor"] = fg_colour

    def set_aspect(self, aspect_ratio=3):
        # a function which places a frame within a containing frame, and
        # then forces the inner frame to keep a specific aspect ratio

        def enforce_aspect_ratio(event):
            # when the pad window resizes, fit the content into it,
            # either by fixing the width or the height and then
            # adjusting the height or width based on the aspect ratio.

            other_heights = self.quality_frame.winfo_height()
            # start by using the width as the controlling dimension
            desired_width = event.width
            desired_height = int(event.width / aspect_ratio) + other_heights

            # if the window is too tall to fit, use the height as
            # the controlling dimension
            if desired_height > event.height:
                desired_height = event.height
                desired_width = int((event.height - other_heights) * aspect_ratio)

            # place the window, giving it an explicit size
            self.canvas_frame.place(
                in_=self.pad_frame,
                x=0,
                y=0,
                relwidth=desired_width / event.width,
                relheight=desired_height / event.height,
            )

        self.pad_frame.bind("<Configure>", enforce_aspect_ratio)

    def update_plots(self, extvers=None):
        import time

        t1 = time.perf_counter()
        self.check_axes_colours()

        if extvers != None:
            self.extvers = extvers
            self.quality_frame.reload_extvers(new_extvers=self.extvers)

        self.master.gal_id = self._root().current_gal_id.get()

        if self._root().plot_options["stretch"].lower() == "linear":
            self.stretch_fn = LinearStretch
        elif self._root().plot_options["stretch"].lower() == "square root":
            self.stretch_fn = SqrtStretch
        elif self._root().plot_options["stretch"].lower() == "logarithmic":
            self.stretch_fn = LogStretch

        for j, name in enumerate(["SCI", "CONTAM", "MODEL", "RESIDUALS"]):
            for i, ver in enumerate(self.extvers):
                if name + ver not in self.plotted_images.keys():
                    self.plotted_images[name + ver] = dict()
                self.plot_kernel(self.fig_axes[j, 2 * i], name, ver)
                self.plot_beam(self.fig_axes[j, (2 * i) + 1], name, ver)

        # print("T2:", time.perf_counter() - t1)

        self.fig.canvas.draw_idle()

        self.fig.canvas.get_tk_widget().grid(row=0, column=0, sticky="news")

        # print("T3:", time.perf_counter() - t1)

    def plot_kernel(self, ax, ext, extver):
        with pf.open(self.master.file_path) as hdul:
            try:
                data = hdul["KERNEL", extver].data

                if self._root().plot_options["limits"] == "grizli default":
                    vmax_kern = 1.1 * np.percentile(data, 99.5)
                    interval = ManualInterval(vmin=-0.1 * vmax_kern, vmax=vmax_kern)
                elif self._root().plot_options["limits"] == "Min-max":
                    interval = MinMaxInterval()
                else:
                    interval = PercentileInterval(
                        float(self._root().plot_options["limits"].replace("%", ""))
                    )

                norm = ImageNormalize(
                    data,
                    interval=interval,
                    stretch=self.stretch_fn(),
                )
                try:
                    self.plotted_images[ext + extver]["kernel"].set_data(data)
                    self.plotted_images[ext + extver]["kernel"].set_norm(norm)
                    self.plotted_images[ext + extver]["kernel"].set_cmap(
                        self._root().plot_options["cmap"]
                    )
                    self.plotted_images[ext + extver]["kernel"].set_visible(True)
                except Exception as e:
                    self.plotted_images[ext + extver]["kernel"] = ax.imshow(
                        data,
                        origin="lower",
                        cmap=self._root().plot_options["cmap"],
                        # aspect="auto"
                        norm=norm,
                        visible=True,
                        interpolation="nearest",
                    )
                ax.set_xticklabels("")
                ax.set_yticklabels("")
                ax.tick_params(axis="both", direction="in", top=True, right=True)
                if ax in self.fig_axes[:, 0]:
                    ax.set_ylabel(ext)
            except Exception as e:
                if "kernel" in self.plotted_images[ext + extver].keys():
                    self.plotted_images[ext + extver]["kernel"].set_visible(False)
                pass

    def plot_beam(self, ax, ext, extver):
        with pf.open(self.master.file_path) as hdul:
            try:
                if ext == "RESIDUALS":
                    data = hdul["SCI", extver].data
                    m = hdul["MODEL", extver].data
                else:
                    data = hdul[ext, extver].data
                    m = 0

                if ext == "SCI":
                    self.coverage[extver] = (
                        1
                        - np.sum(np.all((~np.isfinite(data)) | (data == 0), axis=0))
                        / data.shape[1]
                    )
                    self._root().current_gal_data[extver]["coverage"] = self.coverage[
                        extver
                    ]

                header = hdul["SCI", extver].header
                extent = [header["WMIN"], header["WMAX"], 0, data.shape[0]]

                if self._root().plot_options["limits"] == "grizli default":
                    wht_i = hdul["WHT", extver]
                    clip = wht_i.data > 0
                    if clip.sum() == 0:
                        clip = np.isfinite(wht_i.data)

                    avg_rms = 1 / np.median(np.sqrt(wht_i.data[clip]))
                    vmax = np.maximum(1.1 * np.percentile(data[clip], 98), 5 * avg_rms)
                    vmin = -0.1 * vmax
                    interval = ManualInterval(vmin=vmin, vmax=vmax)
                elif self._root().plot_options["limits"] == "Min-max":
                    interval = MinMaxInterval()
                else:
                    interval = PercentileInterval(
                        float(self._root().plot_options["limits"].replace("%", ""))
                    )

                norm = ImageNormalize(
                    data,
                    interval=interval,
                    stretch=self.stretch_fn(),
                )
                try:
                    self.plotted_images[ext + extver]["beam"].set_data(data - m)
                    self.plotted_images[ext + extver]["beam"].set_norm(norm)
                    self.plotted_images[ext + extver]["beam"].set_cmap(
                        self._root().plot_options["cmap"]
                    )
                    self.plotted_images[ext + extver]["beam"].set_visible(True)
                except:
                    self.plotted_images[ext + extver]["beam"] = ax.imshow(
                        data - m,
                        origin="lower",
                        cmap=self._root().plot_options["cmap"],
                        aspect="auto",
                        norm=norm,
                        extent=extent,
                        visible=True,
                        interpolation="nearest",
                    )
                ax.tick_params(axis="both", direction="in", top=True, right=True)

                if ax not in self.fig_axes[-1]:
                    ax.set_xticklabels("")
                    ax.set_yticklabels("")
                else:
                    ax.set_xlabel(r"$\lambda$ ($\mu$m) - " + extver.split(",")[0])
                try:
                    self.plotted_images[ext + extver]["beam_failed"].set_visible(False)
                except:
                    pass
            except KeyError as e:
                # print (e)
                try:
                    self.plotted_images[ext + extver]["beam_failed"].set_visible(True)
                except Exception as e:
                    # print (e)

                    self.plotted_images[ext + extver]["beam_failed"] = ax.text(
                        0.5,
                        0.5,
                        "No data",
                        transform=ax.transAxes,
                        ha="center",
                        va="center",
                        c=self._root().text_colour,
                    )
                try:
                    self.plotted_images[ext + extver]["beam"].set_visible(False)
                except:
                    pass
                self._root().current_gal_data[extver]["coverage"] = 0.0
                self.quality_frame.quality_menus[extver].set("Unusable")
                self.quality_frame.quality_menus[extver].configure(state="disabled")
            except Exception as e:
                print("beam:", e)
                pass


class MultiQualityFrame(ctk.CTkFrame):
    def __init__(self, master, extvers, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.extvers = extvers
        self.quality_menus = {}

        self.possible_values = ["Excellent", "Good", "Poor", "Unusable"]

        for i, e in enumerate(
            self.extvers,
        ):
            label = ctk.CTkLabel(self, text="Beam Quality")
            label.grid(row=0, column=2 * i, padx=10, pady=(10, 0), sticky="e")
            q_menu = ctk.CTkOptionMenu(
                self,
                values=self.possible_values,
                command=self.save_current,
            )
            try:
                q_menu.set(self._root().current_gal_data[e]["quality"])
            except:
                q_menu.set("Good")
            q_menu.grid(row=0, column=2 * i + 1, padx=10, pady=(10, 0), sticky="w")
            self.quality_menus[e] = q_menu

        self.save_current()

    def keypress_select(self, event, key_maps):
        if event.char in key_maps:
            idx = (event.char == key_maps).nonzero()
            self._root().current_gal_data[self.extvers[int(idx[0])]][
                "quality"
            ] = self.possible_values[int(idx[1])]
            self.quality_menus[self.extvers[int(idx[0])]].set(
                self.possible_values[int(idx[1])]
            )

    def reload_extvers(self, new_extvers=None):
        if self.extvers != None:
            self.extvers = new_extvers

        for e, c in zip(self.extvers, self.quality_menus.values()):
            try:
                c.set(self._root().current_gal_data[e]["quality"])
            except:
                c.set("Good")
            c.configure(state="normal")

        self.save_current()

    def save_current(self, event=None):
        for v, q in zip(self.extvers, self.quality_menus.values()):
            if v not in self._root().current_gal_data.keys():
                self._root().current_gal_data[v] = {}
            self._root().current_gal_data[v]["quality"] = q.get()
