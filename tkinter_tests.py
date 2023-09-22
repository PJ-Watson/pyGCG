import customtkinter

customtkinter.set_appearance_mode("system")
customtkinter.set_default_color_theme("blue")

# app = customtkinter.CTk()
# app.geometry("768x512")


# def button_function():
#     print("button pressed")


# button = customtkinter.CTkButton(
#     master=app,
#     text="CTkButton",
#     command=button_function,
# )
# button.place(relx=0.5, rely=0.5, anchor=customtkinter.CENTER)

# app.mainloop()


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        # self.geometry("768x512")
        self.geometry("1280x720")
        # self.geometry("1366x768")
        # self.attributes("-zoomed", True)

        self.button = customtkinter.CTkButton(
            self,
            text="Test Button",
            command=self.button_callback,
        )

        self.button.place(
            relx=0.5,
            rely=0.5,
            anchor=customtkinter.CENTER,
        )

    def button_callback(self):
        print("Button clicked!")


if __name__ == "__main__":
    app = App()
    app.mainloop()
