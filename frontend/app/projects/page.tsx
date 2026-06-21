"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ArxivTopBar } from "@/components/ArxivTopBar";
import { ProjectEditModal } from "@/components/ProjectEditModal";
import { ProjectSidebarRow } from "@/components/ProjectSidebarRow";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiJson, clearTokens, deleteProject, getAccessToken, updateProject } from "@/lib/api";
import { cn } from "@/lib/utils";
import { LogOut, Plus } from "lucide-react";

type Project = { id: string; name: string; created_at: string };

const EMOJIS = ["🌍", "🤖", "🧬", "⚛️", "📚", "🔬", "🧪", "📊", "🌿", "✨"];

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [selectedEmoji, setSelectedEmoji] = useState(0);
  const [userAv, setUserAv] = useState("·");

  const emojiOptions = useMemo(() => EMOJIS, []);

  const load = useCallback(async () => {
    if (!getAccessToken()) {
      router.replace("/login");
      return;
    }
    try {
      const data = await apiJson<Project[]>("/api/projects/");
      setProjects(data);
    } catch {
      clearTokens();
      router.replace("/login");
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    const t = getAccessToken();
    if (!t) return;
    try {
      const payload = JSON.parse(atob(t.split(".")[1])) as { email?: string; username?: string; sub?: string };
      const s = (payload.email || payload.username || payload.sub || "U") as string;
      const clean = s.replace(/[^a-zA-Z0-9]/g, "");
      setUserAv(clean.length >= 2 ? clean.slice(0, 2).toUpperCase() : s.slice(0, 2).toUpperCase());
    } catch {
      setUserAv("U");
    }
  }, []);

  async function createProject(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const p = await apiJson<Project>("/api/projects/", {
        method: "POST",
        json: { name: name.trim() },
      });
      setName("");
      setModalOpen(false);
      setProjects((prev) => [p, ...prev]);
      router.push(`/projects/${p.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create project");
    }
  }

  function logout() {
    clearTokens();
    router.push("/login");
  }

  function openEditProject(p: Project, e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    setEditingProject(p);
    setEditModalOpen(true);
  }

  async function saveProjectName(name: string) {
    if (!editingProject) return;
    const updated = await updateProject(editingProject.id, name);
    setProjects((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
  }

  async function removeProject() {
    if (!editingProject) return;
    await deleteProject(editingProject.id);
    setProjects((prev) => prev.filter((p) => p.id !== editingProject.id));
    setEditingProject(null);
  }

  if (loading) {
    return (
      <div className="arxiv-mock arxiv-app-shell">
        <ArxivTopBar userInitials={userAv} />
        <div className="mock-dash-main flex flex-1 items-center justify-center">
          <p className="font-mono text-xs text-muted-foreground">Loading…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="arxiv-mock arxiv-app-shell relative">
      <ArxivTopBar userInitials={userAv} />

      <div className="mock-dash flex min-h-0 flex-1">
        <aside className="mock-side">
          <div className="mock-side-lbl">Projects</div>
          <Button type="button" variant="ghost" className="mock-new-dash h-auto w-full justify-start px-3 py-2 font-normal" onClick={() => setModalOpen(true)}>
            <Plus className="size-3.5 text-primary" />
            New project
          </Button>
          {projects.map((p, i) => (
            <ProjectSidebarRow
              key={p.id}
              name={p.name}
              emoji={EMOJIS[i % EMOJIS.length]}
              href={`/projects/${p.id}`}
              onEdit={(e) => openEditProject(p, e)}
            />
          ))}
          <div className="mt-auto border-t p-3">
            <Button type="button" variant="ghost" size="sm" className="h-8 w-full justify-start font-mono text-xs text-primary" onClick={logout}>
              <LogOut className="size-3.5" />
              Log out
            </Button>
          </div>
        </aside>

        <div className="mock-dash-main">
          <div className="mock-glyph">∂</div>
          <h2 className="mock-dash-title">Select a project</h2>
          <p className="mock-dash-sub">
            {projects.length === 0
              ? "Create a new project to upload papers and start chatting with citations."
              : "Choose a project from the sidebar or create a new one."}
          </p>
          <Button type="button" variant="outline" size="sm" className="mt-4" onClick={() => setModalOpen(true)}>
            <Plus className="size-3.5" />
            New project
          </Button>
        </div>
      </div>

      <div className={cn("mock-overlay", modalOpen && "is-open")} role="dialog" aria-modal="true" aria-labelledby="new-proj-title">
        <Card className="mock-modal w-full max-w-md border shadow-lg">
          <CardHeader>
            <CardTitle id="new-proj-title" className="font-serif text-lg">
              New project
            </CardTitle>
            <CardDescription>Create a container for uploads, embeddings, and chat.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={createProject} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="proj-name">Project name</Label>
                <Input
                  id="proj-name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. CMIP6 literature review"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Icon</Label>
                <div className="mock-emoji-grid">
                  {emojiOptions.map((e, i) => (
                    <button
                      key={e}
                      type="button"
                      className={cn("mock-emoji-btn", i === selectedEmoji && "is-sel")}
                      onClick={() => setSelectedEmoji(i)}
                    >
                      {e}
                    </button>
                  ))}
                </div>
              </div>
              {error ? <p className="font-mono text-xs text-destructive">{error}</p> : null}
              <CardFooter className="flex justify-end gap-2 p-0 pt-2">
                <Button type="button" variant="outline" onClick={() => setModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit">Create project</Button>
              </CardFooter>
            </form>
          </CardContent>
        </Card>
      </div>

      <ProjectEditModal
        open={editModalOpen}
        title="Edit project"
        description="Rename or delete this project."
        initialName={editingProject?.name ?? ""}
        submitLabel="Save"
        onClose={() => {
          setEditModalOpen(false);
          setEditingProject(null);
        }}
        onSubmit={saveProjectName}
        onDelete={editingProject ? removeProject : undefined}
      />
    </div>
  );
}
