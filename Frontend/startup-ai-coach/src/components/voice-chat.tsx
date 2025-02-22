import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Mic, MicOff, Send } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

// Declare SpeechRecognition interface
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

export function VoiceChat() {
  const [isListening, setIsListening] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  useEffect(() => {
    wsRef.current = new WebSocket('ws://localhost:8000/ws/voice')
    
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data)
      addMessage('assistant', data.response_text)
      setIsLoading(false)
    }

    return () => wsRef.current?.close()
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  const addMessage = (role: 'user' | 'assistant', content: string) => {
    setMessages(prev => [...prev, { role, content, timestamp: new Date() }])
  }

  const handleSend = () => {
    if (!input.trim()) return
    
    addMessage('user', input)
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ message: input }))
      setIsLoading(true)
    }
    setInput('')
  }

  const toggleListening = () => {
    if (!isListening) {
      const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)()
      recognitionRef.current = recognition;
      recognition.continuous = true
      recognition.interimResults = true
      
      recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map(result => result[0])
          .map(result => result.transcript)
          .join('')
        
        setInput(transcript)
      }
      
      recognition.start()
    } else {
      recognitionRef.current?.stop()
    }
    
    setIsListening(!isListening)
  }

  return (
    <Card className="h-[calc(100vh-8rem)]">
      <CardHeader>
        <CardTitle>Voice Chat</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col h-full">
        <div className="flex-1 overflow-y-auto space-y-4 mb-4">
          <AnimatePresence>
            {messages.map((message, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted'
                  }`}
                >
                  <p>{message.content}</p>
                  <span className="text-xs opacity-70">
                    {message.timestamp.toLocaleTimeString()}
                  </span>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>
        
        <div className="flex gap-2">
          <Button
            variant={isListening ? "destructive" : "default"}
            size="icon"
            onClick={toggleListening}
          >
            {isListening ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
          </Button>
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="resize-none"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSend()
              }
            }}
          />
          <Button onClick={handleSend} disabled={!input.trim() || isLoading}>
            <Send className="h-5 w-5" />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
