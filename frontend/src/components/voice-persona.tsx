"use client";

import {
  BrainIcon,
  CircleIcon,
  EyeClosedIcon,
  MegaphoneIcon,
  MicIcon,
  SquareIcon,
  type LucideIcon,
} from "lucide-react";

import type { PersonaState } from "@/components/ai-elements/persona";
import { Persona } from "@/components/ai-elements/persona";
import { Button } from "@/components/ui/button";
import { ButtonGroup } from "@/components/ui/button-group";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { personaStateFor, type VoiceTurn, useVoiceLoop } from "@/lib/voice";

const states: { state: PersonaState; icon: LucideIcon; label: string }[] = [
  { icon: CircleIcon, label: "Idle", state: "idle" },
  { icon: MicIcon, label: "Listening", state: "listening" },
  { icon: BrainIcon, label: "Thinking", state: "thinking" },
  { icon: MegaphoneIcon, label: "Speaking", state: "speaking" },
  { icon: EyeClosedIcon, label: "Asleep", state: "asleep" },
];

export function VoicePersona({ onTurn }: { onTurn?: (turn: VoiceTurn) => void }) {
  const { status, active, error, start, stop } = useVoiceLoop(onTurn);
  const personaState = personaStateFor(status);
  const busyLabel =
    status === "transcribing" ? "Thinking…" : status === "speaking" ? "Speaking…" : "Listening…";

  return (
    <div className="flex flex-col items-center justify-center gap-6">
      <Persona className="size-64" state={personaState} variant="mana" />

      {/* Continuous listening: Start opens the session (keeps listening on silence gaps,
          auto-processes each utterance). Stop cancels everything and ends the session. */}
      {!active ? (
        <Button
          size="lg"
          aria-label="Start listening"
          onClick={start}
          disabled={status === "transcribing" || status === "speaking"}
        >
          <MicIcon />
          Start
        </Button>
      ) : (
        <div className="flex flex-col items-center gap-2">
          <Button size="lg" variant="destructive" aria-label="Stop listening" onClick={stop}>
            <SquareIcon className="fill-current" />
            Stop
          </Button>
          <span className="text-xs text-muted-foreground" aria-live="polite">
            {busyLabel}
          </span>
        </div>
      )}

      {error && <p className="text-sm text-destructive">{error}</p>}

      <ButtonGroup orientation="horizontal">
        {states.map((option) => (
          <Tooltip key={option.state}>
            <TooltipTrigger
              render={
                <Button
                  size="icon-sm"
                  variant={personaState === option.state ? "default" : "outline"}
                  aria-label={option.label}
                  disabled
                />
              }
            >
              <option.icon className="size-4" />
            </TooltipTrigger>
            <TooltipContent>{option.label}</TooltipContent>
          </Tooltip>
        ))}
      </ButtonGroup>
    </div>
  );
}
