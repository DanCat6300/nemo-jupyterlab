import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { 
  ILSPDocumentConnectionManager,
  IDocumentConnectionData, 
} from '@jupyterlab/lsp';
import { applySemanticTokens, getEditors } from './languageUtils';

/**
 * Initialization data for the jlx_nemo extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'jlx_nemo:plugin',
  description: 'Jupyter Lab extension with Nemo Datalog Reasoner',
  autoStart: true,
  requires: [ILSPDocumentConnectionManager],
  activate: (app: JupyterFrontEnd, connectionManager: ILSPDocumentConnectionManager) => {
    console.log('JupyterLab extension jlx_nemo is activated!');

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

export default plugin;
