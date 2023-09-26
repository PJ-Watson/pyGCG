import customtkinter as ctk
from matplotlib.figure import Figure
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


class SpecFrame(ctk.CTkFrame):
    def __init__(self, master, gal_id, **kwargs):
        super().__init__(master, **kwargs)

        self.gal_id = gal_id

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.grid(row=0, column=1, sticky="news")

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
            padx=20,
            pady=(10, 0),
            sticky="we",
        )
        self.redshift_entry.bind(
            "<Return>",
            self.redshift_entry_callback,
        )
        self.redshift_slider = ctk.CTkSlider(
            self.scrollable_frame,
            variable=self.current_redshift,
            from_=0,
            to=2,
            orientation="horizontal",
            command=lambda slider_value: self.update_lines(slider_value),
        )
        self.redshift_slider.grid(
            row=5,
            padx=20,
            pady=20,
        )

    def redshift_entry_callback(self, event):
        self.update_lines(self.current_redshift.get())

    def change_lines(self):
        if self.emission_checkbox.get() and len(self.plotted_lines["emission"]) == 0:
            self.add_lines(line_type="emission")
            self.update_lines(self.current_redshift.get())
        elif (
            not self.emission_checkbox.get() and len(self.plotted_lines["emission"]) > 0
        ):
            for line in self.fig.get_axes()[0].get_lines():
                if line in self.plotted_lines["emission"].values():
                    line.remove()
            for line_key, line_data in (
                self._root().full_config["lines"]["emission"].items()
            ):
                # print
                del self.plotted_lines["emission"][line_key]

        if (
            self.absorption_checkbox.get()
            and len(self.plotted_lines["absorption"]) == 0
        ):
            self.add_lines(line_type="absorption")
            self.update_lines(self.current_redshift.get())
        elif (
            not self.absorption_checkbox.get()
            and len(self.plotted_lines["absorption"]) > 0
        ):
            for line in self.fig.get_axes()[0].get_lines():
                if line in self.plotted_lines["absorption"].values():
                    line.remove()
            for line_key, line_data in (
                self._root().full_config["lines"]["absorption"].items()
            ):
                # print
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
            self.plot_MUSE_spec(
                gal_id=self._root().current_gal_id,
            )

            self.pyplot_canvas.get_tk_widget().grid(row=0, column=0, sticky="news")

        if self.gal_id != self._root().current_gal_id or not hasattr(
            self, "pyplot_canvas"
        ):
            self.plot_MUSE_spec(
                gal_id=self._root().current_gal_id,
            )

            self.update()

    def plot_MUSE_spec(
        self,
        gal_id,
    ):
        cube_path = (
            Path(self._root().full_config["files"]["cube_path"]).expanduser().resolve()
        )
        if not cube_path.is_file():
            print(cube_path)
            print("no file")
            return

        with pf.open(cube_path) as cube_hdul:
            tab_row = self._root().cat[self._root().cat["v3_id"] == gal_id]

            cube_wcs = WCS(cube_hdul[1].header)

            wavelengths = (
                (np.arange(cube_hdul[1].header["NAXIS3"]) + 1.0)
                - cube_hdul[1].header["CRPIX3"]
            ) * cube_hdul[1].header["CD3_3"] + cube_hdul[1].header["CRVAL3"]
            MUSE_spec = self.cube_extract_spectra(
                cube_hdul[1].data,
                cube_wcs,
                tab_row["RA"],
                tab_row["DEC"],
            )
            if not hasattr(self, "plotted_lines"):
                self.plotted_lines = dict(emission={}, absorption={})

            self.fig.clear()
            ax = self.fig.add_subplot(111)

            self.fig.canvas.mpl_connect("motion_notify_event", self.hover)

            ax.plot(
                wavelengths,
                MUSE_spec / tab_row["flux_auto"],
                linewidth=0.5,
                c="k",
            )
            ax.set_xlabel("Wavelength (nm)")
            ax.set_ylabel("Flux")
            ax.set_title(
                f"IDs: v3={tab_row['v3_id'][0]}, Xin={tab_row['Xin_id'][0]}, NIRCAM={tab_row['NIRCAM_id'][0]}"
            )

            self.add_lines()
            self.custom_annotation = ax.annotate(
                "", xy=(0, 0), xytext=(0, 0), textcoords="offset points"
            )
            self.custom_annotation.set_visible(False)

            self.pyplot_canvas.draw()
            self.gal_id = gal_id

    @staticmethod
    def cube_extract_spectra(
        data_cube,
        cube_wcs,
        ra,
        dec,
        radius=0.5,
        cube_error=None,
    ):
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
        except:
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
            spectrum[i] = aperture_photometry(cube_slice, aperture, error=cube_error)[
                "aperture_sum"
            ]

        return spectrum

    def add_lines(
        self,
        line_type=None,
    ):
        if line_type is None:
            return
        xlims = self.fig.get_axes()[0].get_xlim()
        for line_key, line_data in self._root().full_config["lines"][line_type].items():
            self.plotted_lines[line_type][line_key] = self.fig.get_axes()[0].axvline(
                line_data["centre"] * self.current_redshift.get(),
                c="0.7",
                alpha=0.7,
                linewidth=2,
            )

        self.fig.get_axes()[0].set_xlim(xlims)
        self.pyplot_canvas.draw()

    def update_lines(
        self,
        new_redshift,
    ):
        for line_type in ["emission", "absorption"]:
            try:
                for line_key, line_data in (
                    self._root().full_config["lines"][line_type].items()
                ):
                    current_line = self.plotted_lines[line_type][line_key]
                    current_line.set_data(
                        [
                            line_data["centre"] * (1 + new_redshift),
                            line_data["centre"] * (1 + new_redshift),
                        ],
                        [0, 1],
                    )
            except:
                pass

        self.fig.canvas.draw()

    def hover(self, event):
        if event.inaxes == self.fig.get_axes()[0]:
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
