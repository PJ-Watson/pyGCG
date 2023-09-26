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


def add_lines(
    master,
    line_type="absorption",
):
    xlims = master.fig.get_axes()[0].get_xlim()
    # print (dir(master.fig))
    # print (master.fig.axes)
    # print (master.fig.get_axes())

    # print (master._root().full_config["lines"]["emission"])

    for line_type, colour in zip(["emission", "absorption"], ["r", "b"]):
        for line_key, line_data in (
            master._root().full_config["lines"][line_type].items()
        ):
            master.plotted_lines[line_type][line_key] = master.fig.get_axes()[
                0
            ].axvline(
                line_data["centre"],
                c=colour,
            )

    master.fig.get_axes()[0].set_xlim(xlims)


def update_lines(
    master,
    new_redshift,
):
    # print ("yarp")
    # print (new_redshift)
    # print (master)
    for line_type in ["emission", "absorption"]:
        try:
            for line_key, line_data in (
                master._root().full_config["lines"][line_type].items()
            ):
                current_line = master.plotted_lines[line_type][line_key]
                # print (dir(current_line))
                # print (current_line.get_ydata())
                current_line.set_data(
                    [
                        line_data["centre"] * (1 + new_redshift),
                        line_data["centre"] * (1 + new_redshift),
                    ],
                    [0, 1],
                )
        except:
            pass
    # master.update()
    master.pyplot_canvas.draw_idle()


def plot_MUSE_spec(
    master,
    gal_id=1864,
):
    cube_path = (
        Path(master._root().full_config["files"]["cube_path"]).expanduser().resolve()
    )
    if not cube_path.is_file():
        return

    with pf.open(cube_path) as cube_hdul:
        tab_row = master._root().cat[master._root().cat["v3_id"] == gal_id]

        cube_wcs = WCS(cube_hdul[1].header)

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
        if not hasattr(master, "plotted_lines"):
            master.plotted_lines = dict(emission={}, absorption={})
        # print (master.plotted_lines)

        master.fig.clear()
        ax = master.fig.add_subplot(111)

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

        add_lines(master)

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


# import tkinter as tk     # python 3
# # import Tkinter as tk   # python 2
# import numpy as np
# from matplotlib.backends.backend_tkagg import (
#     FigureCanvasTkAgg, NavigationToolbar2Tk)
# # Implement the default Matplotlib key bindings.
# from matplotlib.backend_bases import key_press_handler
# from matplotlib.figure import Figure


# class Example(tk.Frame):
#     """Illustrate how to drag items on a Tkinter canvas"""

#     def __init__(self, parent):
#         tk.Frame.__init__(self, parent)


#         fig = Figure(figsize=(5, 4), dpi=100)
#         t = np.arange(0, 3, .01)
#         fig.add_subplot(111).plot(t, 2 * np.sin(2 * np.pi * t))

#         #create a canvas
#         self.canvas = tk.Canvas(width=200, height=300)
#         self.canvas.pack(fill="both", expand=True)

#         canvas = FigureCanvasTkAgg(fig, master=root)  # A tk.DrawingArea.
#         canvas.draw()
#         canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

#         # this data is used to keep track of an
#         # item being dragged
#         self._drag_data = {"x": 0, "y": 0, "item": None}

#         # create a movable object
#         self.create_token(100, 150, "black")

#         # add bindings for clicking, dragging and releasing over
#         # any object with the "token" tag
#         self.canvas.tag_bind("token", "<ButtonPress-1>", self.drag_start)
#         self.canvas.tag_bind("token", "<ButtonRelease-1>", self.drag_stop)
#         self.canvas.tag_bind("token", "<B1-Motion>", self.drag)

#     def create_token(self, x, y, color):
#         """Create a token at the given coordinate in the given color"""
#         self.canvas.create_rectangle(
#             x - 5,
#             y - 100,
#             x + 5,
#             y + 100,
#             outline=color,
#             fill=color,
#             tags=("token",),
#         )

#     def drag_start(self, event):
#         """Begining drag of an object"""
#         # record the item and its location
#         self._drag_data["item"] = self.canvas.find_closest(event.x, event.y)[0]
#         self._drag_data["x"] = event.x
#         self._drag_data["y"] = event.y

#     def drag_stop(self, event):
#         """End drag of an object"""
#         # reset the drag information
#         self._drag_data["item"] = None
#         self._drag_data["x"] = 0
#         self._drag_data["y"] = 0

#     def drag(self, event):
#         """Handle dragging of an object"""
#         # compute how much the mouse has moved
#         delta_x = event.x - self._drag_data["x"]
#         delta_y = 0
#         # move the object the appropriate amount
#         self.canvas.move(self._drag_data["item"], delta_x, delta_y)
#         # record the new position
#         self._drag_data["x"] = event.x
#         self._drag_data["y"] = event.y

# if __name__ == "__main__":
#     root = tk.Tk()
#     Example(root).pack(fill="both", expand=True)
#     root.mainloop()

# import tkinter

# import numpy as np

# # Implement the default Matplotlib key bindings.
# from matplotlib.backend_bases import key_press_handler
# from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
#                                                NavigationToolbar2Tk)
# from matplotlib.figure import Figure

# root = tkinter.Tk()
# root.wm_title("Embedding in Tk")

# fig = Figure(figsize=(5, 4), dpi=100)
# t = np.arange(0, 3, .01)
# ax = fig.add_subplot()
# line, = ax.plot(t, 2 * np.sin(2 * np.pi * t))
# ax.set_xlabel("time [s]")
# ax.set_ylabel("f(t)")

# canvas = FigureCanvasTkAgg(fig, master=root)  # A tk.DrawingArea.
# canvas.draw()

# # pack_toolbar=False will make it easier to use a layout manager later on.
# toolbar = NavigationToolbar2Tk(canvas, root, pack_toolbar=False)
# toolbar.update()

# canvas.mpl_connect(
#     "key_press_event", lambda event: print(f"you pressed {event.key}"))
# canvas.mpl_connect("key_press_event", key_press_handler)

# button_quit = tkinter.Button(master=root, text="Quit", command=root.destroy)


# def update_frequency(new_val):
#     # retrieve frequency
#     f = float(new_val)

#     # update data
#     y = 2 * np.sin(2 * np.pi * f * t)
#     line.set_data(t, y)

#     # required to update canvas and attached toolbar!
#     canvas.draw()


# slider_update = tkinter.Scale(root, from_=1, to=5, orient=tkinter.HORIZONTAL,
#                               command=update_frequency, label="Frequency [Hz]")

# # Packing order is important. Widgets are processed sequentially and if there
# # is no space left, because the window is too small, they are not displayed.
# # The canvas is rather flexible in its size, so we pack it last which makes
# # sure the UI controls are displayed as long as possible.
# button_quit.pack(side=tkinter.BOTTOM)
# slider_update.pack(side=tkinter.BOTTOM)
# toolbar.pack(side=tkinter.BOTTOM, fill=tkinter.X)
# canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True)

# tkinter.mainloop()
