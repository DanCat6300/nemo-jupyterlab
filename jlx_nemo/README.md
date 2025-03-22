# jlx_nemo

[![Github Actions Status](https://github.com/DanCat6300/nemo-jupyterlab/workflows/Build/badge.svg)](https://github.com/DanCat6300/nemo-jupyterlab/actions/workflows/build.yml)

Jupyter Lab extension with Nemo Datalog Reasoner

## Requirements

- JupyterLab >= 4.0.0

### Development install

Note: You will need NodeJS to build the extension package.

The `jlpm` command is JupyterLab's pinned version of
[yarn](https://yarnpkg.com/) that is installed with JupyterLab. You may use
`yarn` or `npm` in lieu of `jlpm` below.

**Note**: Activate conda environment if not done so.

```bash
# Clone the repo to your local environment
# Change directory to the jlx_nemo directory
# Install package in development mode
jlpm install
# Link your development version of the extension with JupyterLab
jupyter labextension develop --overwrite
# Rebuild extension Typescript source after making changes
jlpm run build
```

When check the console on your browser devtool, you should see a message that the extension has been activated.

The extension should appear in a list when run this command

```shell
jupyter labextension list
```

### Development uninstall

```bash
pip uninstall jlx_nemo
```

In development mode, you will also need to remove the symlink created by `jupyter labextension develop`
command. To find its location, you can run `jupyter labextension list` to figure out where the `labextensions`
folder is located. Then you can remove the symlink named `jlx_nemo` within that folder.

### Packaging the extension

See [RELEASE](RELEASE.md)
