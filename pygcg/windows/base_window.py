import customtkinter as ctk


class BaseWindow(ctk.CTkToplevel):
    def __init__(self, master, title=None, top_text="", **kwargs):
        super().__init__(master, **kwargs)
        self.geometry("720x568")
        self.title(title)
        self.top_text = top_text

        # Key bindings
        self.protocol("WM_DELETE_WINDOW", self.quit_no_action)
        self.bind("<Control-w>", self.quit_no_action)
        self.bind("<Control-s>", self.action_button_callback)

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid_columnconfigure((0, 1), weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.pack(side="top", fill="both", expand=True)

        self.create_top_label()
        self.create_text_box()
        self.action_button = ctk.CTkButton(
            self.main_frame,
            text="Action",
            command=self.action_button_callback,
        )
        self.action_button.grid(
            row=2,
            column=0,
            padx=20,
            pady=(5, 10),
        )
        self.close_button = ctk.CTkButton(
            self.main_frame,
            text="Cancel",
            command=self.quit_no_action,
        )
        self.close_button.grid(
            row=2,
            column=1,
            padx=20,
            pady=(5, 10),
        )

    def create_top_label(self):
        self.top_label = ctk.CTkLabel(
            self.main_frame,
            text=self.top_text,
        )
        self.top_label.grid(
            row=0,
            column=0,
            columnspan=2,
            padx=20,
            pady=(10, 0),
        )

    def create_text_box(self):
        self.text_box = ctk.CTkTextbox(
            self.main_frame,
        )

        self.text_box.grid(
            row=1, column=0, padx=20, pady=(10, 0), columnspan=2, sticky="news"
        )
        self.text_box.bind("<Control-Key-a>", self.select_all)
        self.text_box.bind("<Control-Key-A>", self.select_all)

    def select_all(self, event=None):
        self.text_box.tag_add("sel", "1.0", "end")
        self.text_box.mark_set("insert", "1.0")
        self.text_box.see("insert")
        return "break"

    def quit_no_action(self, event=None):
        self.destroy()

    def action_button_callback(self, event=None):
        return
