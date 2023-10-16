import sys
import tkinter as tk
import warnings
from typing import Callable, Literal, Optional, Tuple, Union

import customtkinter as ctk
import numpy as np
from customtkinter.windows.widgets.utility import (
    check_kwargs_empty,
    pop_from_dict_by_set,
)
from matplotlib import cbook
from matplotlib.backend_bases import NavigationToolbar2
from matplotlib.backends._backend_tk import ToolTip
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from PIL import Image, ImageOps


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


class IconCheckBox(ctk.CTkBaseClass):
    """
    Checkbox with rounded corners. Default is fg_color=None (transparent fg_color).
    """

    # attributes that are passed to and managed by the tkinter entry only:
    _valid_tk_label_attributes = {
        "cursor",
        "justify",
        "padx",
        "pady",
        "textvariable",
        "state",
        "takefocus",
        "underline",
    }

    def __init__(
        self,
        master: any,
        checked_icon: Union[str, ctk.CTkImage] = None,
        unchecked_icon: Union[str, ctk.CTkImage] = None,
        dark_checked_icon: Optional[ctk.CTkImage] = None,  # Add icons for dark theme
        dark_unchecked_icon: Optional[ctk.CTkImage] = None,
        auto_dark_icon: bool = False,  # If dark theme image not given, this will automatically invert the
        # image supplied to create a dark theme image
        width: int = 20,
        height: int = 20,
        corner_radius: Optional[int] = None,
        border_width: Optional[int] = None,
        border_spacing: int = 2,
        on_value: Union[int, str, bool] = 1,
        off_value: Union[int, str, bool] = 0,
        command: Optional[Callable] = None,
        state: Literal["normal", "disabled"] = "normal",
        hover: bool = True,
        bg_color: Union[str, Tuple[str, str]] = "transparent",
        fg_color: Optional[Union[str, Tuple[str, str]]] = None,
        text_color: Optional[Union[str, Tuple[str, str]]] = None,
        hover_color: Optional[Union[str, Tuple[str, str]]] = None,
        border_color: Optional[Union[str, Tuple[str, str]]] = None,
        text_color_disabled: Optional[Union[str, Tuple[str, str]]] = None,
        text: str = "",
        font: Optional[Union[tuple, ctk.CTkFont]] = None,
        variable: Optional[tk.Variable] = None,
        compound: str = "center",
        anchor: str = "center",  # label anchor: center, n, e, s, w
        wraplength: int = 0,
        **kwargs,
    ):
        # transfer basic functionality (_bg_color, size, __appearance_mode, scaling) to ctk.CTkBaseClass
        super().__init__(master=master, bg_color=bg_color, width=width, height=height)

        # color
        self._fg_color = (
            ctk.ThemeManager.theme["CTkLabel"]["fg_color"]
            if fg_color is None
            else self._check_color_type(fg_color, transparency=True)
        )
        self._text_color = (
            ctk.ThemeManager.theme["CTkLabel"]["text_color"]
            if text_color is None
            else self._check_color_type(text_color)
        )
        self._hover_color: Union[str, Tuple[str, str]] = (
            ctk.ThemeManager.theme["CTkButton"]["hover_color"]
            if hover_color is None
            else self._check_color_type(hover_color)
        )
        self._border_color: Union[str, Tuple[str, str]] = (
            ctk.ThemeManager.theme["CTkButton"]["border_color"]
            if border_color is None
            else self._check_color_type(border_color)
        )
        self._text_color_disabled: Union[str, Tuple[str, str]] = (
            ctk.ThemeManager.theme["CTkButton"]["text_color_disabled"]
            if text_color_disabled is None
            else self._check_color_type(text_color_disabled)
        )
        self._original_color: Union[str, Tuple[str, str]] = ctk.ThemeManager.theme[
            "CTkFrame"
        ]["fg_color"]

        # state
        self._state = state
        self._check_state = False

        # hover
        self._hover = hover

        # shape
        self._size = (width, height)
        self._corner_radius: int = (
            ctk.ThemeManager.theme["CTkButton"]["corner_radius"]
            if corner_radius is None
            else corner_radius
        )
        self._corner_radius = min(self._corner_radius, round(self._current_height / 2))
        self._border_width: int = (
            ctk.ThemeManager.theme["CTkButton"]["border_width"]
            if border_width is None
            else border_width
        )
        self._border_spacing: int = border_spacing

        # text
        self._anchor = anchor
        self._text = text
        self._wraplength = wraplength
        self._compound = compound

        # image
        self.dark_checked_icon = self._check_image_type(
            dark_checked_icon, make_compatible=not auto_dark_icon
        )
        self.dark_unchecked_icon = self._check_image_type(
            dark_unchecked_icon, make_compatible=not auto_dark_icon
        )
        self.checked_icon = self._check_image_type(
            checked_icon, make_compatible=not auto_dark_icon
        )
        self.unchecked_icon = self._check_image_type(
            unchecked_icon, make_compatible=not auto_dark_icon
        )

        if self.dark_checked_icon is None:
            if auto_dark_icon:
                self.dark_checked_icon = self.invert_image(self.checked_icon)
        if self.dark_unchecked_icon is None:
            self.dark_unchecked_icon = self.invert_image(self.unchecked_icon)

        try:
            self.checked_icon = ctk.CTkImage(self.checked_icon)
            self.unchecked_icon = ctk.CTkImage(self.unchecked_icon)
        except:
            warnings.warn(
                "Could not convert images to type ctk.CTkImage. Try using a directory instead."
            )

        if isinstance(self.checked_icon, ctk.CTkImage):
            self.checked_icon._dark_image = self.dark_checked_icon
            self.checked_icon.add_configure_callback(self._update_image)
        if isinstance(self.unchecked_icon, ctk.CTkImage):
            self.unchecked_icon._dark_image = self.dark_unchecked_icon
            self.unchecked_icon.add_configure_callback(self._update_image)

        # checked state
        self._checked_state = False
        self._on_value = on_value
        self._off_value = off_value

        # font
        self._font = ctk.CTkFont() if font is None else self._check_font_type(font)
        if isinstance(self._font, ctk.CTkFont):
            self._font.add_size_configure_callback(self._update_font)

        # command
        self._command = command

        # configure grid system (1x1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._canvas = ctk.CTkCanvas(
            master=self,
            highlightthickness=0,
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height),
        )
        self._draw_engine = ctk.DrawEngine(self._canvas)

        self._variable: tk.Variable = variable

        self._label = tk.Label(
            master=self,
            highlightthickness=0,
            padx=0,
            pady=0,
            borderwidth=0,
            anchor=self._anchor,
            compound=self._compound,
            wraplength=self._apply_widget_scaling(self._wraplength),
            text=self._text,
            font=self._apply_font_scaling(self._font),
        )
        self._label.configure(
            **pop_from_dict_by_set(kwargs, self._valid_tk_label_attributes)
        )

        check_kwargs_empty(kwargs, raise_error=True)

        self._create_grid()
        self._create_bindings()
        self._set_cursor()
        self._update_image()
        self._draw()

    def _set_cursor(self):
        if self._cursor_manipulation_enabled:
            if self._state == tk.DISABLED:
                if sys.platform == "darwin":
                    self._canvas.configure(cursor="arrow")
                elif sys.platform.startswith("win"):
                    self._canvas.configure(cursor="arrow")

            elif self._state == tk.NORMAL:
                if sys.platform == "darwin":
                    self._canvas.configure(cursor="pointinghand")
                elif sys.platform.startswith("win"):
                    self._canvas.configure(cursor="hand2")

    def _check_image_type(self, image: any, make_compatible=True):
        """check image type when passed to widget
        :param make_compatible:
        """
        if image is None:
            return image
        elif isinstance(image, str):
            if make_compatible:
                return ctk.CTkImage(Image.open(image), size=self._size)
            else:
                return Image.open(image)
        elif type(image) == Image:
            if make_compatible:
                return ctk.CTkImage(image, size=self._size)
            else:
                return image

        elif isinstance(image, ctk.CTkImage):
            return image
        else:
            warnings.warn(
                f"{type(self).__name__} Warning: Given image is not ctk.CTkImage but {type(image)}. Image can not be "
                f"scaled on HighDPI displays, use ctk.CTkImage or directory instead.\n"
            )
            return image

    def _create_bindings(self, sequence: Optional[str] = None):
        """set necessary bindings for functionality of widget, will overwrite other bindings"""
        if sequence is None or sequence == "<Enter>":
            self.bind("<Enter>", self._on_enter)
        if sequence is None or sequence == "<Leave>":
            self.bind("<Leave>", self._on_leave)
        if sequence is None or sequence == "<Button-1>":
            self.bind("<Button-1>", self.toggle)

    def _on_enter(self, event=0):
        if self._hover is True and self._state == tk.NORMAL:
            if self._cursor_manipulation_enabled:
                self._label.config(cursor="hand2")
            self._label.config(bg=self._apply_appearance_mode(self._hover_color))
            if self._check_state is True:
                self._canvas.itemconfig(
                    "inner_parts",
                    fill=self._apply_appearance_mode(self._hover_color),
                    outline=self._apply_appearance_mode(self._hover_color),
                )
                self._canvas.itemconfig(
                    "border_parts",
                    fill=self._apply_appearance_mode(self._hover_color),
                    outline=self._apply_appearance_mode(self._hover_color),
                )
            else:
                self._canvas.itemconfig(
                    "inner_parts",
                    fill=self._apply_appearance_mode(self._hover_color),
                    outline=self._apply_appearance_mode(self._hover_color),
                )

    def _on_leave(self, event=0):
        if self._fg_color == "transparent":
            fg_color = self._bg_color
        else:
            fg_color = self._fg_color
        if self._check_state is True:
            if self._fg_color == "transparent":
                inner_parts_color = self._bg_color
            else:
                inner_parts_color = self._fg_color

            self._canvas.itemconfig(
                "inner_parts",
                fill=self._apply_appearance_mode(inner_parts_color),
                outline=self._apply_appearance_mode(inner_parts_color),
            )
            self._canvas.itemconfig(
                "border_parts",
                fill=self._apply_appearance_mode(self._fg_color),
                outline=self._apply_appearance_mode(self._fg_color),
            )
            self._label.config(
                cursor="", bg=self._apply_appearance_mode(inner_parts_color)
            )
        else:
            self._canvas.itemconfig(
                "inner_parts",
                fill=self._apply_appearance_mode(self._bg_color),
                outline=self._apply_appearance_mode(self._bg_color),
            )
            self._canvas.itemconfig(
                "border_parts",
                fill=self._apply_appearance_mode(self._border_color),
                outline=self._apply_appearance_mode(self._border_color),
            )
            self._label.config(
                cursor="", bg=self._apply_appearance_mode(self._bg_color)
            )

    def toggle(self, event=0):
        if self._state == tk.NORMAL:
            if self._checked_state is True:
                self._checked_state = False
                self._update_image()
                self._draw()
            else:
                self._checked_state = True
                self._update_image()
                self._draw()

            if self._variable is not None:
                self._variable_callback_blocked = True
                self._variable.set(
                    self._on_value if self._check_state is True else self._off_value
                )
                self._variable_callback_blocked = False

            if self._command is not None:
                self._command()

            self._on_enter()

    def select(self, from_variable_callback=False):
        self._check_state = True
        self._draw()

        if self._variable is not None and not from_variable_callback:
            self._variable_callback_blocked = True
            self._variable.set(self._on_value)
            self._variable_callback_blocked = False

    def deselect(self, from_variable_callback=False):
        self._check_state = False
        self._draw()

        if self._variable is not None and not from_variable_callback:
            self._variable_callback_blocked = True
            self._variable.set(self._off_value)
            self._variable_callback_blocked = False

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)

        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height),
        )
        self._label.configure(font=self._apply_font_scaling(self._font))
        self._label.configure(wraplength=self._apply_widget_scaling(self._wraplength))

        self._create_grid()
        self._update_image()
        self._draw(no_color_updates=True)

    def _set_appearance_mode(self, mode_string):
        super()._set_appearance_mode(mode_string)
        self._update_image()

    def _set_dimensions(self, width=None, height=None):
        super()._set_dimensions(width, height)
        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height),
        )
        self._create_grid()
        self._draw()

    def _update_font(self):
        """pass font to tkinter widgets with applied font scaling and update grid with workaround"""
        self._label.configure(font=self._apply_font_scaling(self._font))

        # Workaround to force grid to be resized when text changes size.
        # Otherwise, grid will lag and only resizes if other mouse action occurs.
        self._canvas.grid_forget()
        self._canvas.grid(row=0, column=0, sticky="nsew")

    def _update_image(self):
        new_image = self.checked_icon if self._checked_state else self.unchecked_icon

        if isinstance(new_image, ctk.CTkImage):
            self._label.configure(
                image=new_image.create_scaled_photo_image(
                    self._get_widget_scaling(), self._get_appearance_mode()
                )
            )
        elif new_image is not None:
            self._label.configure(image=new_image)

    def destroy(self):
        if isinstance(self._font, ctk.CTkFont):
            self._font.remove_size_configure_callback(self._update_font)
        super().destroy()

    def get(self):
        return self._on_value if self._checked_state else self._off_value

    def _create_grid(self):
        """configure grid system (1x1)"""

        text_label_grid_sticky = self._anchor if self._anchor != "center" else ""
        self._label.grid(
            row=0,
            column=0,
            sticky=text_label_grid_sticky,
            padx=self._apply_widget_scaling(
                min(self._corner_radius, round(self._current_height / 2))
            ),
        )
        self._canvas.grid(row=0, column=0, sticky="nsew")

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)
        requires_recoloring = self._draw_engine.draw_rounded_rect_with_border(
            self._apply_widget_scaling(self._current_width),
            self._apply_widget_scaling(self._current_height),
            self._apply_widget_scaling(self._corner_radius),
            0,
        )

        if no_color_updates is False or requires_recoloring:
            if self._apply_appearance_mode(self._fg_color) == "transparent":
                self._canvas.itemconfig(
                    "inner_parts",
                    fill=self._apply_appearance_mode(self._bg_color),
                    outline=self._apply_appearance_mode(self._bg_color),
                )

                self._label.configure(
                    fg=self._apply_appearance_mode(self._text_color),
                    bg=self._apply_appearance_mode(self._bg_color),
                )
            else:
                if self._checked_state:
                    self._canvas.itemconfig(
                        "inner_parts",
                        fill=self._apply_appearance_mode(self._fg_color),
                        outline=self._apply_appearance_mode(self._fg_color),
                    )

                    self._canvas.itemconfig(
                        "border_parts",
                        fill=self._apply_appearance_mode(self._border_color),
                        outline=self._apply_appearance_mode(self._border_color),
                    )

                    self._label.configure(
                        fg=self._apply_appearance_mode(self._text_color),
                        bg=self._apply_appearance_mode(self._fg_color),
                    )

                else:
                    self._canvas.itemconfig(
                        "inner_parts",
                        fill=self._apply_appearance_mode(self._bg_color),
                        outline=self._apply_appearance_mode(self._bg_color),
                    )
                    self._canvas.itemconfig(
                        "border_parts",
                        fill=self._apply_appearance_mode(self._border_color),
                        outline=self._apply_appearance_mode(self._border_color),
                    )

                    self._label.configure(
                        fg=self._apply_appearance_mode(self._text_color),
                        bg=self._apply_appearance_mode(self._bg_color),
                    )

            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))

    def configure(self, require_redraw=False, **kwargs):
        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self._set_cursor()
            require_redraw = True

        if "corner_radius" in kwargs:
            self._corner_radius = kwargs.pop("corner_radius")
            self._create_grid()
            require_redraw = True

        if "fg_color" in kwargs:
            self._fg_color = self._check_color_type(
                kwargs.pop("fg_color"), transparency=True
            )
            require_redraw = True

        if "text_color" in kwargs:
            self._text_color = self._check_color_type(kwargs.pop("text_color"))
            require_redraw = True

        if "text" in kwargs:
            self._text = kwargs.pop("text")
            self._label.configure(text=self._text)

        if "font" in kwargs:
            if isinstance(self._font, ctk.CTkFont):
                self._font.remove_size_configure_callback(self._update_font)
            self._font = self._check_font_type(kwargs.pop("font"))
            if isinstance(self._font, ctk.CTkFont):
                self._font.add_size_configure_callback(self._update_font)
            self._update_font()

        if "compound" in kwargs:
            self._compound = kwargs.pop("compound")
            self._label.configure(compound=self._compound)

        if "anchor" in kwargs:
            self._anchor = kwargs.pop("anchor")
            self._label.configure(anchor=self._anchor)
            self._create_grid()

        if "wraplength" in kwargs:
            self._wraplength = kwargs.pop("wraplength")
            self._label.configure(
                wraplength=self._apply_widget_scaling(self._wraplength)
            )

        if "checked_icon" in kwargs:
            self.checked_icon = kwargs.pop("checked_icon")
            require_redraw = True

        if "unchecked_icon" in kwargs:
            self.checked_icon = kwargs.pop("unchecked_icon")
            require_redraw = True

        self._label.configure(
            **pop_from_dict_by_set(kwargs, self._valid_tk_label_attributes)
        )  # configure tkinter.Label

        super().configure(
            require_redraw=require_redraw, **kwargs
        )  # configure ctk.CTkBaseClass

    def cget(self, attribute_name: str) -> any:
        if attribute_name == "corner_radius":
            return self._corner_radius

        elif attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "text_color":
            return self._text_color

        elif attribute_name == "text":
            return self._text
        elif attribute_name == "font":
            return self._font
        elif attribute_name == "checked_icon":
            return self.checked_icon
        elif attribute_name == "unchecked_icon":
            return self.unchecked_icon
        elif attribute_name == "compound":
            return self._compound
        elif attribute_name == "anchor":
            return self._anchor
        elif attribute_name == "wraplength":
            return self._wraplength

        elif attribute_name in self._valid_tk_label_attributes:
            return self._label.cget(attribute_name)  # cget of tkinter.Label
        else:
            return super().cget(attribute_name)  # cget of ctk.CTkBaseClass

    def bind(self, sequence: str = None, command: Callable = None, add: str = True):
        """called on the tkinter.Label and tkinter.Canvas"""
        if not (add == "+" or add is True):
            raise ValueError(
                "'add' argument can only be '+' or True to preserve internal callbacks"
            )
        self._canvas.bind(sequence, command, add=True)
        self._label.bind(sequence, command, add=True)

    def unbind(self, sequence: str = None, funcid: Optional[str] = None):
        """called on the tkinter.Label and tkinter.Canvas"""
        if funcid is not None:
            raise ValueError(
                "'funcid' argument can only be None, because there is a bug in"
                + " tkinter and its not clear whether the internal callbacks will be unbinded or not"
            )
        self._canvas.unbind(sequence, None)
        self._label.unbind(sequence, None)

    def focus(self):
        return self._label.focus()

    def focus_set(self):
        return self._label.focus_set()

    def focus_force(self):
        return self._label.focus_force()

    def invert_image(self, image) -> Image:
        """Invert an image and return the inverted image"""
        try:
            if image.mode == "RGBA":
                r, g, b, a = image.split()
                rgb_image = Image.merge("RGB", (r, g, b))
                inverted_image = ImageOps.invert(rgb_image)
                r2, g2, b2 = inverted_image.split()
                final_transparent_image = Image.merge("RGBA", (r2, g2, b2, a))
                return final_transparent_image
            else:
                inverted_image = ImageOps.invert(image)
                return inverted_image
        except AttributeError as e:
            warnings.warn(
                f"{e}\nAn incompatible file type was probably used. Use PIL to open a file instead."
            )
            return image
        except Exception as e:
            warnings.warn(f"{e}\nAn unknown error is preventing image inversion.")
            return image
