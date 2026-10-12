import { ProfileMenu } from "@/components/profile-menu";
import { ThemeToggle } from "@/components/theme-toggle";
import { VoicePersona } from "@/components/voice-persona";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="grid grid-cols-3 items-center px-6 py-4">
        <div className="justify-self-start">
          <ThemeToggle />
        </div>
        <h1 className="font-brand text-center text-xl font-semibold tracking-tight">
          SystemOne Assistant
        </h1>
        <div className="justify-self-end">
          <ProfileMenu />
        </div>
      </header>

      <main className="flex flex-1 items-center justify-center p-6">
        <VoicePersona />
      </main>
    </div>
  );
}
