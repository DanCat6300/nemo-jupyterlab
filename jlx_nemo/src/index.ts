import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

/**
 * Initialization data for the jlx_nemo extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'jlx_nemo:plugin',
  description: 'Jupyter Lab extension with Nemo Datalog Reasoner',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log('JupyterLab extension jlx_nemo is activated!');
  }
};

export default plugin;
