import { differenceInSeconds } from "date-fns";
import { auth } from "@/app/(auth)/auth";
import {
  getChatById,
  getMessagesByChatId,
  getStreamIdsByChatId,
} from "@/lib/db/queries";
import type { Chat } from "@/lib/db/schema";
import { ChatSDKError } from "@/lib/errors";
import type { ChatMessage } from "@/lib/types";
import { getStreamContext } from "../../route";

export async function GET(
  _: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id: chatId } = await params;

  const streamContext = getStreamContext();
  const resumeRequestedAt = new Date();

  if (!streamContext) {
    return new Response(null, { status: 204 });
  }

  if (!chatId) {
    return new ChatSDKError("bad_request:api").toResponse();
  }

  const session = await auth();

  if (!session?.user) {
    return new ChatSDKError("unauthorized:chat").toResponse();
  }

  let chat: Chat | null;

  try {
    chat = await getChatById({ id: chatId });
  } catch {
    return new ChatSDKError("not_found:chat").toResponse();
  }

  if (!chat) {
    return new ChatSDKError("not_found:chat").toResponse();
  }

  if (chat.visibility === "private" && chat.userId !== session.user.id) {
    return new ChatSDKError("forbidden:chat").toResponse();
  }

  const streamIds = await getStreamIdsByChatId({ chatId });

  if (!streamIds.length) {
    return new ChatSDKError("not_found:stream").toResponse();
  }

  const recentStreamId = streamIds.at(-1);

  if (!recentStreamId) {
    return new ChatSDKError("not_found:stream").toResponse();
  }

  // Resumable streaming is disabled; provide lightweight restoration within 15s
  const encoder = new TextEncoder();
  const messages = await getMessagesByChatId({ id: chatId });
  const mostRecentMessage = messages.at(-1);

  /*
   * For when the generation is streaming during SSR
   * but the resumable stream has concluded at this point.
   */
  if (!mostRecentMessage || mostRecentMessage.role !== "assistant") {
    return new Response(null, { status: 204 });
  }
  const messageCreatedAt = new Date(mostRecentMessage.createdAt);
  if (differenceInSeconds(resumeRequestedAt, messageCreatedAt) > 15) {
    return new Response(null, { status: 204 });
  }
  const sse = new ReadableStream({
    start(controller) {
      const payload = {
        type: "message",
        message: {
          id: mostRecentMessage.id,
          role: "assistant",
          parts: mostRecentMessage.parts,
        } as ChatMessage,
        transient: true,
      };
      controller.enqueue(encoder.encode(`data: ${JSON.stringify(payload)}\n\n`));
      controller.close();
    },
  });
  return new Response(sse, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
