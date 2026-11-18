export interface AskResponseData {
  response: string
  refined_query: string
  sources: string[]
  context_used: unknown[]
}

export interface AskResponse {
  success: boolean
  data: Conversation
  error?: string
}

export interface Citation {
  title: string
  url: string
}

export interface Conversation {
  role: string
  content: string
  citations?: Citation[]
  created_at?: string
}

export const createConversation = (role: string, content: string): Conversation => ({
  role,
  content
});

export interface ConversationResponse {
  success: boolean
  data: Conversation[]
  error?: string
}
