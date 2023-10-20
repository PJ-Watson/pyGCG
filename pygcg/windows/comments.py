from pathlib import Path

import customtkinter as ctk

from .base_window import BaseWindow


class CommentsWindow(BaseWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, title="Comments", **kwargs)
        self.top_label.configure(
            text=f"Insert any additional comments for object "
            f"{self._root().current_gal_id.get()} here:"
        )
        self.action_button.configure(text="Save")

    def create_text_box(self):
        super().create_text_box()
        if "comments" in self._root().current_gal_data.keys():
            self.text_box.insert("1.0", self._root().current_gal_data["comments"])

    def action_button_callback(self, event=None):
        self._root().current_gal_data["comments"] = self.text_box.get("1.0", "end")
        self.destroy()
