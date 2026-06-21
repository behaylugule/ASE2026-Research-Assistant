"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Pencil } from "lucide-react";

type Props = {
  name: string;
  emoji: string;
  href: string;
  active?: boolean;
  count?: string | number;
  onEdit: (e: React.MouseEvent) => void;
};

export function ProjectSidebarRow({ name, emoji, href, active, count, onEdit }: Props) {
  return (
    <div className={`mock-proj-row group ${active ? "is-active" : ""}`} style={{ paddingRight: 4 }}>
      <Link
        href={href}
        className="flex min-w-0 flex-1 items-center gap-2 no-underline"
        style={{ color: "inherit" }}
        aria-current={active ? "page" : undefined}
      >
        <span className="mock-proj-ico">{emoji}</span>
        <span className="mock-proj-name">{name}</span>
        {count !== undefined ? <span className="mock-proj-cnt">{count}</span> : null}
      </Link>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="size-7 shrink-0 opacity-40 hover:opacity-100 group-hover:opacity-70"
        aria-label={`Edit ${name}`}
        onClick={onEdit}
      >
        <Pencil className="size-3.5" />
      </Button>
    </div>
  );
}
