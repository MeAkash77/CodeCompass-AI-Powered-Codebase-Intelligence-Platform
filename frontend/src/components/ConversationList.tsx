import { type Conversation } from "../types"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import "./ConversationList.css"
import { CodeBlock } from "./CodeBlock"

interface Props {
  conversations: Conversation[]
}

export const ConversationList = ({ conversations }: Props) => {
  return (
    <div className="conversation-list">
      {conversations.length === 0 && <p className="no-data">Navigate your programming resources!</p>}

      {conversations.map((conv, idx) => (
        <div
          key={idx}
          className={`message-bubble ${conv.role === "User" ? "message-user" : "message-assistant"
            }`}
        >
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              pre: ({ node }) => {
                // eslint-disable-next-line @typescript-eslint/ban-ts-comment
                // @ts-expect-error
                const text = node.children[0]?.children[0]?.value ?? "";
                return <CodeBlock code={text} />;
              }
            }}>
            {conv.content}
          </ReactMarkdown>
        </div>
      ))}
    </div>
  )
}
