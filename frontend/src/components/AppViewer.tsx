import { useRef, useEffect, useState, useCallback } from 'react';
import { useChatStore } from '../store/chatStore';
import { deployProject } from '../api/sse';
import SourceViewer from './SourceViewer';

const RAW_BASE = import.meta.env.VITE_API_URL || '';

export default function AppViewer() {
  const { currentProjectId, viewerRefreshKey } = useChatStore();
  const [viewMode, setViewMode] = useState<'desktop' | 'mobile'>('desktop');
  const [showSource, setShowSource] = useState(false);
  const [deploying, setDeploying] = useState(false);
  const [deployUrl, setDeployUrl] = useState<string | null>(null);
  const [deployError, setDeployError] = useState<string | null>(null);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const refreshTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  const refreshIframe = useCallback(() => {
    // Debounce: refresh 1 second after last file change
    if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current);
    refreshTimerRef.current = setTimeout(() => {
      if (iframeRef.current) {
        iframeRef.current.src = iframeRef.current.src;
      }
    }, 1000);
  }, []);

  const handleDeploy = async () => {
    if (!currentProjectId || deploying) return;
    setDeploying(true);
    setDeployError(null);
    setDeployUrl(null);
    try {
      const result = await deployProject(currentProjectId);
      setDeployUrl(result.deployment.url);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Deploy failed';
      setDeployError(msg);
    } finally {
      setDeploying(false);
    }
  };

  useEffect(() => {
    if (viewerRefreshKey > 0) {
      refreshIframe();
    }
  }, [viewerRefreshKey, refreshIframe]);

  const previewUrl = currentProjectId
    ? `${RAW_BASE}/workspace/${currentProjectId}/index.html`
    : null;

  if (!currentProjectId) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-zinc-600">
        <div className="text-4xl mb-3">🖥️</div>
        <p className="text-sm">Select a project to preview</p>
        <p className="text-xs mt-1">Generated apps will appear here</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-zinc-800 bg-zinc-900/50">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green-500" />
          <span className="text-xs text-zinc-400">
            {showSource ? 'Source Code' : 'Preview'}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setShowSource(!showSource)}
            className={`px-2 py-0.5 rounded text-xs font-medium transition-colors ${
              showSource
                ? 'bg-amber-600/20 text-amber-400 border border-amber-500/30'
                : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800'
            }`}
          >
            {showSource ? '👁️ Preview' : '<> Source'}
          </button>
          {!showSource && (
            <>
              <button
                onClick={() => setViewMode('desktop')}
                className={`px-2 py-0.5 rounded text-xs ${
                  viewMode === 'desktop'
                    ? 'bg-purple-600 text-white'
                    : 'text-zinc-500 hover:text-zinc-300'
                }`}
              >
                Desktop
              </button>
              <button
                onClick={() => setViewMode('mobile')}
                className={`px-2 py-0.5 rounded text-xs ${
                  viewMode === 'mobile'
                    ? 'bg-purple-600 text-white'
                    : 'text-zinc-500 hover:text-zinc-300'
                }`}
              >
                Mobile
              </button>
              <button
                onClick={refreshIframe}
                className="px-2 py-0.5 rounded text-xs text-zinc-500 hover:text-zinc-300 ml-1"
                title="Refresh preview"
              >
                ↻
              </button>
            </>
          )}
          <button
            onClick={handleDeploy}
            disabled={deploying}
            className={`px-3 py-0.5 rounded text-xs font-medium ml-2 transition-colors ${
              deployUrl
                ? 'bg-emerald-600/20 text-emerald-400 border border-emerald-500/30'
                : deploying
                  ? 'bg-purple-600/50 text-white cursor-wait'
                  : 'bg-purple-600 hover:bg-purple-500 text-white'
            }`}
            title="Deploy to Vercel"
          >
            {deploying ? '⏳ Deploying...' : deployUrl ? '✅ Deployed' : '🚀 Deploy'}
          </button>
        </div>
      </div>

      {/* Content area */}
      <div className="flex-1 overflow-hidden">
        {showSource ? (
          <SourceViewer
            projectId={currentProjectId}
            onClose={() => setShowSource(false)}
          />
        ) : (
          <div className="flex-1 flex items-center justify-center bg-zinc-950 p-2 h-full">
            <div
              className={`overflow-hidden bg-white transition-all duration-300 rounded-lg shadow-2xl ${
                viewMode === 'mobile' ? 'w-[375px] max-w-full' : 'w-full'
              } ${viewMode === 'mobile' ? 'h-[667px] max-h-full' : 'h-full'}`}
            >
              {previewUrl && (
                <iframe
                  ref={iframeRef}
                  src={previewUrl}
                  className="w-full h-full border-0"
                  title="App Preview"
                  sandbox="allow-scripts allow-same-origin"
                />
              )}
            </div>
          </div>
        )}
      </div>

      {/* Deploy status */}
      {(deployUrl || deployError) && (
        <div
          className={`px-3 py-2 text-xs border-t ${
            deployUrl
              ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-400'
              : 'bg-red-950/30 border-red-500/30 text-red-400'
          }`}
        >
          {deployUrl ? (
            <div className="flex items-center gap-2">
              <span>✅ Deployed to</span>
              <a
                href={deployUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:text-emerald-300"
              >
                {deployUrl}
              </a>
              <button
                onClick={() => navigator.clipboard.writeText(deployUrl)}
                className="text-zinc-500 hover:text-zinc-300 ml-auto"
                title="Copy URL"
              >
                📋
              </button>
            </div>
          ) : (
            <span>❌ {deployError}</span>
          )}
        </div>
      )}
    </div>
  );
}