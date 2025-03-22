import os
import sys
import json
import shutil
from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from jupyter_client.kernelspec import KernelSpecManager
from tempfile import TemporaryDirectory

kernel_json = {
    "argv": [
        sys.executable,
        "-Xfrozen_modules=off",
        "-m",
        "nemo_kernel",
        "-f",
        "{connection_file}"
    ],
    "display_name": "nemo (nemo-jupyter)",
    "language": "nemo",
    "metadata": {
        "debugger": True
    }
}

class CustomHook(BuildHookInterface):
    def initialize(self, version, build_data):
        here = os.path.abspath(os.path.dirname(__file__))
        sys.path.insert(0, here)
        prefix = os.path.join(here, 'data_kernelspec')

        # Create a temporary directory for a kernel.json file
        with TemporaryDirectory() as td:
            os.chmod(td, 0o755)
            with open(os.path.join(td, 'kernel.json'), 'w') as f:
                json.dump(kernel_json, f, sort_keys=True)
            print('Installing Jupyter kernel spec...')

            # Attempt to get a logo for the kernel
            cur_path = os.path.dirname(os.path.realpath(__file__))
            for logo in ["logo-32x32.png", "logo-64x64.png"]:
                try:
                    shutil.copy(os.path.join(cur_path, logo), td)
                except FileNotFoundError:
                    print("Custom logo files not file. Using default logos.")

            KernelSpecManager().install_kernel_spec(td, 'nemo', user=False, prefix=prefix)
