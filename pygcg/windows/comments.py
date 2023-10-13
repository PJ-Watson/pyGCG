from pathlib import Path

import customtkinter as ctk


class CommentsWindow(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("720x568")
        self.title("Comments")

        # Key bindings
        self.protocol("WM_DELETE_WINDOW", self.quit_comments_gracefully)
        self.bind("<Control-w>", self.quit_comments_gracefully)
        self.bind("<Control-s>", self.quit_comments_gracefully)

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        # self.scrollable_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.pack(side="top", fill="both", expand=True)

        # self.comments_var = ctk.StringVar(
        #     self, ""
        # )
        self.comments_label = ctk.CTkLabel(
            self.main_frame,
            text=f"Insert any additional comments for object {self._root().current_gal_id.get()} here:",
        )
        self.comments_label.grid(
            row=0,
            column=0,
            padx=20,
            pady=(10, 0),
        )

        self.comments_box = ctk.CTkTextbox(
            self.main_frame,
            # textvariable=self.comments_var,
        )
        if "comments" in self._root().current_gal_data.keys():
            self.comments_box.insert("1.0", self._root().current_gal_data["comments"])

        self.comments_box.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="news")
        self.comments_box.bind("<Control-Key-a>", self.select_all)
        self.comments_box.bind("<Control-Key-A>", self.select_all)

        self.comments_save_button = ctk.CTkButton(
            self.main_frame,
            text="Save",
            command=self.quit_comments_gracefully,
        )
        self.comments_save_button.grid(
            row=2,
            column=0,
            padx=20,
            pady=(5, 10),
            # sticky="",
        )

    def select_all(self, event=None):
        self.comments_box.tag_add("sel", "1.0", "end")
        self.comments_box.mark_set("insert", "1.0")
        self.comments_box.see("insert")
        return "break"

    def quit_comments_gracefully(self, event=None):
        # Put some lines here to save current output
        # print ("need to save comments here")
        # print (self.comments_box.get("1.0", "end"))
        self._root().current_gal_data["comments"] = self.comments_box.get("1.0", "end")
        self.destroy()
