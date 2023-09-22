import numpy as np
import astropy.io.fits as pf
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.table import Table
from pathlib import Path
from photutils.aperture import (
    aperture_photometry,
    SkyCircularAperture,
    CircularAperture,
)
import matplotlib.pyplot as plt
from tqdm import tqdm
import json
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def cube_extract_spectra(
    # temp_dir_path,
    data_cube,
    cube_wcs,
    ra,
    dec,
    radius=1,
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
    pix_r = radius / np.sqrt(cube_wcs.celestial.proj_plane_pixel_area()).to(radius.unit)

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


def plot_MUSE_spec(
    master,
    gal_id=1864,
    cat_path="../catalogues/combined_v3_NIRCAM_Xin.fits",
):
    NIRCAM_fits_tab = Table.read(cat_path)

    # print (dir(master._root()))
    cube_path = (
        Path(master._root().full_config["files"]["cube_path"]).expanduser().resolve()
    )
    if not cube_path.is_file():
        return

    with pf.open(cube_path) as cube_hdul:
        tab_row = NIRCAM_fits_tab[NIRCAM_fits_tab["v3_id"] == gal_id]
        # print (tab_row["v3_id"])
        # print (tab_row["ra"],tab_row["dec"])

        cube_wcs = WCS(cube_hdul[1].header)

        # print(cube_hdul[1].header["CUNIT3"])
        wavelengths = (
            (np.arange(cube_hdul[1].header["NAXIS3"]) + 1.0)
            - cube_hdul[1].header["CRPIX3"]
        ) * cube_hdul[1].header["CD3_3"] + cube_hdul[1].header["CRVAL3"]
        MUSE_spec = cube_extract_spectra(
            cube_hdul[1].data,
            cube_wcs,
            tab_row["RA"],
            tab_row["DEC"],
        )

        # fig, ax = plt.subplots(figsize=(8, 6))
        # figure.axes.clear()
        master.fig.clear()
        ax = master.fig.add_subplot(111)

        ax.plot(
            wavelengths,
            MUSE_spec / tab_row["flux_auto"],
            linewidth=0.5,
        )
        ax.set_xlabel("Wavelength (nm)")
        ax.set_ylabel("Flux")
        ax.set_title(
            f"IDs: v3={tab_row['v3_id'][0]}, Xin={tab_row['Xin_id'][0]}, NIRCAM={tab_row['NIRCAM_id'][0]}"
        )
        master.pyplot_canvas.draw_idle()
        # pyplot_canvas = FigureCanvasTkAgg(fig,master=master)
        # pyplot_canvas.draw()
        # master.pyplot_canvas.get_tk_widget().grid(row=0, column=0, sticky="news")
        #  master.pyplot_canvas.get_tk_widget()
        # print (dir(master))
        # print (master._check_color_type())

        # master.pyplot_canvas.show()
        # parent_canvas.get_tk_widget().pack(side="top",fill='both',expand=True)
        # # master.pyplot_canvas.pack(side="top",fill='both',expand=True)
        # master.pyplot_canvas = True
        master.gal_id = gal_id
        # print(figure.get_dpi())
        # print(master.winfo_reqheight())
        # print(master.winfo_reqheight() / figure.get_dpi())
