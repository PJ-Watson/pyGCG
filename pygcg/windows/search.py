import re

import astropy.units as u
import customtkinter as ctk
import numpy as np
from astropy.coordinates import SkyCoord
from CTkMessagebox import CTkMessagebox

from .base_window import BaseWindow


class SearchWindow(BaseWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            title="Find Multiple Objects",
            top_text="Insert each object on a new line:",
            **kwargs,
        )
        self.action_button.configure(text="Search")

    # def create_text_box(self):
    #     super().create_text_box()
    # if "comments" in self._root().current_gal_data.keys():
    #     self.text_box.insert("1.0", self._root().current_gal_data["comments"])

    def warn_input(self, exception=None):
        error = CTkMessagebox(
            title="Error",
            message=f"Could not parse input as on-sky coordinates: {exception}",
            icon="cancel",
            option_focus=1,
        )
        if error.get() == "OK":
            self.focus_force()
            return

    def action_button_callback(self, event=None):
        text_input = self.text_box.get("1.0", "end")

        lines = re.split("\n", text_input.strip())

        try:
            parts = re.split("\s*[,|;|\s]\s*", lines[0].strip())
        except Exception as e:
            self.warn_input(e)

        ids = np.empty(len(lines))
        ras = np.empty_like(ids)
        decs = np.empty_like(ids)

        try:
            if len(parts) == 3:
                for i, l in enumerate(lines):
                    ids[i], ras[i], decs[i] = re.split("\s*[,|;|\s]\s*", l.strip())

            elif len(parts) == 2:
                for i, l in enumerate(lines):
                    # pre.split("\s*[,|;|\s]\s*", l.strip()))
                    ras[i], decs[i] = re.split("\s*[,|;|\s]\s*", l.strip())
            else:
                raise ValueError()
        except:
            self.warn_input("input must be either two or three components per line.")

        new_coords = SkyCoord(ras * u.deg, decs * u.deg)

        sky_match_idx, dist, _ = new_coords.match_to_catalog_sky(
            self._root().sky_coords
        )

        print(sky_match_idx)
        print(dist)


text_input = """
 9, 3.584189547667199 -30.41797175811047
 10 3.584116180775893, -30.41793447778107
 11 3.583798774418007 -30.41785997245157
 3699 ; 3.585369179342615, -30.39425480988234
 3700, 3.586265729668156     -30.40015898193154
 3701, 3.586558502419486, -30.39936292951525
 3702, 3.588664510925963, -30.39604966269288
 5111, 3.573375600145006, -30.38627042393775
"""
