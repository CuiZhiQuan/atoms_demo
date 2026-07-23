import type { ChatMessage } from '../store/chatStore';

interface Props {
  message: ChatMessage;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  if (isSystem) {
    return (
      <div className="flex justify-center py-1">
        <span className="text-xs text-zinc-500 px-2 py-0.5 rounded-full bg-zinc-800/50">
          {message.content}
        </span>
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      <div
        className={`max-w-[85%] px-3.5 py-2.5 rounded-2xl text-sm leading-relaxed ${
          isUser
            ? 'bg-purple-600 text-white rounded-br-md'
            : 'bg-zinc-800 text-zinc-200 rounded-bl-md'
        }`}
      >
        {message.agentName && (
          <div className="text-xs text-purple-400 font-medium mb-1">
            {message.agentName}
          </div>
        )}
        <div className="whitespace-pre-wrap break-words">{message.content}</div>
      </div>
    </div>
  );
}