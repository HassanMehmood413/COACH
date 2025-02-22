import { VoiceChat } from "../components/voice-chat"
import { Analytics } from "../components/analytics"

export default function Home() {
  return (
    <div className="grid gap-6 md:grid-cols-2">
      <VoiceChat />
      <Analytics />
    </div>
  )
}

