"use server";
import { cookies } from "next/headers";
import type { VisibilityType } from "@/lib/types";
import { getPythonAI } from "@/lib/ai/python";
import {
  deleteMessagesByChatIdAfterTimestamp,
  getMessageById,
  updateChatVisibilityById,
} from "@/lib/db/queries";
import { getTextFromMessage } from "@/lib/utils";

export async function saveChatModelAsCookie(model: string) {
  const cookieStore = await cookies();
  cookieStore.set("chat-model", model);
}

export async function generateTitleFromUserMessage({
  message,
}: {
  message: any;
}) {
  const text = getTextFromMessage(message).trim();
  try {
    const ai = getPythonAI();
    const result = await ai.generateTitle({
      text,
    });
    const title = String(result?.title || "").trim();
    if (title.length > 0) {
      return title.slice(0, 80);
    }
  } catch (_) {}
  if (!text) {
    return "New Chat";
  }
  const collapsed = text.replace(/\s+/g, " ");
  return collapsed.slice(0, 80);
}

export async function deleteTrailingMessages({ id }: { id: string }) {
  const messages = await getMessageById({ id });
  const message = messages?.[0];
  if (!message) {
    return;
  }
  await deleteMessagesByChatIdAfterTimestamp({
    chatId: message.chatId,
    timestamp: message.createdAt,
  });
}

export async function updateChatVisibility({
  chatId,
  visibility,
}: {
  chatId: string;
  visibility: VisibilityType;
}) {
  await updateChatVisibilityById({ chatId, visibility });
}
