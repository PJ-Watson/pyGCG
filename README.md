# pyGCG: GLASS-JWST Classification GUI

A Python GUI to aid in viewing and classifying NIRISS data products from GLASS-JWST.

## Installation

In all cases, it is strongly recommended to install `pyGCG` into a new virtual environment, to minimise dependency conflicts (see [Requirements](#requirements)).

### Using pip (recommended)

`pyGCG` can be installed directly from the [Python Package Index (PyPI)](https://pypi.org/project/pyGCG/), by running:

```
pip install --upgrade pygcg
```

### Building from source

Alternatively, to clone the latest GitHub repository, use this command:

```
git clone https://github.com/PJ-Watson/pyGCG.git
```

To build and install `pyGCG`, run (from the root of the source tree):

```
pip install .
```

## Usage

### Launching the GUI

In the most basic configuration, `pyGCG` can be run in a Python session as follows:

```python
from pygcg.GUI_main import run_app
run_app()
```

Alternatively, `pyGCG` can be launched from the terminal using a single line:

```
python -c "from pygcg.GUI_main import run_app; run_app()"
```

## Configuration file

When launching `pyGCG`, one can pass the path of a configuration file using the `config_file` keyword:

```python
from pygcg.GUI_main import run_app
run_app(config_file="/path/to/your/config.toml")
```

By default, `pyGCG` will look for `config.toml` in the current working directory, and will create this file if it doesn't exist, using the included [`example.toml`](pygcg/example_config.toml).
This file will also be created if the supplied configuration file is invalid.

The configuration file is a TOML-formatted file organised into various sections, or tables.

### Files

This table describes the location of the necessary files and directories.

| Key | Description |
| --- | --- |
| `extractions_dir` | The directory in which NIRISS extractions are stored. By default, this is assumed to contain all ancillary data (catalogue, segmentation maps, direct images). |
| `out_dir` | The directory in which the `pyGCG` output will be stored. If no directory is provided, or it is not possible to create the supplied directory, `pyGCG` will run in read-only mode. |
| `cat_path` | The file path of the input catalogue. By default, `pyGCG` will search for a file matching `*ir.cat.fits` inside `extractions_dir`. The catalogue must contain columns that can be interpreted as `id`, `ra`, and `dec` (see [Cat](#cat)). |
| `prep_dir` | If different to `extractions_dir`, this can be used to specify the directory containing the segmentation map and direct images. |
| `cube_path` | The file path of the corresponding MUSE datacube. |
| `temp_dir` | The directory in which temporary files are stored. Defaults to `out_dir/.temp/`. |
| `skip_existing` | If `True`, `pyGCG` will skip loading objects which already exist in the output catalogue. |
| `out_cat_name` | The name of the output catalogue. Defaults to `pyGCG_output.fits`. |

### Grisms

This table specifies the grism filters and position angles used in observations.

| Key | Default | Description |
| --- | --- | --- |
| `R` | `"F200W"` | The name of the grism filter that will be mapped to the red channel in the RGB image. Conventionally, this would be the filter covering the longest wavelengths. |
| `G` | `"F150W"` | Same as above, but for the green channel. |
| `B` | `"F115W"` | Same as above, but for the blue channel. |
| `PA1` | `72.0` | The position angle (in degrees) of the first grism orientation. |
| `PA2` | `341.0` | The position angle (in degrees) of the first grism orientation. |

### Cat

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
