import { useChatStore } from '../store/chatStore';

export default function RaceResults() {
  const { raceResults, raceSelected, setRaceSelected, setCurrentProject, reset } = useChatStore();

  if (!raceResults || raceResults.length === 0) return null;

  const handleSelect = async (laneIdx: number) => {
    // Race ID is embedded in the session; we just need to select
    // For simplicity, we directly set the selected project
    const selected = raceResults.find((r) => r.lane_idx === laneIdx);
    if (selected) {
      setCurrentProject(selected.project_id);
      setRaceSelected(true);
      reset();
    }
  };

  if (raceSelected) return null;

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-zinc-900 border border-zinc-700 rounded-2xl p-6 max-w-lg w-full mx-4 shadow-2xl">
        <h3 className="text-lg font-semibold text-white mb-2">🏁 Race Results</h3>
        <p className="text-sm text-zinc-400 mb-4">
          Select the best result to continue editing
        </p>

        <div className="space-y-3">
          {raceResults.map((result) => (
            <button
              key={result.lane_idx}
              onClick={() => handleSelect(result.lane_idx)}
              className="w-full text-left p-4 rounded-xl bg-zinc-800 border border-zinc-700 hover:border-purple-500 transition-all group"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-white">
                  Lane {result.lane_idx + 1}
                </span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-purple-600/20 text-purple-400">
                  {result.model}
                </span>
              </div>
              <p className="text-xs text-zinc-400 line-clamp-2">
                {result.summary || 'No summary available'}
              </p>
              <div className="mt-2 text-xs text-purple-400 opacity-0 group-hover:opacity-100 transition-opacity">
                Select this result →
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}