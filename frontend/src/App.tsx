import { useEffect } from 'react';
import ModeSelector from './components/ModeSelector';
import ProjectList from './components/ProjectList';
import ChatPanel from './components/ChatPanel';
import AgentStatus from './components/AgentStatus';
import AppViewer from './components/AppViewer';
import RaceResults from './components/RaceResults';
import AuthPage from './components/AuthPage';
import { useAuthStore } from './store/authStore';
import { getMe } from './api/sse';

function App() {
  const { isAuthenticated, isLoading, token, setAuth, logout, setLoading } = useAuthStore();

  // Verify stored token on mount
  useEffect(() => {
    if (token) {
      getMe()
        .then((data) => setAuth(data.user, token))
        .catch(() => {
          // Token invalid or expired
          logout();
        });
    } else {
      setLoading(false);
    }
  }, []);

  // Show loading spinner while checking auth
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0f0f13]">
        <div className="animate-spin h-6 w-6 border-2 border-purple-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return <AuthPage />;
  }

  return (
    <div className="h-screen flex flex-col bg-[#0f0f13]">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-2.5 border-b border-zinc-800 bg-zinc-900/50 shrink-0">
        <div className="flex items-center gap-3">
          <h1 className="text-base font-bold text-white tracking-tight">
            <span className="text-purple-500">Atoms</span> MVP
          </h1>
          <span className="text-xs text-zinc-600 px-2 py-0.5 rounded-full bg-zinc-800">
            v0.1.0
          </span>
        </div>
        <div className="flex items-center gap-4">
          <ModeSelector />
          <button
            onClick={logout}
            className="text-xs text-zinc-500 hover:text-zinc-300"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Main content: three columns */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Project List */}
        <aside className="w-56 shrink-0 border-r border-zinc-800 bg-zinc-900/30 overflow-hidden">
          <ProjectList />
        </aside>

        {/* Center: Chat */}
        <main className="flex-1 flex flex-col min-w-0 border-r border-zinc-800">
          <AgentStatus />
          <ChatPanel />
        </main>

        {/* Right: App Viewer */}
        <aside className="flex-1 min-w-0 bg-zinc-950 relative">
          <AppViewer />
        </aside>
      </div>

      {/* Race Results Overlay */}
      <RaceResults />
    </div>
  );
}

export default App;