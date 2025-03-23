# Jupyter Lab LSP config

## Instruction

***Make sure your virtual environment is activated***

Jupyter Lab LSP documentation: [here](https://jupyterlab-lsp.readthedocs.io/en/latest/index.html)

1. You must first install jupyterlab-lsp

    ```cmd
    pip install jupyterlab-lsp
    ```

    or

    ```cmd
    conda install jupyterlab-lsp
    ```

2. Search for `jupyter-lsp-jupyter-server.json` file in the list of directories after using this command.

    ```cmd
    jupyter --path
    ```

3. Edit your config following the this json file or just copy-paste (risky). **Change the absolute path according to your local**

4. Also modify your `kernel.json` file. See the file in the nemo_kernel folder.
