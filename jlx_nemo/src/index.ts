import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { 
  ILSPDocumentConnectionManager,
  IDocumentConnectionData, 
} from '@jupyterlab/lsp';
import { applySemanticTokens, getEditors } from './languageUtils';
import { INotebookTracker, NotebookPanel } from '@jupyterlab/notebook';
import { Cell } from '@jupyterlab/cells';

/**
 * Initialization data for the jlx_nemo extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'jlx_nemo:plugin',
  description: 'Jupyter Lab extension with Nemo Datalog Reasoner',
  autoStart: true,
  requires: [ILSPDocumentConnectionManager, INotebookTracker],
  activate: (app: JupyterFrontEnd, connectionManager: ILSPDocumentConnectionManager, notebookTracker: INotebookTracker) => {
    console.log('JupyterLab extension jlx_nemo is activated!');

    // Tracking notebook activities
    notebookTracker.currentChanged.connect((_, panel: NotebookPanel | null) => {
      if (!panel) return;
      const notebookModel = panel.model;
      if (!notebookModel) return;

      // Handle cell removal event
      notebookModel.cells.changed.connect((_, changes) => {
        if (changes.type === 'remove') sendCellIdsToKernel(panel);
      }) 
    });

    // Accessing the connection to the language server to apply manual action
    connectionManager.connected.connect((_, connectionData: IDocumentConnectionData) => {
      const capabilities = connectionData.connection?.serverCapabilities;
      if (capabilities && connectionData.virtualDocument.language === 'nemo') {
        console.log('Applying temporary adaptation for nemo-language-server');
        
        // Turn on document highlight request for jupyterlab-lsp
        if (!capabilities.documentHighlightProvider && capabilities.semanticTokensProvider) {
          console.log('Force activate document highlight request');
          Object.assign(capabilities, { documentHighlightProvider: true });
        }

        // Fetch and apply syntax highlighting on didChange/diagnostics 
        connectionData.connection.serverNotifications['textDocument/publishDiagnostics'].connect((_, params) => {
          const virtualDocument = connectionData.virtualDocument;
          const editors = getEditors(virtualDocument);
          applySemanticTokens(editors as any, connectionData);
        });
      }
    });
  }
};

/**
 * Function to send a list of cell ids to the kernel and trigger code execution
 */
function sendCellIdsToKernel(panel: NotebookPanel) {
  const kernel = panel.sessionContext.session?.kernel;
  const cellIds = panel.content.widgets
    .filter(widget => widget instanceof Cell)
    .map(cell => (cell as Cell).model.id);

  kernel?.sendShellMessage({
    content: {
      code: `cell_removal_event, ${JSON.stringify(cellIds)}`
    },
    header: {
      msg_id: 'cell_delete_notification',
      msg_type: 'execute_request',
      session: kernel.clientId,
      username: '',
      date: new Date().toDateString(),
      version: '5.0'
    },
    metadata: {},
    parent_header: {},
    buffers: [],
    channel: 'shell'
  });
}

export default plugin;
