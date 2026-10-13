import { useCallback, useState } from "react";
import { ThemeProvider } from "next-themes";

import { ProfileMenu } from "@/components/profile-menu";
import { ThemeToggle } from "@/components/theme-toggle";
import { VoicePersona } from "@/components/voice-persona";
import type { VoiceTurn } from "@/lib/use-voice-loop";

export default function App() {
  const [turns, setTurns] = useState<VoiceTurn[]>([]);
  const handleTurn = useCallback((turn: VoiceTurn) => {
    setTurns((current) => [...current, turn]);
  }, []);

  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
      <div className="relative flex min-h-screen flex-col">
        <header className="relative z-10 grid grid-cols-[1fr_auto_1fr] items-center px-6 py-4">
          <div />
          <h1 className="font-brand text-center text-xl font-semibold tracking-tight">
            SystemOne Assistant
          </h1>
          <div className="flex justify-self-end gap-2">
            <ThemeToggle />
            <ProfileMenu />
          </div>
        </header>

        <aside className="absolute inset-y-20 left-6 hidden w-72 flex-col overflow-hidden rounded-2xl border bg-card/80 shadow-sm backdrop-blur md:flex">
          <div className="border-b px-4 py-3">
            <h2 className="text-sm font-semibold">Conversation</h2>
            <p className="text-xs text-muted-foreground">Your voice input and assistant replies</p>
          </div>
          <div className="flex-1 space-y-4 overflow-y-auto p-4">
            {turns.length === 0 ? (
              <p className="pt-4 text-center text-sm text-muted-foreground">
                Start speaking to see the conversation here.
              </p>
            ) : (
              turns.map((turn, index) => (
                <div className="space-y-3" key={`${turn.transcript}-${index}`}>
                  <div className="rounded-xl rounded-br-sm bg-muted px-3 py-2 text-sm">
                    <p className="mb-1 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                      You
                    </p>
                    <p>{turn.transcript}</p>
                  </div>
                  <div className="rounded-xl rounded-bl-sm border px-3 py-2 text-sm">
                    <p className="mb-1 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                      Assistant
                    </p>
                    <p>{turn.reply}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </aside>

        <main className="flex flex-1 items-center justify-center p-6">
          <VoicePersona onTurn={handleTurn} />
        </main>
      </div>
    </ThemeProvider>
  );
}
