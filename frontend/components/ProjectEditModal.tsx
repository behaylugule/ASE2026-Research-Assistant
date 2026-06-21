"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { Trash2 } from "lucide-react";

type Props = {
  open: boolean;
  title: string;
  description?: string;
  initialName?: string;
  submitLabel?: string;
  onClose: () => void;
  onSubmit: (name: string) => Promise<void>;
  onDelete?: () => Promise<void>;
};

export function ProjectEditModal({
  open,
  title,
  description,
  initialName = "",
  submitLabel = "Save",
  onClose,
  onSubmit,
  onDelete,
}: Props) {
  const [name, setName] = useState(initialName);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (open) {
      setName(initialName);
      setError(null);
    }
  }, [open, initialName]);

  useEffect(() => {
    if (!open) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && !saving && !deleting) onClose();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onClose, saving, deleting]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) {
      setError("Project name is required.");
      return;
    }
    if (trimmed === initialName.trim()) {
      onClose();
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await onSubmit(trimmed);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save project");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!onDelete) return;
    const confirmed = window.confirm(
      `Delete project "${initialName}"?\n\nAll documents, chat history, and embeddings in this project will be permanently removed.`,
    );
    if (!confirmed) return;
    setDeleting(true);
    setError(null);
    try {
      await onDelete();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete project");
    } finally {
      setDeleting(false);
    }
  }

  const busy = saving || deleting;

  return (
    <div
      className={cn("mock-overlay", open && "is-open")}
      role="dialog"
      aria-modal="true"
      aria-labelledby="project-edit-modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget && !busy) onClose();
      }}
    >
      <Card className="mock-modal w-full max-w-md border shadow-lg">
        <CardHeader>
          <CardTitle id="project-edit-modal-title" className="font-serif text-lg">
            {title}
          </CardTitle>
          {description ? <CardDescription>{description}</CardDescription> : null}
        </CardHeader>
        <CardContent className="space-y-4">
          <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="project-edit-name">Project name</Label>
              <Input
                id="project-edit-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. CMIP6 literature review"
                required
                maxLength={255}
                autoFocus
                disabled={busy}
              />
            </div>
            {error ? <p className="font-mono text-xs text-destructive">{error}</p> : null}
            <CardFooter className="flex justify-end gap-2 p-0 pt-2">
              <Button type="button" variant="outline" onClick={onClose} disabled={busy}>
                Cancel
              </Button>
              <Button type="submit" disabled={busy}>
                {saving ? "Saving…" : submitLabel}
              </Button>
            </CardFooter>
          </form>

          {onDelete ? (
            <>
              <Separator />
              <div className="space-y-2">
                <p className="text-xs text-muted-foreground">Permanently remove this project and all its documents.</p>
                <Button
                  type="button"
                  variant="destructive"
                  size="sm"
                  disabled={busy}
                  onClick={() => void handleDelete()}
                >
                  <Trash2 className="size-3.5" />
                  {deleting ? "Deleting…" : "Delete project"}
                </Button>
              </div>
            </>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
