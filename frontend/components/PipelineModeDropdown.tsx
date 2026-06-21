"use client";

import { BookOpen, Check, ChevronDown, FileText, Gauge, HelpCircle, Layers } from "lucide-react";
import type { ChatMode, PipelineMode } from "@/lib/chat-stream";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

const PIPELINE_OPTIONS: {
  id: PipelineMode;
  label: string;
  title: string;
  icon: React.ComponentType<{ className?: string }>;
}[] = [
  { id: "qa", label: "Q&A", title: "Grounded Q&A with citations", icon: HelpCircle },
  { id: "summarize", label: "Summarize", title: "Full document map-reduce summary", icon: FileText },
  { id: "literature_search", label: "Literature", title: "Explore themes across papers", icon: BookOpen },
  { id: "synthesis", label: "Synthesis", title: "Multi-paper literature review", icon: Layers },
];

const CHAT_MODE_OPTIONS: { id: ChatMode; label: string; title: string }[] = [
  { id: "fast", label: "Fast", title: "Fewer chunks · lower latency" },
  { id: "deep", label: "Deep", title: "More context · thorough answers" },
];

type Props = {
  pipelineMode: PipelineMode;
  chatMode: ChatMode;
  topKLabel: string;
  hint?: string;
  disabled?: boolean;
  className?: string;
  onPipelineChange: (mode: PipelineMode) => void;
  onChatModeChange: (mode: ChatMode) => void;
};

export function PipelineModeDropdown({
  pipelineMode,
  chatMode,
  topKLabel,
  hint,
  disabled,
  className,
  onPipelineChange,
  onChatModeChange,
}: Props) {
  const pipeline = PIPELINE_OPTIONS.find((o) => o.id === pipelineMode) ?? PIPELINE_OPTIONS[0];
  const PipelineIcon = pipeline.icon;
  const modeLabel = chatMode === "fast" ? "Fast" : "Deep";

  return (
    <div className={cn("flex shrink-0 items-center gap-1.5", className)}>
      <DropdownMenu>
        <Tooltip>
          <TooltipTrigger asChild>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" disabled={disabled} className="h-9 gap-1.5 font-normal shadow-xs">
                <PipelineIcon className="size-3.5 text-muted-foreground" />
                <span className="hidden sm:inline">{pipeline.label}</span>
                <ChevronDown className="size-3.5 text-muted-foreground opacity-70" />
              </Button>
            </DropdownMenuTrigger>
          </TooltipTrigger>
          {hint ? (
            <TooltipContent side="top" className="max-w-xs text-xs">
              {hint}
            </TooltipContent>
          ) : null}
        </Tooltip>
        <DropdownMenuContent align="start" side="top" className="min-w-[160px]">
          <DropdownMenuLabel className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">
            Pipeline
          </DropdownMenuLabel>
          {PIPELINE_OPTIONS.map((opt) => {
            const Icon = opt.icon;
            const selected = pipelineMode === opt.id;
            return (
              <DropdownMenuItem
                key={opt.id}
                title={opt.title}
                onClick={() => onPipelineChange(opt.id)}
                className={cn("gap-2", selected && "bg-accent text-accent-foreground")}
              >
                <Icon className="size-3.5" />
                <span className="flex-1">{opt.label}</span>
                {selected ? <Check className="size-3.5" /> : null}
              </DropdownMenuItem>
            );
          })}
        </DropdownMenuContent>
      </DropdownMenu>

      {pipelineMode !== "summarize" ? (
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" disabled={disabled} className="h-9 gap-1.5 font-normal shadow-xs">
            <Gauge className="size-3.5 text-muted-foreground" />
            <span className="hidden sm:inline">{modeLabel}</span>
            <ChevronDown className="size-3.5 text-muted-foreground opacity-70" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" side="top" className="min-w-[120px]">
          <DropdownMenuLabel className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">
            Depth
          </DropdownMenuLabel>
          {CHAT_MODE_OPTIONS.map((opt) => {
            const selected = chatMode === opt.id;
            return (
              <DropdownMenuItem
                key={opt.id}
                title={opt.title}
                onClick={() => onChatModeChange(opt.id)}
                className={cn(selected && "bg-accent text-accent-foreground")}
              >
                <span className="flex-1">{opt.label}</span>
                {selected ? <Check className="size-3.5" /> : null}
              </DropdownMenuItem>
            );
          })}
        </DropdownMenuContent>
      </DropdownMenu>
      ) : (
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge variant="secondary" className="h-9 px-2 font-mono text-[10px] font-normal">
            {topKLabel}
          </Badge>
        </TooltipTrigger>
        <TooltipContent side="top" className="text-xs">
          Full document — all chunks
        </TooltipContent>
      </Tooltip>
      )}

      {pipelineMode !== "summarize" ? (
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge variant="secondary" className="hidden h-9 px-2 font-mono text-[10px] font-normal md:inline-flex">
            {topKLabel}
          </Badge>
        </TooltipTrigger>
        <TooltipContent side="top" className="text-xs">
          Chunks retrieved per query
        </TooltipContent>
      </Tooltip>
      ) : null}
    </div>
  );
}
