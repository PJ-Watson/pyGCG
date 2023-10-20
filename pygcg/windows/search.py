import customtkinter as ctk

from .base_window import BaseWindow


class SearchWindow(BaseWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            title="Find Multiple Objects",
            top_text="Insert each object on a new line:",
            **kwargs,
        )
        self.bind("<Control-s>", self.action_button_callback)
        self.action_button.configure(text="Search")

    # def create_text_box(self):
    #     super().create_text_box()
    # if "comments" in self._root().current_gal_data.keys():
    #     self.text_box.insert("1.0", self._root().current_gal_data["comments"])

    def action_button_callback(self, event=None):
        text_input = self.text_box.get("1.0", "end")

        # self._root().current_gal_data["comments"] = self.text_box.get("1.0", "end")
        # self.destroy()


# # SearchWindow=BaseWindow
# class SearchWindow(BaseWindow):
#     def __init__(self, *args, **kwargs):
#         print ("Fuck yeah")
#         super().__init__(*args, title="Find Multiple Objects", top_text="Search for objects here or something", **kwargs)
