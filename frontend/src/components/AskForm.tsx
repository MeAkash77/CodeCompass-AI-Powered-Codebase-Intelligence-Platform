import { useState, useRef } from "react"
import "./AskForm.css"

interface Props {
  onAsk: (prompt: string) => Promise<void>
  loading: boolean
}

export const AskForm = ({ onAsk, loading }: Props) => {
  const [prompt, setPrompt] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)

  const handleSubmit = async () => {
    if (!prompt.trim()) return
    await onAsk(prompt)
    setPrompt("")
  }

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setPrompt(e.target.value)

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height = textareaRef.current.scrollHeight + "px"
    }
  };

  return (
    <div className="ask-form">
      <textarea
        ref={textareaRef}
        className="ask-input"
        rows={1}
        placeholder="Ask a question..."
        value={prompt}
        onChange={handleChange}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault()
            handleSubmit()
          }
        }}
      />
      <button 
        type="button"
        className="ask-button"
        onClick={handleSubmit} 
        disabled={loading}>
        {loading ? "Thinking..." : "Send"}
      </button>
    </div>
  )
}
