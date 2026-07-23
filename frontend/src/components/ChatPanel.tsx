import { useRef, useEffect, useState } from 'react';
import { useChatStore } from '../store/chatStore';
import MessageBubble from './MessageBubble';
import { runStream } from '../api/sse';
import type { SSEEvent } from '../api/sse';

export default function ChatPanel() {
  const {
    messages, addMessage, mode, currentProjectId,
    isRunning, setRunning, setActiveAgent, appendThought, clearThoughts,
    triggerViewerRefresh, setRaceResults, reset, refreshProjects, setCurrentProject,
  } = useChatStore();

  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleEvent = (event: SSEEvent) => {
    const { type, payload } = event;

    switch (type) {
      case 'session_start':
        addMessage({ role: 'system', content: `Session started · Mode: ${payload.mode}` });
        setCurrentProject(payload.project_id as string);
        refreshProjects();
        break;

      case 'session_end':
        addMessage({ role: 'system', content: 'Session ended' });
        break;

      case 'agent_start':
        setActiveAgent(payload.agent as string);
        clearThoughts();
        addMessage({
          role: 'system',
          content: `${payload.agent} is working...`,
        });
        break;

      case 'agent_thought':
        appendThought(payload.thought as string);
        break;

      case 'agent_end':
        setActiveAgent(null);
        clearThoughts();
        if (payload.result) {
          addMessage({
            role: 'agent',
            agentName: payload.agent as string,
            content: payload.result as string,
          });
        }
        break;

      case 'tool_call':
        addMessage({
          role: 'system',
          content: `🔧 ${payload.tool}: ${JSON.stringify(payload.arguments)}`,
        });
        break;

      case 'tool_result':
        // Tool results are usually verbose, skip or show compact
        break;

      case 'file_created':
        addMessage({
          role: 'system',
          content: `📄 Created: ${payload.path}`,
        });
        triggerViewerRefresh();
        break;

      case 'file_updated':
        triggerViewerRefresh();
        break;

      case 'message':
        addMessage({
          role: 'system',
          content: payload.text as string,
        });
        break;

      case 'race_complete': {
        const results = payload.results as Array<{
          lane_idx: number; model: string; project_id: string; summary: string;
        }>;
        setRaceResults(results);
        addMessage({
          role: 'system',
          content: `🏁 Race complete! ${results.length} results available. Please select the best one.`,
        });
        break;
      }

      case 'error':
        addMessage({
          role: 'system',
          content: `❌ Error: ${payload.message}`,
        });
        break;

      case 'done':
        setRunning(false);
        setActiveAgent(null);
        clearThoughts();
        triggerViewerRefresh();
        refreshProjects();
        break;
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isRunning) return;

    const prompt = input.trim();
    setInput('');
    addMessage({ role: 'user', content: prompt });
    setRunning(true);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      await runStream(prompt, mode, currentProjectId, handleEvent, controller.signal);
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        addMessage({
          role: 'system',
          content: `❌ Connection error: ${(err as Error).message}`,
        });
      }
    } finally {
      setRunning(false);
      setActiveAgent(null);
      clearThoughts();
    }
  };

  const handleStop = () => {
    abortRef.current?.abort();
    reset();
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-3">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-zinc-500">
            <div className="text-4xl mb-3">🚀</div>
            <p className="text-sm font-medium">Atoms MVP</p>
            <p className="text-xs mt-1">Describe what you want to build</p>
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-4 py-3 border-t border-zinc-800">
        <div className="flex gap-2 items-stretch">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Describe the app you want to build..."
            rows={2}
            disabled={isRunning}
            className="flex-1 px-3 py-2 rounded-xl bg-zinc-800 border border-zinc-700 text-sm text-zinc-200 placeholder-zinc-500 resize-none focus:outline-none focus:border-purple-500 disabled:opacity-50"
          />
          {isRunning ? (
            <button
              onClick={handleStop}
              className="px-8 rounded-xl bg-red-600 text-white text-sm font-medium hover:bg-red-500"
            >
              ⏹
            </button>
          ) : (
            <button
              onClick={handleSend}
              disabled={!input.trim()}
              className="px-8 rounded-xl bg-purple-600 text-white text-sm font-medium hover:bg-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              ▶
            </button>
          )}
        </div>
      </div>
    </div>
  );
}