import { useState, useEffect } from 'react';
import { fetchProjectFiles, type ProjectFile } from '../api/sse';

interface Props {
  projectId: string;
  onClose: () => void;
}

const LANG_MAP: Record<string, string> = {
  html: 'html',
  htm: 'html',
  css: 'css',
  js: 'javascript',
  jsx: 'jsx',
  ts: 'typescript',
  tsx: 'tsx',
  json: 'json',
  md: 'markdown',
  py: 'python',
  svg: 'xml',
  xml: 'xml',
};

function getLang(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase() || '';
  return LANG_MAP[ext] || '';
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export default function SourceViewer({ projectId, onClose }: Props) {
  const [files, setFiles] = useState<ProjectFile[]>([]);
  const [activeFile, setActiveFile] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchProjectFiles(projectId)
      .then((data) => {
        setFiles(data);
        // Auto-select index.html or first file
        const first = data.find((f) => f.path.endsWith('index.html')) || data[0];
        if (first) setActiveFile(first.path);
      })
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load'))
      .finally(() => setLoading(false));
  }, [projectId]);

  const active = files.find((f) => f.path === activeFile);

  return (
    <div className="flex flex-col h-full bg-zinc-950">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-zinc-800">
        <div className="flex items-center gap-2">
          <span className="text-sm text-zinc-300">📁 Source Code</span>
          <span className="text-xs text-zinc-600">{files.length} files</span>
        </div>
        <button
          onClick={onClose}
          className="text-zinc-500 hover:text-zinc-300 text-sm px-2 py-0.5 rounded hover:bg-zinc-800"
        >
          ✕
        </button>
      </div>

      {loading && (
        <div className="flex-1 flex items-center justify-center text-zinc-500 text-sm">
          Loading...
        </div>
      )}

      {error && (
        <div className="flex-1 flex items-center justify-center text-red-400 text-sm">
          {error}
        </div>
      )}

      {!loading && !error && (
        <div className="flex flex-1 overflow-hidden">
          {/* File tree */}
          <div className="w-52 border-r border-zinc-800 overflow-y-auto flex-shrink-0">
            {files
              .filter((f) => !f.binary)
              .map((f) => (
                <button
                  key={f.path}
                  onClick={() => setActiveFile(f.path)}
                  className={`w-full text-left px-3 py-1.5 text-xs flex items-center gap-2 transition-colors ${
                    f.path === activeFile
                      ? 'bg-purple-600/20 text-purple-400 border-l-2 border-purple-500'
                      : 'text-zinc-400 hover:bg-zinc-900 border-l-2 border-transparent'
                  }`}
                >
                  <span className="text-zinc-600 w-4 text-center">
                    {getFileIcon(f.path)}
                  </span>
                  <span className="truncate flex-1">{f.path}</span>
                  <span className="text-zinc-700 flex-shrink-0">
                    {formatSize(f.size)}
                  </span>
                </button>
              ))}
            {files.filter((f) => !f.binary).length === 0 && (
              <div className="p-3 text-xs text-zinc-600">No source files</div>
            )}
          </div>

          {/* Code view */}
          <div className="flex-1 overflow-auto">
            {active ? (
              <div className="p-4">
                <div className="text-xs text-zinc-600 mb-2 font-mono">
                  {activeFile}
                </div>
                <pre className="text-sm font-mono leading-relaxed">
                  <code className={`language-${getLang(activeFile)}`}>
                    {active.content}
                  </code>
                </pre>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full text-zinc-600 text-sm">
                Select a file to view
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function getFileIcon(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase() || '';
  const icons: Record<string, string> = {
    html: '🌐', htm: '🌐',
    css: '🎨',
    js: '📜', jsx: '📜', ts: '📜', tsx: '📜',
    json: '📋',
    md: '📝',
    py: '🐍',
    svg: '🖼️',
    xml: '📋',
  };
  return icons[ext] || '📄';
}