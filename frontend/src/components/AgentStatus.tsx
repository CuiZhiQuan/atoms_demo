import { useChatStore } from '../store/chatStore';

export default function AgentStatus() {
  const { activeAgent, agentThoughts, isRunning } = useChatStore();

  if (!isRunning && !activeAgent) return null;

  return (
    <div className="px-3 py-2 bg-zinc-800/50 border-b border-zinc-800">
      <div className="flex items-center gap-2">
        {isRunning && (
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-purple-500 animate-pulse" />
            <span className="text-xs text-purple-400 font-medium">
              {activeAgent || 'Thinking...'}
            </span>
          </span>
        )}
        {!isRunning && activeAgent && (
          <span className="text-xs text-zinc-500">Idle</span>
        )}
      </div>
      {agentThoughts && (
        <p className="text-xs text-zinc-400 mt-1 line-clamp-2 italic">
          {agentThoughts.slice(-200)}
        </p>
      )}
    </div>
  );
}