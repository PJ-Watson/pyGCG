import tkinter as tk

import customtkinter as ctk
import numpy as np
from matplotlib import cbook
from matplotlib.backend_bases import NavigationToolbar2
from matplotlib.backends._backend_tk import ToolTip
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from PIL import Image

from .icon_checkbox import IconCheckBox


class VerticalNavigationToolbar2Tk(NavigationToolbar2Tk):
    def __init__(self, canvas, window, pack_toolbar=False, **kwargs):
        NavigationToolbar2Tk._set_image_for_button = self._set_image_for_button

        super().__init__(canvas, window, pack_toolbar=False, **kwargs)

    # # Override the damn image selection
    @staticmethod
    def _set_image_for_button(self, button):
        """
        Set the image for a button based on its pixel size.

        The pixel size is determined by the DPI scaling of the window.
        """

        if button._image_file is None:
            return

        # Allow _image_file to be relative to Matplotlib's "images" data
        # directory.
        path_regular = cbook._get_data_path("images", button._image_file)
        path_large = path_regular.with_name(
            path_regular.name.replace(".png", "_large.png")
        )
        size = button.winfo_pixels("18p")

        # Nested functions because ToolbarTk calls  _Button.
        def _get_color(color_name):
            # `winfo_rgb` returns an (r, g, b) tuple in the range 0-65535
            return button.winfo_rgb(button.cget(color_name))

        def _is_dark(color):
            if isinstance(color, str):
                color = _get_color(color)
            return max(color) < 65535 / 2

        def _recolor_icon(image, color):
            image_data = np.asarray(image).copy()
            black_mask = (image_data[..., :3] == 0).all(axis=-1)
            image_data[black_mask, :3] = color
            return Image.fromarray(image_data, mode="RGBA")

        # Use the high-resolution (48x48 px) icon if it exists and is needed
        with Image.open(
            path_large if (size > 24 and path_large.exists()) else path_regular
        ) as im:
            # assure a RGBA image as foreground color is RGB
            im = im.convert("RGBA")
            image = ctk.CTkImage(im.resize((size, size)))
            button._ntimage = image

            # create a version of the icon with the button's text color
            foreground = 255 * np.array(self._root().text_colour)
            im_alt = _recolor_icon(im, foreground)
            image_alt = ctk.CTkImage(im_alt.resize((size, size)))
            button._ntimage_alt = image_alt

        if ctk.get_appearance_mode() == "Dark":
            image_kwargs = {"image": image_alt}
        else:
            image_kwargs = {"image": image}

        # Checkbuttons may switch the background to `selectcolor` in the
        # checked state, so check separately which image it needs to use in
        # that state to still ensure enough contrast with the background.
        if isinstance(button, tk.Checkbutton) and button.cget("selectcolor") != "":
            if self._windowingsystem != "x11":
                selectcolor = "selectcolor"
            else:
                # On X11, selectcolor isn't used directly for indicator-less
                # buttons. See `::tk::CheckEnter` in the Tk button.tcl source
                # code for details.
                r1, g1, b1 = _get_color("selectcolor")
                r2, g2, b2 = _get_color("activebackground")
                selectcolor = ((r1 + r2) / 2, (g1 + g2) / 2, (b1 + b2) / 2)
            if _is_dark(selectcolor):
                image_kwargs["selectimage"] = image_alt
            else:
                image_kwargs["selectimage"] = image

        try:
            button.configure(**image_kwargs, height="18p", width="18p")
        except:
            button.configure(
                unchecked_icon=image_kwargs["image"],
                checked_icon=image_kwargs["image"],
                height="18p",
                width="18p",
            )
            button._update_image()
            button._draw()
            pass

    # override _Button() to re-pack the toolbar button in vertical direction
    def _Button(self, text, image_file, toggle, command):
        if not toggle:
            b = ctk.CTkButton(
                master=self,
                text=None,
                command=command,
                bg_color=self._root().bg_colour_name,
                fg_color=self._root().bg_colour_name,
            )
        else:
            # There is a bug in tkinter included in some python 3.6 versions
            # that without this variable, produces a "visual" toggling of
            # other near checkbuttons
            # https://bugs.python.org/issue29402
            # https://bugs.python.org/issue25684
            var = ctk.IntVar(master=self)
            b = IconCheckBox(
                master=self,
                text="",
                command=command,
                unchecked_icon=image_file,
                checked_icon=image_file,
                fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"],
                variable=var,
                bg_color=self._root().bg_colour_name,
                auto_dark_icon=True,
            )
            b.var = var
        b._image_file = image_file
        if image_file is not None:
            # Explicit class because ToolbarTk calls _Button.
            NavigationToolbar2Tk._set_image_for_button(self, b)
        else:
            b.configure(font=self._label_font)
        b.pack(side="top", pady=5)  # re-pack button in vertical direction
        return b

    # override _Spacer() to create vertical separator
    def _Spacer(self):
        s = tk.Frame(self, width=26, relief="ridge", bg="DarkGray", padx=2)
        s.pack(side="top", pady=5)  # pack in vertical direction
        return s

    # disable showing mouse position in toolbar
    def set_message(self, s):
        pass
