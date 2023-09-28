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
            padx=(20,10),
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
            padx=(20,10),
            pady=10,
            sticky="we",
        )

    def change_lines(self):
        if self.emission_checkbox.get() and len(self.plotted_lines["emission"]) == 0:
            self.add_lines(line_type="emission")
            self.update_lines()
        elif (
            not self.emission_checkbox.get() and len(self.plotted_lines["emission"]) > 0
        ):
            for line in self.fig_axes.get_lines():
                if line in self.plotted_lines["emission"].values():
                    line.remove()
            for line_key, line_data in (
                self._root().full_config["lines"]["emission"].items()
            ):
                del self.plotted_lines["emission"][line_key]

        if (
            self.absorption_checkbox.get()
            and len(self.plotted_lines["absorption"]) == 0
        ):
            self.add_lines(line_type="absorption")
            self.update_lines()
        elif (
            not self.absorption_checkbox.get()
            and len(self.plotted_lines["absorption"]) > 0
        ):
            for line in self.fig_axes.get_lines():
                if line in self.plotted_lines["absorption"].values():
                    line.remove()
            for line_key, line_data in (
                self._root().full_config["lines"]["absorption"].items()
            ):
                del self.plotted_lines["absorption"][line_key]

        self.pyplot_canvas.draw()
        self.update()

    def update_plot(self):
        if not hasattr(self, "pyplot_canvas"):
            self.fig = Figure(constrained_layout=True)
            self.pyplot_canvas = FigureCanvasTkAgg(
                figure=self.fig,
                master=self,
            )

            if not hasattr(self, "plotted_lines"):
                self.plotted_lines = dict(emission={}, absorption={})

            self.fig_axes = self.fig.add_subplot(111)

            self.fig.canvas.mpl_connect("motion_notify_event", self.hover)

            self.fig_axes.set_xlabel(r"Wavelength (\AA)")
            self.fig_axes.set_ylabel("Flux")

            self.custom_annotation = self.fig_axes.annotate(
                "", xy=(0, 0), xytext=(0, 0), textcoords="offset points"
            )
            self.custom_annotation.set_visible(False)

            self.plot_grizli(
                gal_id=int(self._root().current_gal_id.get()),
            )
            self.plot_MUSE_spec(
                gal_id=int(self._root().current_gal_id.get()),
            )
            self.add_lines()

            self.gal_id = int(self._root().current_gal_id.get())
            self.pyplot_canvas.draw_idle()

            self.pyplot_canvas.get_tk_widget().grid(row=0, column=0, sticky="news")

        if self.gal_id != self._root().current_gal_id.get() or not hasattr(
            self, "pyplot_canvas"
        ):
            self.gal_id = int(self._root().current_gal_id.get())
            self.plot_MUSE_spec(
                gal_id=int(self._root().current_gal_id.get()),
            )
            self.plot_grizli(
                gal_id=int(self._root().current_gal_id.get()),
            )
            self.pyplot_canvas.draw_idle()

            self.update()

    def plot_grizli(
        self,
        gal_id,
    ):
        file_path = [*(
            Path(self._root().full_config["files"]["extractions_dir"]).expanduser().resolve()
        ).glob(f"*{gal_id:0>5}.1D.fits")][0]

        self.clip = 0.05

        ymax = 0
        colours = {
            "F115W": "C0",
            "F150W": "C1",
            "F200W": "C2",
        }

        if not hasattr(self, "plotted_grisms"):
            self.plotted_grisms = dict()
        else:
            for v in self.plotted_grisms.values():
                v.remove()
        with pf.open(file_path) as hdul:
            for hdu in hdul[1:]:
                # print (hdu)
                data_table = Table(hdu.data)
                # print (self.clip*len(data_table["wave"]))
                # print (np.percentile(data_table["flux"]/data_table["flat"]/1e-19,[1,99]))
                # print (hdu.name)
                y_vals = data_table["flux"]/data_table["flat"]/1e-19
                self.plotted_grisms[hdu.name] = self.fig_axes.errorbar(
                    data_table["wave"],
                    y_vals,
                    yerr=data_table["err"]/data_table["flat"]/1e-19,
                    fmt="o",
                    markersize=3,
                    ecolor=colors.to_rgba(colours[hdu.name], 0.5),
                    c=colours[hdu.name]
                )
                # print (self.plotted_grisms[hdu.name])
                # print (self.fig_axes.get_children())
                ymax = np.nanmax([ymax, np.nanmax(y_vals)])

        self.fig_axes.set_ylim(ymin=-0.05*ymax, ymax=1.05*ymax)

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
        if hasattr(self, "plotted_cube"):
            for line in self.fig_axes.get_lines():
                if line == self.plotted_cube:
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
                tab_row["RA"],
                tab_row["DEC"],
                radius=tab_row["r50_SE"][0],
            )
            # if not hasattr(self, "plotted_lines"):
            #     self.plotted_lines = dict(emission={}, absorption={})

            # self.fig.clear()
            # ax = self.fig.add_subplot(111)

            # self.fig.canvas.mpl_connect("motion_notify_event", self.hover)

            self.plotted_cube, = self.fig_axes.plot(
                wavelengths,
                MUSE_spec / np.nanmedian(MUSE_spec)*np.nanmedian(self.fig_axes.get_ylim()),
                linewidth=0.5,
                c="k",
            )
            print (tab_row["flux_auto"])
            # ax.set_xlabel("Wavelength (nm)")
            # ax.set_ylabel("Flux")
            self.fig_axes.set_title(
                f"IDs: v3={tab_row['v3_id'][0]}, Xin={tab_row['Xin_id'][0]}, NIRCAM={tab_row['NIRCAM_id'][0]}"
            )

            # self.add_lines()
            # self.custom_annotation = ax.annotate(
            #     "", xy=(0, 0), xytext=(0, 0), textcoords="offset points"
            # )
            # self.custom_annotation.set_visible(False)
            # self.gal_id = gal_id

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
            with pf.open(temp_dir / f"{ra[0]:.6f}_{dec[0]:.6f}_r{radius:.6f}.fits") as hdul:
                return hdul[0].data
        except Exception as e:
            print (e)
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
                print ("failed")
                radius *= u.arcsec
            print (radius)
            print (radius.unit)

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
                spectrum[i] = aperture_photometry(cube_slice, aperture, error=cube_error)[
                    "aperture_sum"
                ]

            new_hdul = pf.HDUList()
            new_hdul.append(
                pf.ImageHDU(
                    data=spectrum,
                    header=cube_wcs.spectral.to_header()
                )
            )
            new_hdul.writeto(temp_dir / f"{ra[0]:.6f}_{dec[0]:.6f}_r{radius.value:.6f}.fits")

            return spectrum

    def add_lines(
        self,
        line_type=None,
    ):
        if line_type is None:
            return
        xlims = self.fig_axes.get_xlim()
        for line_key, line_data in self._root().full_config["lines"][line_type].items():
            self.plotted_lines[line_type][line_key] = self.fig.get_axes()[0].axvline(
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
                    current_line = self.plotted_lines[line_type][line_key]
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
                if len(self.plotted_lines[line_type]) > 0:
                    for line_key, line_data in (
                        self._root().full_config["lines"][line_type].items()
                    ):
                        if self.plotted_lines[line_type][line_key].contains(event)[0]:
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