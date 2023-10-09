import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import matplotlib.colors as colors
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from pathlib import Path
import astropy.io.fits as pf
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u
from tqdm import tqdm
import numpy as np
from photutils.aperture import (
    aperture_photometry,
    SkyCircularAperture,
    CircularAperture,
)
from astropy.visualization import (
    make_lupton_rgb,
    MinMaxInterval,
    SqrtStretch,
    ImageNormalize,
    LinearStretch,
    LogStretch,
    ManualInterval,
    PercentileInterval,
)
from astropy.table import Table
from astropy.convolution import convolve, Gaussian1DKernel


class SpecFrame(ctk.CTkFrame):
    def __init__(self, master, gal_id, **kwargs):
        super().__init__(master, **kwargs)

        if gal_id == "":
            return
        self.gal_id = gal_id
        self.plotted_components = dict(emission={}, absorption={})
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.grid(row=0, column=1, rowspan=2, sticky="news")
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        self.reference_lines_label = ctk.CTkLabel(
            self.scrollable_frame, text="Show reference lines:"
        )
        self.reference_lines_label.grid(row=0, padx=10, pady=(10, 0), sticky="w")
        self.emission_checkbox = ctk.CTkCheckBox(
            self.scrollable_frame, text="Emission", command=self.change_lines
        )
        self.emission_checkbox.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")
        self.absorption_checkbox = ctk.CTkCheckBox(
            self.scrollable_frame, text="Absorption", command=self.change_lines
        )
        self.absorption_checkbox.grid(
            row=2, column=0, padx=20, pady=(10, 0), sticky="w"
        )

        self.redshift_frame = ctk.CTkFrame(self.scrollable_frame)
        self.redshift_frame.grid(row=3, sticky="ew")
        self.redshift_frame.columnconfigure([0, 1], weight=1)
        self.redshift_label = ctk.CTkLabel(self.redshift_frame, text="Redshift:")
        self.redshift_label.grid(
            row=0, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="w"
        )
        self.current_redshift = ValidateFloatVar(
            master=self,
            value=0,
        )
        self.redshift_entry = ctk.CTkEntry(
            self.redshift_frame,
            textvariable=self.current_redshift,
        )
        self.redshift_entry.grid(
            row=1,
            column=0,
            padx=(20, 10),
            pady=(10, 0),
            sticky="we",
        )
        self.redshift_entry.bind(
            "<Return>",
            self.update_lines,
        )
        self.reset_redshift_button = ctk.CTkButton(
            self.redshift_frame, text="Reset", command=self.reset_redshift
        )
        self.reset_redshift_button.grid(
            row=1,
            column=1,
            padx=(20, 10),
            pady=(10, 0),
            sticky="we",
        )
        self.redshift_slider = ctk.CTkSlider(
            self.redshift_frame,
            from_=0,
            to=2,
            command=self.update_lines,
            number_of_steps=200,
        )
        self.redshift_slider.grid(
            row=2,
            column=0,
            columnspan=2,
            padx=(20, 10),
            pady=10,
            sticky="we",
        )

        self.muse_checkbox = ctk.CTkCheckBox(
            self.scrollable_frame, text="MUSE spectrum", command=self.change_components
        )
        self.muse_checkbox.grid(row=4, column=0, padx=20, pady=(10, 0), sticky="w")
        self.grizli_checkbox = ctk.CTkCheckBox(
            self.scrollable_frame,
            text="NIRISS spectrum",
            command=self.change_components,
        )
        self.grizli_checkbox.select()
        self.grizli_checkbox.grid(row=5, column=0, padx=20, pady=(10, 0), sticky="w")
        self.grizli_temp_checkbox = ctk.CTkCheckBox(
            self.scrollable_frame,
            text="Grizli templates",
            command=self.change_components,
        )
        self.grizli_temp_checkbox.grid(
            row=6, column=0, padx=20, pady=(10, 0), sticky="w"
        )
        self.grizli_temp_checkbox.select()

        self.images_frame = ImagesFrame(self, gal_id=self.gal_id)
        self.images_frame.grid(row=2, column=0, columnspan=1, sticky="news")

        if self._root().main_tabs.get() == "Spec view":
            self.update_plot()

    def update_plot(self):
        if not hasattr(self, "pyplot_canvas"):
            self.gal_id = self._root().current_gal_id.get()

            self.fig = Figure(constrained_layout=True)
            self.pyplot_canvas = FigureCanvasTkAgg(
                figure=self.fig,
                master=self,
            )

            self.fig_axes = self.fig.add_subplot(111)

            self.fig.canvas.mpl_connect("motion_notify_event", self.hover)

            toolbar = NavigationToolbar2Tk(self.fig.canvas, self, pack_toolbar=False)
            toolbar.update()

            self.fig_axes.set_xlabel(r"Wavelength (${\rm \AA}$)")
            self.fig_axes.set_ylabel("Flux")

            self.custom_annotation = self.fig_axes.annotate(
                "", xy=(0, 0), xytext=(0, 0), textcoords="offset points"
            )
            self.custom_annotation.set_visible(False)

            self._update_all()

            self.add_lines()

            f = zoom_factory(self.fig_axes)

            self.pyplot_canvas.draw_idle()

            self.pyplot_canvas.get_tk_widget().grid(row=0, column=0, sticky="news")
            toolbar.grid(row=1, column=0, sticky="news")

        if self.gal_id != self._root().current_gal_id.get():
            self.gal_id = self._root().current_gal_id.get()
            self._update_all()
            self.update_lines()
            self.pyplot_canvas.draw()
            self.update()

    def _update_all(self):
        _row_path = [
            *(
                Path(self._root().config["files"]["extractions_dir"])
                .expanduser()
                .resolve()
            ).glob(f"*{self._root().seg_id:0>5}.row.fits")
        ][0]
        with pf.open(_row_path) as hdul:
            self.grizli_redshift = Table(hdul[1].data)["redshift"].value[0]
            self._root().current_gal_data["grizli_redshift"] = self.grizli_redshift
            self._root().current_gal_data["estimated_redshift"] = self.grizli_redshift
            self.current_redshift.set(self.grizli_redshift)
            self.redshift_slider.set(self.grizli_redshift)

        self.cube_path = (
            Path(self._root().config["files"]["cube_path"]).expanduser().resolve()
        )
        if not self.cube_path.is_file():
            self.muse_checkbox.configure(state="disabled")
        else:
            self.muse_checkbox.configure(state="normal")

        if self.grizli_checkbox.get():
            self.plot_grizli()
        if self.grizli_temp_checkbox.get():
            self.plot_grizli(templates=True)
        if self.muse_checkbox.get():
            self.plot_MUSE_spec()
        try:
            # tab_row = self._root().cat[self._root().id_col == self.gal_id]
            # # self.fig_axes.set_title(
            # #     f"IDs: v3={tab_row['v3_id'].value}, Xin={tab_row['Xin_id'].value}, NIRCAM={tab_row['NIRCAM_id'].value}"
            # # )
            self.fig_axes.set_title(f"ID={self.gal_id}")
        except Exception as e:
            # print(e)
            pass
        self.images_frame.update_images()

    def plot_grizli(self, templates=False):
        file_path = [
            *(
                Path(self._root().config["files"]["extractions_dir"])
                .expanduser()
                .resolve()
            ).glob(f"*{self._root().seg_id:0>5}.1D.fits")
        ][0]

        if templates:
            dict_key = "grism_templates"
        else:
            dict_key = "grisms"

        ymax = 0
        colours = {
            "F115W": "C0",
            "F150W": "C1",
            "F200W": "C2",
        }

        if dict_key not in self.plotted_components.keys():
            self.plotted_components[dict_key] = dict()
        else:
            try:
                for v in self.plotted_components[dict_key].values():
                    v.remove()
            except:
                pass
        with pf.open(file_path) as hdul:
            for hdu in hdul[1:]:
                data_table = Table(hdu.data)
                clip = data_table["err"] > 0
                if clip.sum() == 0:
                    clip = np.isfinite(data_table["err"])
                if templates:
                    (self.plotted_components[dict_key][hdu.name],) = self.fig_axes.plot(
                        data_table["wave"][clip],
                        data_table["line"][clip] / data_table["flat"][clip] / 1e-19,
                        c="tab:red",
                        alpha=0.7,
                    )
                else:
                    try:
                        y_vals = (
                            data_table["flux"][clip]
                            / data_table["flat"][clip]
                            / data_table["pscale"][clip]
                            / 1e-19
                        )
                        y_err = (
                            data_table["err"][clip]
                            / data_table["flat"][clip]
                            / data_table["pscale"][clip]
                            / 1e-19
                        )
                    except:
                        y_vals = (
                            data_table["flux"][clip] / data_table["flat"][clip] / 1e-19
                        )
                        y_err = (
                            data_table["err"][clip] / data_table["flat"][clip] / 1e-19
                        )
                    self.plotted_components[dict_key][
                        hdu.name
                    ] = self.fig_axes.errorbar(
                        data_table["wave"][clip],
                        y_vals,
                        yerr=y_err,
                        fmt="o",
                        markersize=3,
                        ecolor=colors.to_rgba(colours[hdu.name], 0.5),
                        c=colours[hdu.name],
                    )
                    ymax = np.nanmax([ymax, np.nanmax(y_vals)])

        if not templates:
            self.fig_axes.set_ylim(ymin=-0.05 * ymax, ymax=1.05 * ymax)

    def plot_MUSE_spec(
        self,
    ):
        if not self.cube_path.is_file():
            return
        if "MUSE_spec" in self.plotted_components.keys():
            for line in self.fig_axes.get_lines():
                if line == self.plotted_components["MUSE_spec"]:
                    line.remove()

        with pf.open(cube_path) as cube_hdul:
            cube_wcs = WCS(cube_hdul[1].header)

            wavelengths = (
                (np.arange(cube_hdul[1].header["NAXIS3"]) + 1.0)
                - cube_hdul[1].header["CRPIX3"]
            ) * cube_hdul[1].header["CD3_3"] + cube_hdul[1].header["CRVAL3"]
            MUSE_spec = self.cube_extract_spectra(
                cube_hdul[1].data,
                cube_wcs,
                self._root().tab_row[self._root().config["cat"].get("ra", "ra")],
                self._root().tab_row[self._root().config["cat"].get("dec", "dec")],
                # radius=tab_row["r50_SE"][0],
            )

            (self.plotted_components["MUSE_spec"],) = self.fig_axes.plot(
                wavelengths,
                MUSE_spec
                / np.nanmedian(MUSE_spec)
                * np.nanmedian(self.fig_axes.get_ylim()),
                linewidth=0.5,
                c="k",
            )

    def cube_extract_spectra(
        self,
        data_cube,
        cube_wcs,
        ra,
        dec,
        radius=0.5,
        cube_error=None,
        kernel_sig=5,
    ):
        # temp_dir = (
        #     Path(self._root().config["files"]["temp_dir"]).expanduser().resolve()
        # )
        try:
            with pf.open(
                self.temp_dir
                / f"{ra[0]:.6f}_{dec[0]:.6f}_r{radius:.6f}_c{kernel_sig:.3f}.fits"
            ) as hdul:
                return hdul[0].data
        except Exception as e:
            print(e)
            try:
                ra.unit
                dec.unit
                sc = SkyCoord(
                    ra=ra,
                    dec=dec,
                )
            except:
                sc = SkyCoord(
                    ra=ra * u.deg,
                    dec=dec * u.deg,
                )
            try:
                radius.unit
                assert radius.unit is not None, ValueError
            except:
                print("failed")
                radius *= u.arcsec

            pix_c = np.hstack(sc.to_pixel(cube_wcs.celestial)[:])
            pix_r = radius / np.sqrt(cube_wcs.celestial.proj_plane_pixel_area()).to(
                radius.unit
            )

            aperture = CircularAperture(
                pix_c,
                pix_r.value,
            )

            spectrum = np.zeros(data_cube.shape[0])
            for i, cube_slice in tqdm(
                enumerate(data_cube[:]),
                desc="Extracting wavelength slice",
                total=len(spectrum),
            ):
                spectrum[i] = aperture_photometry(
                    cube_slice, aperture, error=cube_error
                )["aperture_sum"]

            kernel = Gaussian1DKernel(kernel_sig)
            spectrum = convolve(spectrum, kernel)

            new_hdul = pf.HDUList()
            new_hdul.append(
                pf.ImageHDU(data=spectrum, header=cube_wcs.spectral.to_header())
            )
            new_hdul.writeto(
                self.temp_dir
                / f"{ra[0]:.6f}_{dec[0]:.6f}_r{radius.value:.6f}_c{kernel_sig:.3f}.fits"
            )

            return spectrum

    def add_lines(
        self,
        line_type=None,
    ):
        if line_type is None:
            return
        xlims = self.fig_axes.get_xlim()
        for line_key, line_data in self._root().config["lines"][line_type].items():
            self.plotted_components[line_type][line_key] = self.fig.get_axes()[
                0
            ].axvline(
                line_data["centre"] * float(self.current_redshift.get()),
                c="0.7",
                alpha=0.7,
                linewidth=2,
            )

        self.fig_axes.set_xlim(xlims)
        self.pyplot_canvas.draw()

    def update_lines(self, event=None):
        if type(event) == float:
            self.current_redshift.set(np.round(event, decimals=8))
        else:
            self.redshift_slider.set(float(self.current_redshift.get()))

        self._root().current_gal_data["estimated_redshift"] = float(
            self.current_redshift.get()
        )
        for line_type in ["emission", "absorption"]:
            try:
                for line_key, line_data in (
                    self._root().config["lines"][line_type].items()
                ):
                    current_line = self.plotted_components[line_type][line_key]
                    current_line.set_data(
                        [
                            line_data["centre"]
                            * (1 + float(self.current_redshift.get())),
                            line_data["centre"]
                            * (1 + float(self.current_redshift.get())),
                        ],
                        [0, 1],
                    )
            except:
                pass

        self.fig.canvas.draw()
        self.update()

    def reset_redshift(self):
        self.current_redshift.set(self.grizli_redshift)
        self.redshift_slider.set(self.grizli_redshift)
        self.update_lines()

    def change_components(self, event=None):
        if self.muse_checkbox.get():
            self.plot_MUSE_spec()
        elif "MUSE_spec" in self.plotted_components.keys():
            self.plotted_components["MUSE_spec"].remove()
            del self.plotted_components["MUSE_spec"]

        if self.grizli_checkbox.get():
            self.plot_grizli()
        elif "grisms" in self.plotted_components.keys():
            for v in self.plotted_components["grisms"].values():
                v.remove()
            del self.plotted_components["grisms"]

        if self.grizli_temp_checkbox.get():
            self.plot_grizli(templates=True)
        elif "grism_templates" in self.plotted_components.keys():
            for v in self.plotted_components["grism_templates"].values():
                v.remove()
            del self.plotted_components["grism_templates"]

        self.pyplot_canvas.draw()
        self.update()

    def change_lines(self):
        if (
            self.emission_checkbox.get()
            and len(self.plotted_components["emission"]) == 0
        ):
            self.add_lines(line_type="emission")
            self.update_lines()
        elif (
            not self.emission_checkbox.get()
            and len(self.plotted_components["emission"]) > 0
        ):
            for line in self.fig_axes.get_lines():
                if line in self.plotted_components["emission"].values():
                    line.remove()
            for line_key, line_data in self._root().config["lines"]["emission"].items():
                del self.plotted_components["emission"][line_key]

        if (
            self.absorption_checkbox.get()
            and len(self.plotted_components["absorption"]) == 0
        ):
            self.add_lines(line_type="absorption")
            self.update_lines()
        elif (
            not self.absorption_checkbox.get()
            and len(self.plotted_components["absorption"]) > 0
        ):
            for line in self.fig_axes.get_lines():
                if line in self.plotted_components["absorption"].values():
                    line.remove()
            for line_key, line_data in (
                self._root().config["lines"]["absorption"].items()
            ):
                del self.plotted_components["absorption"][line_key]

        self.pyplot_canvas.draw()
        self.update()

    def hover(self, event):
        if event.inaxes == self.fig_axes:
            for line_type in ["emission", "absorption"]:
                if len(self.plotted_components[line_type]) > 0:
                    for line_key, line_data in (
                        self._root().config["lines"][line_type].items()
                    ):
                        if self.plotted_components[line_type][line_key].contains(event)[
                            0
                        ]:
                            self.custom_annotation.xy = [event.xdata, event.ydata]
                            self.custom_annotation.set_text(
                                self._root().config["lines"][line_type][line_key][
                                    "latex_name"
                                ]
                            )

                            self.custom_annotation.set_visible(True)
                            self.fig.canvas.draw()
                            return
        self.custom_annotation.set_visible(False)
        self.fig.canvas.draw()


# based on https://gist.github.com/tacaswell/3144287
def zoom_factory(ax, base_scale=1.1):
    """
    Add ability to zoom with the scroll wheel.


    Parameters
    ----------
    ax : matplotlib axes object
        axis on which to implement scroll to zoom
    base_scale : float
        how much zoom on each tick of scroll wheel

    Returns
    -------
    disconnect_zoom : function
        call this to disconnect the scroll listener
    """

    def limits_to_range(lim):
        return lim[1] - lim[0]

    fig = ax.get_figure()  # get the figure of interest
    if hasattr(fig.canvas, "capture_scroll"):
        fig.canvas.capture_scroll = True
    has_toolbar = hasattr(fig.canvas, "toolbar") and fig.canvas.toolbar is not None
    if has_toolbar:
        toolbar = fig.canvas.toolbar
        toolbar.push_current()

    def zoom_fun(event):
        if event.inaxes is not ax:
            return
        # get the current x and y limits
        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()
        cur_yrange = limits_to_range(cur_ylim)
        cur_xrange = limits_to_range(cur_xlim)
        xdata = event.xdata  # get event x location
        ydata = event.ydata  # get event y location

        if event.button == "up":
            # deal with zoom in
            scale_factor = base_scale
        elif event.button == "down":
            # deal with zoom out
            scale_factor = 1 / base_scale
        else:
            # deal with something that should never happen
            scale_factor = 1
        # set new limits
        new_xlim = [
            xdata - (xdata - cur_xlim[0]) / scale_factor,
            xdata + (cur_xlim[1] - xdata) / scale_factor,
        ]
        new_ylim = [
            ydata - (ydata - cur_ylim[0]) / scale_factor,
            ydata + (cur_ylim[1] - ydata) / scale_factor,
        ]

        new_yrange = limits_to_range(new_ylim)
        new_xrange = limits_to_range(new_xlim)
        ax.set_xlim(new_xlim)
        ax.set_ylim(new_ylim)

        if has_toolbar:
            toolbar.push_current()
        ax.figure.canvas.draw_idle()  # force re-draw

    # attach the call back
    cid = fig.canvas.mpl_connect("scroll_event", zoom_fun)

    def disconnect_zoom():
        fig.canvas.mpl_disconnect(cid)

    # return the disconnect function
    return disconnect_zoom


# From https://stackoverflow.com/questions/4140437/
class ValidateFloatVar(ctk.StringVar):
    """StringVar subclass that only allows valid float values to be put in it."""

    def __init__(self, master=None, value=None, name=None):
        ctk.StringVar.__init__(self, master, value, name)
        self._old_value = self.get()
        self.trace("w", self._validate)

    def _validate(self, *_):
        new_value = self.get()
        try:
            new_value == "" or float(new_value)
            self._old_value = new_value
        except ValueError:
            ctk.StringVar.set(self, self._old_value)


class ImagesFrame(ctk.CTkFrame):
    def __init__(self, master, gal_id, **kwargs):
        super().__init__(master, **kwargs)

        self.gal_id = gal_id

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.update_seg_path()
        self.update_rgb_path()

        self.fig = Figure(
            constrained_layout=True,
            figsize=(10, 2),
        )
        self.pyplot_canvas = FigureCanvasTkAgg(
            figure=self.fig,
            master=self,
        )
        self.fig.set_facecolor("none")
        self.pyplot_canvas.get_tk_widget().config(bg=self.cget("bg_color")[-1])
        self.fig_axes = self.fig.subplots(
            1,
            5,
            sharey=True,
            # aspect="auto",
            # width_ratios=[1,shape_sci/shape_kernel],
            # width_ratios=[0.5,1]
        )
        for a in self.fig_axes:
            a.set_xticklabels("")
            a.set_yticklabels("")
            a.tick_params(axis="both", direction="in", top=True, right=True)

        self.default_cmap = colors.ListedColormap(["C1", "C0", "C2", "C3", "C4", "C5"])

        self.plotted_components = {}

        self.fig.canvas.draw_idle()

        self.fig.canvas.get_tk_widget().grid(row=0, column=0, sticky="news")

        if self._root().main_tabs.get() == "Spec view":
            self.plot_seg_map()

    def update_seg_path(self, pattern="*seg.fits"):
        self.seg_path = [
            *(
                Path(self._root().config["files"]["prep_dir"]).expanduser().resolve()
            ).glob(pattern)
        ]
        if len(self.seg_path) == 0:
            print("Segmentation map not found.")
            self.seg_path = None
        else:
            self.seg_path = self.seg_path[0]

    def update_rgb_path(self):
        self.rgb_paths = []
        for p in self._root().filter_names:
            rgb_path = [
                *(
                    Path(self._root().config["files"]["prep_dir"])
                    .expanduser()
                    .resolve()
                ).glob(f"*{p.lower()}_drz_sci.fits")
            ]
            if len(rgb_path) == 0:
                print(f"{p} image not found.")
                self.rgb_paths.append(None)
            else:
                self.rgb_paths.append(rgb_path[0])

    def plot_images(self, border=5):
        if self.seg_path is None and all(x is None for x in self.rgb_paths):
            print("No images to plot.")
            for a, f in zip(self.fig_axes[:-2][::-1], self._root().filter_names):
                self.plotted_components[f"{f}_text"] = a.text(
                    0.5,
                    0.5,
                    f,
                    transform=a.transAxes,
                    ha="center",
                    va="center",
                    c="k",
                )
            self.plotted_components[f"rgb_text"] = self.fig_axes[-2].text(
                0.5,
                0.5,
                "No images found.",
                transform=self.fig_axes[-2].transAxes,
                ha="center",
                va="center",
                c="k",
            )
            self.plotted_components[f"seg_text"] = self.fig_axes[-1].text(
                0.5,
                0.5,
                "Segmentation map\nnot found.",
                transform=self.fig_axes[-1].transAxes,
                ha="center",
                va="center",
                c="k",
            )

            return
        if self.seg_path is not None:
            for k, v in self.plotted_components.items():
                v.remove()
            self.plotted_components = {}
            with pf.open(self.seg_path) as hdul:
                seg_wcs = WCS(hdul[0].header)
                seg_data = hdul[0].data

                y_c, x_c = extract_pixel_ra_dec(
                    self._root().tab_row,
                    seg_wcs,
                    key_ra=self._root().config["cat"].get("ra", "ra"),
                    key_dec=self._root().config["cat"].get("dec", "dec"),
                ).value

                location = np.where(seg_data == self._root().seg_id)
                width = np.nanmax(location[0]) - np.nanmin(location[0])
                height = np.nanmax(location[1]) - np.nanmin(location[1])

                if width > height:
                    w_d = 0
                    h_d = (width - height) / 2
                elif height > width:
                    h_d = 0
                    w_d = (height - width) / 2
                else:
                    w_d, h_d = 0, 0

                self.cutout_dimensions = [
                    int(
                        np.clip(
                            np.nanmin(location[0]) - border - w_d, 0, seg_data.shape[0]
                        )
                    ),
                    int(
                        np.clip(
                            np.nanmax(location[0]) + border + w_d, 0, seg_data.shape[0]
                        )
                    ),
                    int(
                        np.clip(
                            np.nanmin(location[1]) - border - h_d, 0, seg_data.shape[1]
                        )
                    ),
                    int(
                        np.clip(
                            np.nanmax(location[1]) + border + h_d, 0, seg_data.shape[1]
                        )
                    ),
                ]
                cutout = seg_data[
                    self.cutout_dimensions[0] : self.cutout_dimensions[1],
                    self.cutout_dimensions[2] : self.cutout_dimensions[3],
                ].astype(float)
                cutout[cutout == 0] = np.nan

                cutout_copy = cutout % 5 + 1
                cutout_copy[cutout == float(self._root().seg_id)] = 0

                self.plotted_components["seg"] = self.fig_axes[-1].imshow(
                    cutout_copy,
                    origin="lower",
                    cmap=self.default_cmap,
                    aspect="equal",
                    extent=[0, cutout_copy.shape[0], 0, cutout_copy.shape[1]],
                )
                self.fig_axes[-1].set_xlim(xmax=cutout_copy.shape[0])
                self.fig_axes[-1].set_ylim(ymax=cutout_copy.shape[1])

                self.plotted_components["seg_marker"] = self.fig_axes[-1].scatter(
                    y_c
                    - int(
                        np.clip(
                            np.nanmin(location[1]) - border - h_d, 0, seg_data.shape[1]
                        )
                    ),
                    x_c
                    - int(
                        np.clip(
                            np.nanmin(location[0]) - border - w_d, 0, seg_data.shape[0]
                        )
                    ),
                    marker="P",
                    c="k",
                )
        if not all(x is None for x in self.rgb_paths):
            self.rgb_data = np.empty(
                (
                    3,
                    self.cutout_dimensions[1] - self.cutout_dimensions[0],
                    self.cutout_dimensions[3] - self.cutout_dimensions[2],
                )
            )

            for i, v in enumerate(self.rgb_paths):
                with pf.open(v) as hdul:
                    self.rgb_data[i] = hdul[0].data[
                        self.cutout_dimensions[0] : self.cutout_dimensions[1],
                        self.cutout_dimensions[2] : self.cutout_dimensions[3],
                    ] * 10 ** ((hdul[0].header["ZP"] - 25) / 2.5)

            self.rgb_stretched = make_lupton_rgb(
                self.rgb_data[0],
                self.rgb_data[1],
                self.rgb_data[2],
                stretch=0.1,  # Q=10
            )
            self.plotted_components["rgb"] = self.fig_axes[-2].imshow(
                self.rgb_stretched,
                origin="lower",
                aspect="equal",
                extent=[0, self.rgb_stretched.shape[0], 0, self.rgb_stretched.shape[1]],
            )
            self.fig_axes[-2].set_xlim(xmax=self.rgb_stretched.shape[0])
            self.fig_axes[-2].set_ylim(ymax=self.rgb_stretched.shape[1])

            vmax = np.nanmax(
                [1.1 * np.percentile(self.rgb_data, 98), 5 * np.std(self.rgb_data)]
            )
            vmin = -0.1 * vmax
            interval = ManualInterval(vmin=vmin, vmax=vmax)
            for a, d, f in zip(
                self.fig_axes[:-2][::-1], self.rgb_data, self._root().filter_names
            ):
                norm = ImageNormalize(
                    d,
                    interval=interval,
                    stretch=SqrtStretch(),
                )
                self.plotted_components[f] = a.imshow(
                    d,
                    origin="lower",
                    cmap="binary",
                    aspect="equal",
                    extent=[0, d.shape[0], 0, d.shape[1]],
                    norm=norm,
                )
                self.plotted_components[f"{f}_text"] = a.text(
                    0.05, 0.95, f, transform=a.transAxes, ha="left", va="top", c="red"
                )

        # self.fig_axes.set_facecolor("0.7")

        self.pyplot_canvas.draw_idle()
        self.update()

    def update_images(self, force=False):
        if (
            self.gal_id != self._root().current_gal_id.get()
            or force
            or len(self.plotted_components) == 0
        ):
            self.gal_id = self._root().current_gal_id.get()
            self.plot_images()


def extract_pixel_radius(q_table, celestial_wcs, key="flux_radius"):
    # The assumption is that SExtractor radii are typically measured in pixel units
    radius = q_table[key]
    if hasattr(radius, "unit") and radius.unit != None:
        radius = radius.value * radius.unit  # Avoiding problems with columns
        if radius.unit == u.pix:
            pass
        elif u.get_physical_type(radius) == "dimensionless":
            radius *= u.pix
        elif u.get_physical_type(radius) == "angle":
            pixel_scale = (
                np.sqrt(celestial_wcs.proj_plane_pixel_area()).to(u.arcsec) / u.pix
            )
            radius /= pixel_scale
        else:
            raise ValueError(
                "The units of this radius cannot be automatically converted."
            )
    else:
        print("Radius has no unit, assuming pixels.")
        if hasattr(radius, "value"):
            radius = radius.value * u.pix
        else:
            radius = radius * u.pix

    return radius


def extract_pixel_ra_dec(q_table, celestial_wcs, key_ra="ra", key_dec="dec"):
    try:
        orig_ra = q_table[key_ra]
        orig_dec = q_table[key_dec]
    except:
        print(
            "No match found for supplied ra, dec keys. Performing automatic search instead."
        )
        lower_colnames = np.array([x.lower() for x in q_table.colnames])
        for r, d in [[key_ra, key_dec], ["ra", "dec"]]:
            possible_names = []
            for n in lower_colnames:
                if d.lower() in n:
                    possible_names.append(n)
            possible_names = sorted(possible_names, key=lambda x: (len(x), x))
            for n in possible_names:
                r_poss = n.replace(d.lower(), r.lower())
                if r_poss in lower_colnames:
                    orig_ra = q_table[
                        q_table.colnames[int((lower_colnames == r_poss).nonzero()[0])]
                    ]
                    orig_dec = q_table[
                        q_table.colnames[int((lower_colnames == n).nonzero()[0])]
                    ]
                    break
            else:
                continue
            break

    def check_deg(orig):
        if hasattr(orig, "unit") and orig.unit != None:
            new = orig.value * orig.unit  # Avoiding problems with columns
            if new.unit == u.pix:
                return new
            elif u.get_physical_type(new) == "dimensionless":
                new *= u.deg
            if u.get_physical_type(new) == "angle":
                new = new.to(u.deg)
        else:
            print("Coordinate has no unit, assuming degrees.")
            if hasattr(orig, "value"):
                new = orig.value * u.deg
            else:
                new = orig * u.deg
        return new

    new_ra, new_dec = check_deg(orig_ra), check_deg(orig_dec)
    if new_ra.unit == u.pix:
        print(new_ra, new_dec)
        return new_ra, new_dec

    sc = SkyCoord(new_ra, new_dec)
    pix_c = np.hstack(sc.to_pixel(celestial_wcs)[:]) * u.pix
    return pix_c

    # return new_ra, new_dec
