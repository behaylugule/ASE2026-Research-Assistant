"use client";

import Link from "next/link";
import { Moon, Sun } from "lucide-react";
import { useArxivTheme } from "@/components/ThemeProvider";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

type ArxivTopBarProps = {
  userInitials?: string;
  logoHref?: string;
};

export function ArxivTopBar({ userInitials = "—", logoHref = "/projects" }: ArxivTopBarProps) {
  const { theme, toggleTheme } = useArxivTheme();

  return (
    <header className="mock-topbar">
      <Link href={logoHref} className="mock-logo transition-opacity hover:opacity-80" style={{ textDecoration: "none", color: "inherit" }}>
        <span className="mock-dot" aria-hidden />
        Arxiv
      </Link>
      <Badge variant="outline" className="ml-auto font-mono text-[10px] font-normal">
        RAG · pgvector
      </Badge>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            type="button"
            variant="outline"
            size="icon-sm"
            onClick={toggleTheme}
            aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
          >
            {theme === "dark" ? <Sun className="size-3.5" /> : <Moon className="size-3.5" />}
          </Button>
        </TooltipTrigger>
        <TooltipContent>{theme === "dark" ? "Light theme" : "Dark theme"}</TooltipContent>
      </Tooltip>
      <Avatar className="size-7 border">
        <AvatarFallback className="bg-primary text-[10px] font-medium text-primary-foreground">{userInitials}</AvatarFallback>
      </Avatar>
    </header>
  );
}
