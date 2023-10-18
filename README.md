# pyGCG: GLASS-JWST Classification GUI

A Python GUI to aid in viewing and classifying NIRISS data products from GLASS-JWST.

## Installation

In all cases, it is strongly recommended to install `pyGCG` into a new virtual environment, to minimise dependency conflicts (see [Requirements](#requirements)).

### Using pip (recommended)

`pyGCG` can be installed directly from the [Python Package Index (PyPI)](https://pypi.org/project/pyGCG/), by running:

```pip install --upgrade pygcg```

### Building from source

Alternatively, to clone the latest GitHub repository, use this command:

```git clone https://github.com/PJ-Watson/pyGCG.git```

To build and install `pyGCG`, run (from the root of the source tree):

```pip install .```

## Usage

### Launching the GUI

In the most basic configuration, `pyGCG` can be run in a Python session as follows:

<code>
from pygcg.GUI_main import run_app

run_app()
</code>

Alternatively, `pyGCG` can be launched from the terminal using a single line:

```python -c "from pygcg.GUI_main import run_app; run_app()```

### Configuration file

TODO

## Requirements

`pyGCG` has the following strict requirements:

 - [Python](https://www.python.org/) 3.10 or later
 - [NumPy](https://www.numpy.org/) 1.24 or later
 - [Matplotlib](https://matplotlib.org/) 3.6 or later
 - [Astropy](https://www.astropy.org/) 5.3 or later
 - [CustomTkinter](https://customtkinter.tomschimansky.com/) 5.2 or later
 - [CTkMessageBox](https://github.com/Akascape/CTkMessagebox/) 2.5 or later
 - [Photutils](https://photutils.readthedocs.io/) 1.9 or later
 - [TOML Kit](https://tomlkit.readthedocs.io/) 0.12 or later
 - [tqdm](https://tqdm.github.io/) 4.66 or later

`pyGCG` has been tested with Python 3.10, and is developed primarily on Python 3.11. Note that not all of the required packages may yet be compatible with Python 3.12.
