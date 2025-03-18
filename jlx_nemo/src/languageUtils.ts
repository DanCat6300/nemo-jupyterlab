import {
  IDocumentConnectionData,
  VirtualDocument
} from '@jupyterlab/lsp';
import { EditorView, Decoration, DecorationSet } from '@codemirror/view';
import { StateField, StateEffect } from '@codemirror/state';

/**
 * Custom styling for nemo syntax highlighting.
 */
const nemoTheme = EditorView.baseTheme({
  ".cm-keyword": { color: "blue", fontWeight: "bold" },
  ".cm-variable": { color: "black" },
  ".cm-string": { color: "green" },
  ".cm-number": { color: "red" },
  ".cm-operator": { color: "purple" },
  ".cm-comment": { color: "gray", fontStyle: "italic" }
});

/**
 * Mapping of token types to CodeMirror classes.
 */
const tokenTypeMap: Record<number, string> = {
  0: "cm-type",
  1: "cm-variable",
  2: "cm-string",
  3: "cm-keyword",
  4: "cm-number",
  5: "cm-number",
  6: "cm-atom",
  7: "cm-property",
  8: "cm-operator",
  9: "cm-comment"
};

/**
 * Effect for updating ranges of semantic tokens.
 */
const setSemanticTokens = StateEffect.define<{ from: number, to: number, type: string }>({
  map: ({ from, to, type }, change) => ({ from: change.mapPos(from), to: change.mapPos(to), type: type })
});

/**
 * StateField to manage semantic token decorations.
 */
const semanticTokensField = StateField.define<DecorationSet>({
  create: () => Decoration.none,
  update(tokens, tr) {
    tokens = tokens.map(tr.changes);
    for (let e of tr.effects) {
      if (e.is(setSemanticTokens)) {
        tokens = tokens.update({
          add: [Decoration.mark({ class: e.value.type }).range(e.value.from, e.value.to)]
        })
      }
    }
    return tokens;
  },
  provide: (f) => EditorView.decorations.from(f)
});

/**
 * Trigger jupyterlab-lsp to request document highlight, embedded with semantic tokens.
 */
async function fetchSemanticTokens(connectionData: IDocumentConnectionData) {
  // Fetch syntax highlighting from nemo-language-server
  const response = await connectionData.connection.clientRequests['textDocument/documentHighlight'].request({
    textDocument: { uri: connectionData.virtualDocument.documentInfo.uri },
    position: { line: 0, character: 0 }
  }) ?? [];

  /*
  Map the response to a valid format
  This is a temporary fix until jupyterlab-lsp offer semanticTokens/full request.
  SemanticTokens {delta_line, delta_start, length, token_type}
  -> DocumentHighlight [range {start {line: delta_line, char: delta_start}, end {line: token_type, char: length}}]
  */
  let lastLine = 0, lastChar = 0;
  return response.map((highlight: any) => {
    let line = lastLine + highlight.range.start.line;
    let char = highlight.range.start.line === 0 ? lastChar + highlight.range.start.character : highlight.range.start.character;
    lastLine = line;
    lastChar = char;
    return {
      start: { line: line, char: char },
      end: { line: line, char: char + highlight.range.end.character },
      type: tokenTypeMap[highlight.range.end.line] || "cm-default"
    }
  })
}

/**
 * Distribute tokens into appropriate editors/cells
 */
function mapTokensToEditorViews(tokens: any[], editorViews: any[]) {
  let tokensByCells = [];
  let lastLine = 0;

  for (let editorView of editorViews) {
    let tokenCell = []
    for (let token of tokens) {
      if (token.start.line >= lastLine && token.start.line < editorView.lineCount + lastLine) {
        token.start.line -= lastLine;
        token.end.line -= lastLine;
        tokenCell.push(token);
      }
    }
    lastLine = editorView.lineCount + lastLine + 2;
    tokensByCells.push(tokenCell);
  }
  return tokensByCells;
}

/**
 * Retrieve all editors, each cell has an editor
 */
export function getEditors(virtualDocument: VirtualDocument) {
  let lastEditor = virtualDocument.getEditorAtVirtualLine({ line: 0, ch: 0, isVirtual: true }).getEditor();
  let editorsArr = [lastEditor];

  // Scan and retrive editors by lines of code in the virtual document
  for (let line = 0; line < virtualDocument.lastVirtualLine; line++) {
    const editor = virtualDocument.getEditorAtVirtualLine({ line: line, ch: 0, isVirtual: true }).getEditor();
    if (editor?.uuid !== lastEditor?.uuid) {
      lastEditor = editor;
      editorsArr.push(editor);
    }
  }

  return editorsArr;
}

/**
 * Applies semantic tokens as decorations in the CodeMirror editor.
 */
export async function applySemanticTokens(editors: object[], connectionData: IDocumentConnectionData) {
  // Retrieve semantic tokens and distribute them to the appropriate cells
  const tokens = await fetchSemanticTokens(connectionData);
  if (!tokens) return false;
  const tokensByCells = mapTokensToEditorViews(tokens, editors);

  // Apply semantic tokens to each editor
  for (let i = 0; i < editors.length; i++) {
    if (!tokensByCells[i].length) return false;

    const view = (editors[i] as any).editor;
    let effects: StateEffect<unknown>[] = tokensByCells[i].map((token: any) => setSemanticTokens.of({
      from: view.state.doc.line(token.start.line + 1).from + token.start.char,
      to: view.state.doc.line(token.end.line + 1).from + token.end.char,
      type: token.type
    }));

    if (!view.state.field(semanticTokensField, false)) {
      effects.push(StateEffect.appendConfig.of([semanticTokensField, nemoTheme]));
    }

    view.dispatch({ effects });
  }
  return true;
}
