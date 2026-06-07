import React from 'react';
import { DiffEditor } from '@monaco-editor/react';

function PRViewer({ originalCode, modifiedCode, language="python" }) {
  return (
    <div className="h-[500px] border border-slate-200 rounded-lg overflow-hidden shadow-inner">
      <DiffEditor
        original={originalCode}
        modified={modifiedCode}
        language={language}
        theme="light"
        options={{
          readOnly: true,
          renderSideBySide: false, // Unified diff view
          minimap: { enabled: false },
        }}
      />
    </div>
  );
}

export default PRViewer;
