import re

import astropy.units as u
import customtkinter as ctk
import numpy as np
from astropy.coordinates import SkyCoord
from CTkMessagebox import CTkMessagebox

from pygcg.utils import ValidateFloatVar

from .base_window import BaseWindow


class SearchWindow(BaseWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            title="Find Multiple Objects",
            top_text="Insert each object on a new line.",
            **kwargs,
        )
        self.action_button.configure(text="Search")
        self.top_label.grid_configure(columnspan=1)

        radius_frame = ctk.CTkFrame(
            self.main_frame, fg_color=self._root().bg_colour_name
        )
        radius_frame.grid(row=0, column=1, sticky="ew")
        radius_label = ctk.CTkLabel(radius_frame, text="Search radius (arcsec):")
        radius_label.grid(row=0, column=0, padx=(10, 5), pady=(10, 0), sticky="e")

        self.search_radius = ValidateFloatVar(self)
        self.search_radius.set(1.0)
        self.radius_entry = ctk.CTkEntry(radius_frame, textvariable=self.search_radius)
        self.radius_entry.grid(row=0, column=1, padx=(5, 10), pady=(10, 0), sticky="w")

    def warn_input(self, exception=None):
        error = CTkMessagebox(
            title="Error",
            message=exception,
            icon="cancel",
            option_focus=1,
        )
        if error.get() == "OK":
            self.focus_force()
            return

    def action_button_callback(self, event=None):
        if hasattr(self, "ids_arr"):
            del self.ids_arr

        text_input = self.text_box.get("1.0", "end")

        lines = re.split("\n", text_input.strip())

        try:
            parts = re.split("\s*[,|;|\s]\s*", lines[0].strip())
        except Exception as e:
            self.warn_input(f"Could not parse input: {e}")
            return

        ras = np.empty(len(lines), dtype=object)
        decs = np.empty_like(ras, dtype=object)

        try:
            if len(parts) == 3:
                self.ids_arr = np.empty_like(ras, dtype=object)
                for i, l in enumerate(lines):
                    # print(re.split("\s*[,|;|\s]\s*", l.strip()))
                    self.ids_arr[i], ras[i], decs[i] = re.split(
                        "\s*[,|;|\s]\s*", l.strip()
                    )

            elif len(parts) == 2:
                for i, l in enumerate(lines):
                    # print(re.split("\s*[,|;|\s]\s*", l.strip()))
                    ras[i], decs[i] = re.split("\s*[,|;|\s]\s*", l.strip())
            else:
                raise ValueError()
        except Exception as e:
            self.warn_input(
                "Could not parse input: input must be either "
                "two or three components per line."
            )
            return

        try:
            new_coords = SkyCoord(ras.astype(float) * u.deg, decs.astype(float) * u.deg)
        except Exception as e:
            try:
                new_coords = SkyCoord(ras, decs)
            except Exception as e:
                try:
                    new_coords = SkyCoord(ras, decs, unit=(u.hourangle, u.deg))
                except Exception as e:
                    self.warn_input(f"Could not parse input coordinates: {e}")
                    return

        sky_match_idx, dist, _ = new_coords.match_to_catalog_sky(
            self._root().sky_coords
        )

        sky_match_idx = sky_match_idx[
            dist <= float(self.search_radius.get()) * u.arcsec
        ]
        if hasattr(self, "ids_arr"):
            self.ids_arr = self.ids_arr[
                dist <= float(self.search_radius.get()) * u.arcsec
            ]

        _, unique_idx = np.unique(sky_match_idx, return_index=True)
        match_idx = sky_match_idx[np.sort(unique_idx)]
        if hasattr(self, "ids_arr"):
            self.ids_arr = self.ids_arr[np.sort(unique_idx)]

        if len(match_idx) == 0:
            self.warn_input("No matches found!")
            return

        check_confirm = CTkMessagebox(
            title="Confirm Selection",
            message=(
                f"{len(match_idx)}/{len(ras)} entries have a unique match in the "
                "current catalogue. View only these objects?"
            ),
            icon="question",
            option_1="Cancel",
            option_2="Confirm",
            option_focus=2,
        )
        if check_confirm.get() == "Cancel":
            self.focus_force()
            return

        self._root().id_col = self.ids_arr
        self._root().seg_id_col = self._root().seg_id_col[match_idx]
        self._root().cat = self._root().cat[match_idx]
        self._root().sky_coords = SkyCoord(
            self._root().cat[
                self._root().config.get("catalogue", {}).get("ra", "X_WORLD")
            ],
            self._root().cat[
                self._root().config.get("catalogue", {}).get("dec", "Y_WORLD")
            ],
        )

        self._root().current_gal_id.set(self._root().id_col[0])
        self._root().tab_row = self._root().cat[0]
        self._root().seg_id = self._root().seg_id_col[0]
        if hasattr(self._root(), "current_seg_id"):
            self._root().current_seg_id.set(self._root().seg_id)

        self._root().set_current_data()

        self._root().generate_tabs()
