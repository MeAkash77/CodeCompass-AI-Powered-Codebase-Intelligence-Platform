import api from "./api";
import { type AskResponse } from "../types"

export const ask = async (prompt: string): Promise<AskResponse> => {
  const payload = { prompt, max_tokens: 8192 }
  const response = await api.post<AskResponse>(`/ask`, payload)
  return response.data
}
