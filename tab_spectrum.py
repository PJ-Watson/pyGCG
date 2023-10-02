import customtkinter as ctk
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
from astropy.table import Table


class SpecFrame(ctk.CTkFrame):
    def __init__(self, master, gal_id, **kwargs):
        super().__init__(master, **kwargs)

        self.gal_id = int(gal_id)
        self.plotted_components = dict(emission={}, absorption={})
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.grid(row=0, column=1, sticky="news")
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

        self.redshift_label = ctk.CTkLabel(self.scrollable_frame, text="Redshift:")
        self.redshift_label.grid(row=3, padx=10, pady=(10, 0), sticky="w")
        self.current_redshift = ctk.DoubleVar(
            master=self,
            value=0,
        )

        self.redshift_entry = ctk.CTkEntry(
            self.scrollable_frame,
            textvariable=self.current_redshift,
        )
        self.redshift_entry.grid(
            row=4,
            column=0,
            padx=(20, 10),
            pady=(10, 0),
            sticky="we",
        )
        self.redshift_entry.bind(
            "<Return>",
            self.update_lines,
        )
        self.redshift_slider = ctk.CTkSlider(
            self.scrollable_frame,
            variable=self.current_redshift,
            from_=0,
            to=2,
            # orientation="horizontal",
            command=self.update_lines,
            # border_width=20,
        )
        self.redshift_slider.grid(
            row=5,
            column=0,
            # padx=(10,10),
            # padx=(30,40),
            # padx=(10,0),
            # padx=(0,20),
            padx=(20, 10),
            pady=10,
            sticky="we",
        )

        self.muse_checkbox = ctk.CTkCheckBox(
            self.scrollable_frame, text="MUSE spectrum", command=self._test_event
        )
        self.muse_checkbox.grid(
            row=6, column=0, padx=20, pady=(10, 0), sticky="w"
        )
        self.grizli_checkbox = ctk.CTkCheckBox(
            self.scrollable_frame, text="NIRISS spectrum", command=self._test_event
        )
        self.grizli_checkbox.select()
        self.grizli_checkbox.grid(
            row=7, column=0, padx=20, pady=(10, 0), sticky="w"
        )
        self.grizli_temp_checkbox = ctk.CTkCheckBox(
            self.scrollable_frame, text="Grizli templates", command=self._test_event
        )
        self.grizli_temp_checkbox.grid(
            row=8, column=0, padx=20, pady=(10, 0), sticky="w"
        )
            

    def _test_event(self, event=None):
        # checkboxes = 
        if self.muse_checkbox.get():
            self.plot_MUSE_spec(
                gal_id=self.gal_id,
            )
            self.pyplot_canvas.draw()
        else:
            if "MUSE_spec" in self.plotted_components.keys():
                self.plotted_components["MUSE_spec"].remove()
                del self.plotted_components["MUSE_spec"]
            self.pyplot_canvas.draw()
            self.update()
        
        if self.grizli_checkbox.get():
            self.plot_grizli(
                gal_id=self.gal_id,
            )
            self.pyplot_canvas.draw()
        else:
            if "grisms" in self.plotted_components.keys():
                for v in self.plotted_components["grisms"].values():
                    v.remove()
                del self.plotted_components["grisms"]
            self.pyplot_canvas.draw()
            self.update()

        if self.grizli_temp_checkbox.get():
            self.plot_grizli(
                gal_id=self.gal_id,
                templates=True,
            )
            self.pyplot_canvas.draw()
        else:
            if "grism_templates" in self.plotted_components.keys():
                for v in self.plotted_components["grism_templates"].values():
                    v.remove()
                del self.plotted_components["grism_templates"]
            self.pyplot_canvas.draw()
            self.update()

    def change_lines(self):
        if self.emission_checkbox.get() and len(self.plotted_components["emission"]) == 0:
            self.add_lines(line_type="emission")
            self.update_lines()
        elif (
            not self.emission_checkbox.get() and len(self.plotted_components["emission"]) > 0
        ):
            for line in self.fig_axes.get_lines():
                if line in self.plotted_components["emission"].values():
                    line.remove()
            for line_key, line_data in (
                self._root().full_config["lines"]["emission"].items()
            ):
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
                self._root().full_config["lines"]["absorption"].items()
            ):
                del self.plotted_components["absorption"][line_key]

        self.pyplot_canvas.draw()
        self.update()

    def update_plot(self):
        if not hasattr(self, "pyplot_canvas"):
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

            _path = [
                *(
                    Path(self._root().full_config["files"]["extractions_dir"])
                    .expanduser()
                    .resolve()
                ).glob(f"*{self.gal_id:0>5}.row.fits")
            ][0]
            with pf.open(_path) as hdul:
                self.current_redshift.set(Table(hdul[1].data)["redshift"].value[0])

            if self.grizli_checkbox.get():
                self.plot_grizli(
                    gal_id=int(self._root().current_gal_id.get()),
                )
            if self.grizli_temp_checkbox.get():
                self.plot_grizli(
                    gal_id=int(self._root().current_gal_id.get()),
                    templates=True,
                )
            if self.muse_checkbox.get():
                self.plot_MUSE_spec(
                    gal_id=int(self._root().current_gal_id.get()),
                )
            self.add_lines()

            self.gal_id = int(self._root().current_gal_id.get())

            f = zoom_factory(self.fig_axes)

            self.pyplot_canvas.draw_idle()

            self.pyplot_canvas.get_tk_widget().grid(row=0, column=0, sticky="news")
            toolbar.grid(row=1, column=0, sticky="news")

        if self.gal_id != int(self._root().current_gal_id.get()):
            print ("running this")
            self.gal_id = int(self._root().current_gal_id.get())

            _path = [
                *(
                    Path(self._root().full_config["files"]["extractions_dir"])
                    .expanduser()
                    .resolve()
                ).glob(f"*{self.gal_id:0>5}.row.fits")
            ][0]
            with pf.open(_path) as hdul:
                self.current_redshift.set(Table(hdul[1].data)["redshift"].value[0])

            if self.grizli_checkbox.get():
                self.plot_grizli(
                    gal_id=int(self._root().current_gal_id.get()),
                )
            if self.grizli_temp_checkbox.get():
                self.plot_grizli(
                    gal_id=int(self._root().current_gal_id.get()),
                    templates=True,
                )
            if self.muse_checkbox.get():
                self.plot_MUSE_spec(
                    gal_id=int(self._root().current_gal_id.get()),
                )
            self.update_lines()
            try:
                tab_row = self._root().cat[self._root().cat["v3_id"] == int(self.gal_id)]
                self.fig_axes.set_title(
                    f"IDs: v3={tab_row['v3_id'].value}, Xin={tab_row['Xin_id'].value}, NIRCAM={tab_row['NIRCAM_id'].value}"
                )
                # print (tab_row['v3_id'])
            except Exception as e:
                print (e)
                pass
            self.pyplot_canvas.draw()

            self.update()

    def plot_grizli(
        self,
        gal_id,
        templates=False
    ):
        file_path = [
            *(
                Path(self._root().full_config["files"]["extractions_dir"])
                .expanduser()
                .resolve()
            ).glob(f"*{gal_id:0>5}.1D.fits")
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
            for v in self.plotted_components[dict_key].values():
                v.remove()
        with pf.open(file_path) as hdul:
            for hdu in hdul[1:]:
                # print (hdu)
                data_table = Table(hdu.data)
                # print (self.clip*len(data_table["wave"]))
                # print (np.percentile(data_table["flux"]/data_table["flat"]/1e-19,[1,99]))
                # print (hdu.name)
                clip = data_table["err"] > 0
                if clip.sum() == 0:
                    clip = np.isfinite(data_table["err"])
                if templates:
                    (self.plotted_components[dict_key][hdu.name],) = self.fig_axes.plot(
                        data_table["wave"][clip],
                        data_table["line"][clip] / data_table["flat"][clip] / 1e-19,
                        c="tab:red",
                        alpha=0.7
                    )
                else:
                    y_vals = data_table["flux"][clip] / data_table["flat"][clip] / data_table["pscale"][clip] / 1e-19
                    self.plotted_components[dict_key][hdu.name] = self.fig_axes.errorbar(
                        data_table["wave"][clip],
                        y_vals,
                        yerr=data_table["err"][clip] / data_table["flat"][clip] /data_table["pscale"][clip] / 1e-19,
                        fmt="o",
                        markersize=3,
                        ecolor=colors.to_rgba(colours[hdu.name], 0.5),
                        c=colours[hdu.name],
                    )
                # print (self.plotted_grisms[hdu.name])
                # print (self.fig_axes.get_children())
                    ymax = np.nanmax([ymax, np.nanmax(y_vals)])

        if not templates:
            self.fig_axes.set_ylim(ymin=-0.05 * ymax, ymax=1.05 * ymax)

    def plot_MUSE_spec(
        self,
        gal_id,
    ):
        cube_path = (
            Path(self._root().full_config["files"]["cube_path"]).expanduser().resolve()
        )
        if not cube_path.is_file():
            print("no cube file")
            return
        if "MUSE_spec" in self.plotted_components.keys():
            for line in self.fig_axes.get_lines():
                if line == self.plotted_components["MUSE_spec"]:
                    line.remove()

        with pf.open(cube_path) as cube_hdul:
            tab_row = self._root().cat[self._root().cat["v3_id"] == gal_id]

            cube_wcs = WCS(cube_hdul[1].header)

            wavelengths = (
                (np.arange(cube_hdul[1].header["NAXIS3"]) + 1.0)
                - cube_hdul[1].header["CRPIX3"]
            ) * cube_hdul[1].header["CD3_3"] + cube_hdul[1].header["CRVAL3"]
            # print (tab_row)
            MUSE_spec = self.cube_extract_spectra(
                cube_hdul[1].data,
                cube_wcs,
                tab_row["v3_ra"],
                tab_row["v3_dec"],
                radius=tab_row["r50_SE"][0],
            )
            # if not hasattr(self, "plotted_components"):
            #     self.plotted_components = dict(emission={}, absorption={})

            # self.fig.clear()
            # ax = self.fig.add_subplot(111)

            # self.fig.canvas.mpl_connect("motion_notify_event", self.hover)

            (self.plotted_components["MUSE_spec"],) = self.fig_axes.plot(
                wavelengths,
                MUSE_spec
                / np.nanmedian(MUSE_spec)
                * np.nanmedian(self.fig_axes.get_ylim()),
                linewidth=0.5,
                c="k",
            )
            # self.fig_axes.set_title(
            #     f"IDs: v3={tab_row['v3_id'][0]}, Xin={tab_row['Xin_id'][0]}, NIRCAM={tab_row['NIRCAM_id'][0]}"
            # )

    def cube_extract_spectra(
        self,
        data_cube,
        cube_wcs,
        ra,
        dec,
        radius=0.5,
        cube_error=None,
    ):
        temp_dir = (
            Path(self._root().full_config["files"]["temp_dir"]).expanduser().resolve()
        )
        try:
            with pf.open(
                temp_dir / f"{ra[0]:.6f}_{dec[0]:.6f}_r{radius:.6f}.fits"
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
            # print (radius)
            # print (radius.unit)

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

            new_hdul = pf.HDUList()
            new_hdul.append(
                pf.ImageHDU(data=spectrum, header=cube_wcs.spectral.to_header())
            )
            new_hdul.writeto(
                temp_dir / f"{ra[0]:.6f}_{dec[0]:.6f}_r{radius.value:.6f}.fits"
            )

            return spectrum

    def add_lines(
        self,
        line_type=None,
    ):
        if line_type is None:
            return
        xlims = self.fig_axes.get_xlim()
        for line_key, line_data in self._root().full_config["lines"][line_type].items():
            self.plotted_components[line_type][line_key] = self.fig.get_axes()[0].axvline(
                line_data["centre"] * self.current_redshift.get(),
                c="0.7",
                alpha=0.7,
                linewidth=2,
            )

        self.fig_axes.set_xlim(xlims)
        self.pyplot_canvas.draw()

    def update_lines(self, event=None):
        for line_type in ["emission", "absorption"]:
            try:
                for line_key, line_data in (
                    self._root().full_config["lines"][line_type].items()
                ):
                    current_line = self.plotted_components[line_type][line_key]
                    current_line.set_data(
                        [
                            line_data["centre"] * (1 + self.current_redshift.get()),
                            line_data["centre"] * (1 + self.current_redshift.get()),
                        ],
                        [0, 1],
                    )
            except:
                pass

        self.fig.canvas.draw()

    def hover(self, event):
        if event.inaxes == self.fig_axes:
            for line_type in ["emission", "absorption"]:
                if len(self.plotted_components[line_type]) > 0:
                    for line_key, line_data in (
                        self._root().full_config["lines"][line_type].items()
                    ):
                        if self.plotted_components[line_type][line_key].contains(event)[0]:
                            self.custom_annotation.xy = [event.xdata, event.ydata]
                            self.custom_annotation.set_text(
                                self._root().full_config["lines"][line_type][line_key][
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
        # it might be possible to have an interactive backend without
        # a toolbar. I'm not sure so being safe here
        toolbar = fig.canvas.toolbar
        toolbar.push_current()
    # orig_xlim = ax.get_xlim()
    # orig_ylim = ax.get_ylim()
    # orig_yrange = limits_to_range(orig_ylim)
    # orig_xrange = limits_to_range(orig_xlim)
    # orig_center = ((orig_xlim[0] + orig_xlim[1]) / 2, (orig_ylim[0] + orig_ylim[1]) / 2)

    def zoom_fun(event):
        if event.inaxes is not ax:
            return
        # get the current x and y limits
        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()
        cur_yrange = limits_to_range(cur_ylim)
        cur_xrange = limits_to_range(cur_xlim)
        # cur_center = ((orig_xlim[0] + orig_xlim[1]) / 2, (orig_ylim[0] + orig_ylim[1]) / 2)
        # set the range
        # (cur_xlim[1] - cur_xlim[0]) * 0.5
        # (cur_ylim[1] - cur_ylim[0]) * 0.5
        xdata = event.xdata  # get event x location
        ydata = event.ydata  # get event y location

        # print (f"Current position: ({xdata},{ydata}).")
        # print (f"Current limits: ([{cur_xlim}],[{cur_ylim}]).")

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
        # print (f"New limits: ([{new_xlim}],[{new_ylim}]).")

        new_yrange = limits_to_range(new_ylim)
        new_xrange = limits_to_range(new_xlim)

        # print (f"Old range, f{orig_xrange}")
        # print (f"New range, f{new_xrange}")

        # if np.abs(new_yrange) > np.abs(orig_yrange):
        #     new_ylim = orig_center[1] - new_yrange / 2, orig_center[1] + new_yrange / 2
        # if np.abs(new_xrange) > np.abs(orig_xrange):
        #     new_xlim = orig_center[0] - new_xrange / 2, orig_center[0] + new_xrange / 2
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