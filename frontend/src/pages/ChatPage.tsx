import { useState, useRef, useEffect } from "react"
import { ask } from "../services/ask"
import { getAllConversations } from "../services/conversations"
import { type Conversation, createConversation } from "../types"
import { AskForm } from "../components/AskForm"
import { ConversationList } from "../components/ConversationList"
import { Header } from "../components/Header"
import { Toast } from "../components/Toast"
import "./ChatPage.css"

export const ChatPage = () => {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const chatEndRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [conversations])

  useEffect(() => {
    const fetchConversations = async () => {
      try {
        const res = await getAllConversations()
        if (res.success) {
          setConversations(res.data)
        }
      } catch (err: unknown) {
        console.error("Failed to load conversations:", err)
        setError("Failed to load conversations")
      }
    }

    fetchConversations()
  }, [])

  const handleAsk = async (prompt: string) => {
    setLoading(true)
    setError("")

    const userConversation: Conversation = createConversation("User", prompt)
    setConversations((prev) => [...prev, userConversation])
    try {
      const res = await ask(prompt)
      if (res.success) {
        setConversations(prev => [...prev, res.data])
      } else {
        console.error("Server response error")
        setError("Something went wrong. Please try again.")
      }
    } catch (err: unknown) {
      console.error("Calling server error:", err)
      setError("Something went wrong. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Header title="code-compass" />
      {error && (
        <Toast
          message={error}
          type="error"
          onClose={() => setError("")}
        />
      )}
      <div className="chat-page">
        <main className="chat-main">
          <ConversationList conversations={conversations} />
          <div ref={chatEndRef} />
        </main>

        <footer className="chat-footer">
          <AskForm onAsk={handleAsk} loading={loading} />
        </footer>
      </div>
    </>
  )
}
