import { useChatStore } from '../store/chatStore';

export default function ModeSelector() {
  const { mode, setMode, isRunning } = useChatStore();

  const modes = [
    { value: 'engineer' as const, label: '⚡ Engineer', desc: 'Single agent, fast' },
    { value: 'team' as const, label: '🤝 Team', desc: '4-agent collaboration' },
    { value: 'race' as const, label: '🏁 Race', desc: '3 models compete' },
  ];

  return (
    <div className="flex gap-1.5">
      {modes.map((m) => (
        <button
          key={m.value}
          onClick={() => setMode(m.value)}
          disabled={isRunning}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 ${
            mode === m.value
              ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/20'
              : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
          title={m.desc}
        >
          {m.label}
        </button>
      ))}
    </div>
  );
}