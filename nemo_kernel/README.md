# nemo_kernel

`nemo_kernel` is a Jupyter kernel under development. The kernel is an effort to utilise Jupyter Lab as a user interface for Nemo Datalog Reasoner.

More detail on Nemo [here](https://github.com/knowsys/nemo/tree/main).

## Installation

To install `nemo_kernel` from git into a Conda environment

1. Create and activate a conda environment if not done so.
2. Ensure the followings are installed: `metakernel`, `maturin`, `jupyter`, `jupyterlab`, `ipykernel`. If not, install with `pip` or `conda`.
3. Install `nmo_python`

    `nemo` is required for this step: [nemo](https://github.com/knowsys/nemo)
    1. Direct the terminal to nemo-python folder inside nemo directory.
    2. Run `maturin develop`

4. At your desire directory, download nemo_kernel and install

    ```bash
    git clone https://github.com/DanCat6300/nemo-jupyterlab.git
    cd nemo-jupyterlab/nemo_kernel
    pip install .
    or
    pip install -e . # For development
    ```

## Using the nemo kernel

**Jupyter Lab**: The kernel is available to choose in the kernel list.

**Console frontends**: To use it with the console frontends, add ``--kernel nemo`` to
their command line arguments.

## Troubleshooting

In case the kernel is not detectable or nmo-python is not found:

1. Check whether you have installed nmo-python before installing the kernel.

    ```cmd
    conda list
    ```

2. Check which python executable you are using, this relates to incorrect virtual environment.

    ```bash
    which python
    ```
