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
from astropy.table import Table
from astropy.convolution import convolve, Gaussian1DKernel


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

        self.seg_frame = SegMapFrame(self.scrollable_frame, gal_id=self.gal_id)
        self.seg_frame.grid(row=7,column=0, sticky="news")
        self.scrollable_frame.grid_rowconfigure(7, weight=1)

        if self._root().main_tabs.get()=="Spec view":
            self.update_plot()

    def update_plot(self):
        if not hasattr(self, "pyplot_canvas"):
            self.gal_id = int(self._root().current_gal_id.get())

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

        if self.gal_id != int(self._root().current_gal_id.get()):
            self.gal_id = int(self._root().current_gal_id.get())
            self._update_all()
            self.update_lines()
            self.pyplot_canvas.draw()
            self.update()

    def _update_all(self):
        _path = [
            *(
                Path(self._root().full_config["files"]["extractions_dir"])
                .expanduser()
                .resolve()
            ).glob(f"*{self.gal_id:0>5}.row.fits")
        ][0]
        with pf.open(_path) as hdul:
            self.grizli_redshift = Table(hdul[1].data)["redshift"].value[0]
            self.current_redshift.set(self.grizli_redshift)
            self.redshift_slider.set(self.grizli_redshift)

        if self.grizli_checkbox.get():
            self.plot_grizli()
        if self.grizli_temp_checkbox.get():
            self.plot_grizli(templates=True)
        if self.muse_checkbox.get():
            self.plot_MUSE_spec()
        try:
            tab_row = self._root().cat[self._root().cat["v3_id"] == self.gal_id]
            self.fig_axes.set_title(
                f"IDs: v3={tab_row['v3_id'].value}, Xin={tab_row['Xin_id'].value}, NIRCAM={tab_row['NIRCAM_id'].value}"
            )
        except Exception as e:
            print(e)
            pass
        self.seg_frame.update_seg_map()

    def plot_grizli(self, templates=False):
        file_path = [
            *(
                Path(self._root().full_config["files"]["extractions_dir"])
                .expanduser()
                .resolve()
            ).glob(f"*{self.gal_id:0>5}.1D.fits")
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
                    y_vals = (
                        data_table["flux"][clip]
                        / data_table["flat"][clip]
                        / data_table["pscale"][clip]
                        / 1e-19
                    )
                    self.plotted_components[dict_key][
                        hdu.name
                    ] = self.fig_axes.errorbar(
                        data_table["wave"][clip],
                        y_vals,
                        yerr=data_table["err"][clip]
                        / data_table["flat"][clip]
                        / data_table["pscale"][clip]
                        / 1e-19,
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
            tab_row = self._root().cat[self._root().cat["v3_id"] == self.gal_id]

            cube_wcs = WCS(cube_hdul[1].header)

            wavelengths = (
                (np.arange(cube_hdul[1].header["NAXIS3"]) + 1.0)
                - cube_hdul[1].header["CRPIX3"]
            ) * cube_hdul[1].header["CD3_3"] + cube_hdul[1].header["CRVAL3"]
            MUSE_spec = self.cube_extract_spectra(
                cube_hdul[1].data,
                cube_wcs,
                tab_row["v3_ra"],
                tab_row["v3_dec"],
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
        temp_dir = (
            Path(self._root().full_config["files"]["temp_dir"]).expanduser().resolve()
        )
        try:
            with pf.open(
                temp_dir
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
            print(spectrum)

            new_hdul = pf.HDUList()
            new_hdul.append(
                pf.ImageHDU(data=spectrum, header=cube_wcs.spectral.to_header())
            )
            new_hdul.writeto(
                temp_dir
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
        for line_key, line_data in self._root().full_config["lines"][line_type].items():
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
        for line_type in ["emission", "absorption"]:
            try:
                for line_key, line_data in (
                    self._root().full_config["lines"][line_type].items()
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

    def hover(self, event):
        if event.inaxes == self.fig_axes:
            for line_type in ["emission", "absorption"]:
                if len(self.plotted_components[line_type]) > 0:
                    for line_key, line_data in (
                        self._root().full_config["lines"][line_type].items()
                    ):
                        if self.plotted_components[line_type][line_key].contains(event)[
                            0
                        ]:
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

class SegMapFrame(ctk.CTkFrame):
    def __init__(self, master, gal_id, **kwargs):
        super().__init__(master, **kwargs)

        self.gal_id = gal_id

        self.rowconfigure(0,weight=1)
        self.columnconfigure(0,weight=1)

        self.update_seg_path()

        self.fig = Figure(
            constrained_layout=True,
            figsize=(1,1),
        )
        self.pyplot_canvas = FigureCanvasTkAgg(
            figure=self.fig,
            master=self,
        )

        self.fig_axes = self.fig.add_subplot(111)

        prop_cycle = plt.rcParams['axes.prop_cycle']
        self.default_cmap = colors.LinearSegmentedColormap.from_list("default", prop_cycle.by_key()['color'][:7])
        # print (plt.rcParams['axes.prop_cycle'])

        # self.fig.canvas.mpl_connect("motion_notify_event", self.hover)

        # toolbar = NavigationToolbar2Tk(self.fig.canvas, self, pack_toolbar=False)
        # toolbar.update()

        # self.fig_axes.set_xlabel(r"Wavelength (${\rm \AA}$)")
        # self.fig_axes.set_ylabel("Flux")

        # self.custom_annotation = self.fig_axes.annotate(
        #     "", xy=(0, 0), xytext=(0, 0), textcoords="offset points"
        # )
        # self.custom_annotation.set_visible(False)

        # self._update_all()

        # self.add_lines()

        # f = zoom_factory(self.fig_axes)

        self.fig.canvas.draw_idle()

        self.fig.canvas.get_tk_widget().grid(row=0, column=0, sticky="news")  

        if self._root().main_tabs.get()=="Spec view":
            self.plot_seg_map()

    def update_seg_path(self, pattern="*seg.fits"):

        self.seg_path = [
            *(
                Path(self._root().full_config["files"]["prep_dir"])
                .expanduser()
                .resolve()
            ).glob(pattern)
        ]
        if len(self.seg_path)==0:
            print ("Segmentation map not found.")
            self.seg_path = None
        else:
            self.seg_path = self.seg_path[0]
            # toolbar.grid(row=1, column=0, sticky="news")

    def plot_seg_map(self, border=5):
        if self.seg_path is None:
            print ("Currently nothing to do here.")
        else:
            with pf.open(self.seg_path) as hdul:
                seg_wcs = WCS(hdul[0].header)
                seg_data = hdul[0].data
                print (seg_wcs)
                tab_row = self._root().cat[self._root().cat["v3_id"] == self.gal_id][0]
                radius = extract_pixel_radius(tab_row,  seg_wcs, "v3_flux_radius").value
                radius = 1.1*extract_pixel_radius(tab_row,  seg_wcs, "v3_kron_rcirc").value
                y_c, x_c = extract_pixel_ra_dec(tab_row, seg_wcs).value
                print (x_c, y_c)
                
                print (np.where(seg_data==self.gal_id)[0])
                location = np.where(seg_data==self.gal_id)
                print (np.nanmin(np.where(seg_data==self.gal_id)[0]), )
                print (np.nanmin(location[0]))

                cutout = hdul[0].data[
                    int(np.clip(x_c-radius, 0, hdul[0].data.shape[0])):int(np.clip(x_c+radius, 0, hdul[0].data.shape[0])),
                    int(np.clip(y_c-radius, 0, hdul[0].data.shape[1])):int(np.clip(y_c+radius,0, hdul[0].data.shape[1]))
                ]
                print (cutout)
                cutout = seg_data[
                    np.nanmin(location[0])-border:np.nanmax(location[0])+border,
                    np.nanmin(location[1])-border:np.nanmax(location[1])+border,
                ].astype(float)
                cutout[cutout==0] = np.nan
                self.fig_axes.imshow(cutout%7, origin="lower", cmap=self.default_cmap, aspect="equal")
                self.pyplot_canvas.draw_idle()
                self.update()

        self.fig_axes.set_facecolor("0.7")
        self.fig_axes.set_xticklabels("")
        self.fig_axes.set_yticklabels("")

    def update_seg_map(self, force=False):
        if self.gal_id != int(self._root().current_gal_id.get()) or force:
            self.gal_id = int(self._root().current_gal_id.get())
            self.plot_seg_map()



def extract_pixel_radius(q_table,celestial_wcs, key="flux_radius" ):
    # The assumption is that SExtractor radii are typically measured in pixel units
    radius = q_table[key]
    if hasattr(radius, "unit") and radius.unit!=None:
        radius = radius.value*radius.unit # Avoiding problems with columns
        if radius.unit == u.pix:
            pass
        elif u.get_physical_type(radius) == "dimensionless":
            radius*=u.pix
        elif u.get_physical_type(radius) == "angle":
            pixel_scale = np.sqrt(celestial_wcs.proj_plane_pixel_area()).to(u.arcsec)/u.pix
            radius /= pixel_scale
        else:
            raise ValueError("The units of this radius cannot be automatically converted.")
    else:
        print ("Radius has no unit, assuming pixels.")
        if hasattr(radius, "value"):
            radius = radius.value*u.pix
        else:
            radius = radius*u.pix

    return radius

def extract_pixel_ra_dec(q_table, celestial_wcs, key_ra="ra", key_dec="dec"):

    try:
        orig_ra = q_table[key_ra]
        orig_dec = q_table[key_dec]
    except:
        print ("No match found for supplied ra, dec keys. Performing automatic search instead.")
        lower_colnames = np.array([x.lower() for x in q_table.colnames])
        for r, d in [[key_ra, key_dec], ["ra", "dec"]]:
            possible_names = []
            for n in lower_colnames:
                if d.lower() in n:
                    possible_names.append(n)
            possible_names = sorted(possible_names, key=lambda x: (len(x), x))
            # print (possible_names)
            # print (possible_names.sort())
            for n in possible_names:
                r_poss = n.replace(d.lower(), r.lower())
                if r_poss in lower_colnames:
                    # idx = (lower_colnames == d_poss).nonzero()[0]
                    # print (idx.dtype)
                    # # print (q_table.colnames[idx])
                    orig_ra = q_table[q_table.colnames[int((lower_colnames == r_poss).nonzero()[0])]]
                    orig_dec = q_table[q_table.colnames[int((lower_colnames == n).nonzero()[0])]]
                    break
            else:
                continue
            break
    
    # new_ra, new_dec = 0,0

    def check_deg(orig):
        if hasattr(orig, "unit") and orig.unit!=None:
            new = orig.value*orig.unit # Avoiding problems with columns
            if new.unit == u.pix:
                return new
            elif u.get_physical_type(new) == "dimensionless":
                new*=u.deg
            if u.get_physical_type(new) == "angle":
                new = new.to(u.deg)
        else:
            print ("Coordinate has no unit, assuming degrees.")
            if hasattr(orig, "value"):
                new = orig.value*u.deg
            else:
                new = orig*u.deg
        return new

    new_ra, new_dec = check_deg(orig_ra), check_deg(orig_dec)
    if new_ra.unit == u.pix:
        return new_ra, new_dec
        
    sc = SkyCoord(new_ra, new_dec)
    pix_c = np.hstack(sc.to_pixel(celestial_wcs)[:])*u.pix
    return pix_c



    # return new_ra, new_dec