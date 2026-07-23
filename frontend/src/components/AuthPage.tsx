import { useState } from 'react';
import { useAuthStore } from '../store/authStore';
import { login, register } from '../api/sse';

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { setAuth } = useAuthStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const fn = isLogin ? login : register;
      const data = await fn(username, password);
      setAuth(data.user, data.token);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0f0f13]">
      <div className="w-full max-w-sm px-6">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-white tracking-tight">
            <span className="text-purple-500">Atoms</span> MVP
          </h1>
          <p className="text-sm text-zinc-500 mt-1">
            Build apps with AI agents
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-zinc-400 mb-1">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter username"
              required
              minLength={3}
              className="w-full px-3 py-2 rounded-lg bg-zinc-800 border border-zinc-700 text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-purple-500"
            />
          </div>

          <div>
            <label className="block text-xs text-zinc-400 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              required
              minLength={6}
              className="w-full px-3 py-2 rounded-lg bg-zinc-800 border border-zinc-700 text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-purple-500"
            />
          </div>

          {error && (
            <div className="text-xs text-red-400 bg-red-900/20 px-3 py-2 rounded-lg">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 rounded-lg bg-purple-600 text-white text-sm font-medium hover:bg-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Loading...' : isLogin ? 'Log In' : 'Sign Up'}
          </button>
        </form>

        {/* Toggle */}
        <div className="text-center mt-4">
          <button
            onClick={() => { setIsLogin(!isLogin); setError(''); }}
            className="text-sm text-zinc-500 hover:text-purple-400"
          >
            {isLogin ? "Don't have an account? Sign up" : 'Already have an account? Log in'}
          </button>
        </div>
      </div>
    </div>
  );
}