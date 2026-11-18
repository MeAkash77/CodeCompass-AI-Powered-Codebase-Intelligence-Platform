import api from "./api";
import { type ConversationResponse } from "../types";

export const getAllConversations = async (): Promise<ConversationResponse> => {
  const response = await api.get<ConversationResponse>(`/conversations`);
  return response.data;
}
