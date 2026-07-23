import { useEffect, useState } from 'react';
import { useChatStore, type Project } from '../store/chatStore';
import { fetchProjects, createProject, deleteProject } from '../api/sse';

export default function ProjectList() {
  const { projects, setProjects, currentProjectId, setCurrentProject } = useChatStore();
  const [newName, setNewName] = useState('');

  useEffect(() => {
    fetchProjects().then(setProjects).catch(console.error);
  }, [setProjects]);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    try {
      const project = await createProject(newName.trim(), 'engineer');
      setProjects([project as Project, ...projects]);
      setCurrentProject(project.id);
      setNewName('');
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteProject(id);
      setProjects(projects.filter((p) => p.id !== id));
      if (currentProjectId === id) setCurrentProject(null);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 border-b border-zinc-800">
        <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-2">
          Projects
        </h2>
        <div className="flex gap-1.5">
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
            placeholder="New project..."
            className="flex-1 px-2.5 py-1.5 rounded-lg bg-zinc-800 border border-zinc-700 text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-purple-500"
          />
          <button
            onClick={handleCreate}
            disabled={!newName.trim()}
            className="px-2.5 py-1.5 rounded-lg bg-purple-600 text-white text-sm hover:bg-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            +
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {projects.length === 0 && (
          <p className="text-zinc-500 text-xs text-center py-8">No projects yet</p>
        )}
        {projects.map((project) => (
          <div
            key={project.id}
            onClick={() => setCurrentProject(project.id)}
            className={`px-4 py-2.5 cursor-pointer border-b border-zinc-800/50 transition-colors group ${
              currentProjectId === project.id
                ? 'bg-purple-600/10 border-l-2 border-l-purple-500'
                : 'hover:bg-zinc-800/50'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="min-w-0">
                <p className="text-sm text-zinc-200 truncate">{project.name}</p>
                <p className="text-xs text-zinc-500 mt-0.5">
                  {project.mode} · {new Date(project.updated_at).toLocaleDateString()}
                </p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDelete(project.id);
                }}
                className="opacity-0 group-hover:opacity-100 text-zinc-500 hover:text-red-400 text-xs px-1.5 py-0.5 rounded transition-all"
                title="Delete project"
              >
                ✕
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}