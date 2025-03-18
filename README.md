# Nemo-Jupyterlab

This repository serves as code storage for the team project.

The project is to develop a kernel with Nemo Datalog Reasoner as an interpreter.
This may also involves extending UI components of the frontend, Jupyter Lab.

See jlx_nemo for frontend extension.
See kernel development in the nemo_kernel folder.

## Project setup

To avoid dependency conflict, a virtual environment should be set up.

1. Install *Anaconda* to use `conda` for terminal commands.
2. Create a conda environment and **activate the environment**.

    ```shell
    conda create -n [env_name] --override-channels --strict-channel-priority -c conda-forge -c nodefaults jupyterlab nodejs git copier=7 jinja2-time
    ```

    Terminal may need to be restarted before activating an environment for the first time

    ```shell
    conda init
    conda activate [env_name]
    ```

&nbsp;

The project consists of 2 parts: kernel (backend development) and jupyterlab extension (mainly frontend).

### Set up jupyter lab extension template

The setup process is described  in Jupyter's documentation:
<https://jupyterlab.readthedocs.io/en/stable/extension/extension_dev.html#developer-extensions>

There is also a tutorial by Jupyter:
<https://jupyterlab.readthedocs.io/en/stable/extension/extension_tutorial.html>

Below are the steps specifically for this project:

**Note**: Activate conda environment if not done so.

1. Direct to the extension's folder to install dependencies and build the extension

    ```shell
    jlpm install
    jlpm run build
    ```

2. Install the extension to be used in Jupyter Lab

    ```shell
    jupyter labextension develop --overwrite
    ```

    The extension should appear in a list when run this command

    ```shell
    jupyter labextension list
    ```

3. Open another terminal and test run

    ```shell
    conda activate [env_name]
    jupyter lab
    ```

    When check the console on your browser devtool, you should see a message that the extension has been activated.

4. Start extending Jupyter Lab :)

    When making changes to the code, you only need to run `jlpm run build` and refresh the browser.

### Set up and install the kernel

**Note**: It is recommend to do this outside of the Jupyterlab extension folder.

1. Activate conda environment if not done so.
2. Ensure the followings are installed: `metakernel`, `maturin`, `jupyter`, `jupyterlab`, `ipykernel`. If not, install with `pip` or `conda`.
3. Install `nmo_python`

    `nemo` is required for this step: <https://github.com/knowsys/nemo>
    1. Direct the terminal to nemo-python folder inside nemo directory.
    2. Run `maturin develop`
    3. Redirect back to project directory.

4. Install the kernel to be recognised by Jupyter Lab

    ```shell
    python -m ipykernel install --user --name "[env_name]" --display-name "[kernel_name] ([env])"
    ```

5. Access the location where the `kernel.json` is newly created and replace `ipython_launcher` with `nemo_kernel` in the file. The file location can be seen on the terminal after running the previous command.
6. **At the location of `nemo_kernel.py`**, start Jupyter Lab and test run.

## Language Server

Please see `README.md` in `jl_config` and `language_server_changes`.

&nbsp;

This concludes the long project set up :)

Please reach out if encounter any problem.

(Setup may change in the future)
