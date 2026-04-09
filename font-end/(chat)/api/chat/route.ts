import { geolocation } from "@vercel/functions";
import { after } from "next/server";
import { auth, type UserType } from "@/app/(auth)/auth";
import { entitlementsByUserType } from "@/lib/ai/entitlements";
import type { RequestHints } from "@/lib/ai/prompts";
import { getPythonAI } from "@/lib/ai/python";
import {
  createStreamId,
  deleteChatById,
  getChatById,
  getMessageCountByUserId,
  getMessagesByChatId,
  ensureUserExists,
  saveChat,
  saveMessages,
} from "@/lib/db/queries";
import type { DBMessage } from "@/lib/db/schema";
import { ChatSDKError } from "@/lib/errors";
import type { ChatMessage, VisibilityType } from "@/lib/types";
import { convertToUIMessages, generateUUID } from "@/lib/utils";
import { generateTitleFromUserMessage } from "../../actions";
import { type PostRequestBody, postRequestBodySchema } from "./schema";

export const maxDuration = 60;

export function getStreamContext() {
  return null;
}

export async function POST(request: Request) {
  let requestBody: PostRequestBody;

  try {
    const json = await request.json();
    requestBody = postRequestBodySchema.parse(json);
  } catch (_) {
    return new ChatSDKError("bad_request:api").toResponse();
  }

  try {
    if ("resume" in requestBody && requestBody.resume === true) {
      const sse = new ReadableStream({
        start(controller) {
          controller.close();
        },
      });
      return new Response(sse, {
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          Connection: "keep-alive",
        },
      });
    }

    const { id, message, selectedVisibilityType }: {
      id: string;
      message: ChatMessage;
      selectedVisibilityType: VisibilityType;
    } = requestBody as any;

    const session = await auth();

    if (!session?.user) {
      return new ChatSDKError("unauthorized:chat").toResponse();
    }

    const userType: UserType = session.user.type;

    const messageCount = await getMessageCountByUserId({
      id: session.user.id,
      differenceInHours: 24,
    });

    if (messageCount > entitlementsByUserType[userType].maxMessagesPerDay) {
      return new ChatSDKError("rate_limit:chat").toResponse();
    }

    await ensureUserExists({
      id: session.user.id,
      email: (session.user as any).email ?? null,
    });

    const chat = await getChatById({ id });
    let messagesFromDb: DBMessage[] = [];

    let createdTitle: string | null = null;
    if (chat) {
      if (chat.userId !== session.user.id) {
        return new ChatSDKError("forbidden:chat").toResponse();
      }
      // Only fetch messages if chat already exists
      messagesFromDb = await getMessagesByChatId({ id });
    } else {
      const title = await generateTitleFromUserMessage({
        message,
      });

      await saveChat({
        id,
        userId: session.user.id,
        title,
        visibility: selectedVisibilityType,
      });
      createdTitle = title;
      // New chat - no need to fetch messages, it's empty
    }

    const messageId = message.id ?? generateUUID();
    const uiMessages = [
      ...convertToUIMessages(messagesFromDb),
      { ...message, id: messageId },
    ];

    const { longitude, latitude, city, country } = geolocation(request);

    const requestHints: RequestHints = {
      longitude,
      latitude,
      city,
      country,
    };

    await saveMessages({
      messages: [
        {
          chatId: id,
          id: messageId,
          role: "user",
          userId: session.user.id,
          parts: message.parts,
          attachments: [],
          createdAt: new Date(),
        },
      ],
    });

    const streamId = generateUUID();
    await createStreamId({ streamId, chatId: id });

    const ai = getPythonAI();
    const assistantMessageId = generateUUID();
    let assistantText = "";
    const sse = new ReadableStream({
      async start(controller) {
        const encoder = new TextEncoder();
        try {
          if (createdTitle) {
            const initLine = `data: ${JSON.stringify({
              type: "chat-created",
              data: { id, title: createdTitle, visibility: selectedVisibilityType },
            })}\n\n`;
            controller.enqueue(encoder.encode(initLine));
          }
          for await (const chunk of ai.streamChat({
            id: streamId,
            messages: uiMessages,
            hints: requestHints,
          })) {
            if (chunk.type === "text-delta") {
              assistantText += chunk.text;
              const line = `data: ${JSON.stringify({
                type: "text-delta",
                data: chunk.text,
              })}\n\n`;
              controller.enqueue(encoder.encode(line));
            } else if (chunk.type === "finish") {
              controller.close();
            }
          }
        } catch (err) {
          // Fallback: emit a friendly assistant message on error/timeout
          if (!assistantText) {
            assistantText =
              "Xin lỗi, hệ thống AI đang tạm thời không phản hồi. Vui lòng thử lại sau.";
            try {
              const line = `data: ${JSON.stringify({
                type: "text-delta",
                data: assistantText,
              })}\n\n`;
              controller.enqueue(encoder.encode(line));
            } catch (_) {}
          }
          try {
            const line = `data: ${JSON.stringify({
              type: "finish",
            })}\n\n`;
            controller.enqueue(encoder.encode(line));
          } catch (_) {}
          controller.close();
        }
      },
    });

    after(async () => {
      if (assistantText) {
        try {
          await saveMessages({
            messages: [
              {
                chatId: id,
                id: assistantMessageId,
                role: "assistant",
                // @ts-ignore
                userId: null,
                parts: [{ type: "text", text: assistantText }],
                attachments: [],
                createdAt: new Date(),
              },
            ],
          });
        } catch (err) {
          console.warn("Failed to persist assistant message for chat", id, err);
        }
      }
    });

    return new Response(sse, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
  } catch (error) {
    const vercelId = request.headers.get("x-vercel-id");

    if (error instanceof ChatSDKError) {
      return error.toResponse();
    }

    // Check for Vercel AI Gateway credit card error
    if (
      error instanceof Error &&
      error.message?.includes(
        "AI Gateway requires a valid credit card on file to service requests"
      )
    ) {
      return new ChatSDKError("bad_request:activate_gateway").toResponse();
    }

    console.error("Unhandled error in chat API:", error, { vercelId });
    return new ChatSDKError("offline:chat").toResponse();
  }
}

export async function DELETE(request: Request) {
  const { searchParams } = new URL(request.url);
  const id = searchParams.get("id");

  if (!id) {
    return new ChatSDKError("bad_request:api").toResponse();
  }

  const session = await auth();

  if (!session?.user) {
    return new ChatSDKError("unauthorized:chat").toResponse();
  }

  const chat = await getChatById({ id });

  if (chat?.userId !== session.user.id) {
    return new ChatSDKError("forbidden:chat").toResponse();
  }

  const deletedChat = await deleteChatById({ id });

  return Response.json(deletedChat, { status: 200 });
}
