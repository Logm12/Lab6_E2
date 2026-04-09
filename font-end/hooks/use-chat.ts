import { useCallback, useMemo, useRef, useState } from "react";
import { ChatSDKError } from "@/lib/errors";
import type { ChatMessage } from "@/lib/types";
import { fetchWithErrorHandlers, generateUUID } from "@/lib/utils";

export type UseChatHelpers<M = ChatMessage> = {
  messages: M[];
  setMessages: (updater: ((prev: M[]) => M[]) | M[]) => void;
  sendMessage: (message: M) => Promise<void>;
  status: "idle" | "submitted" | "streaming";
  stop: () => void;
  regenerate: () => void;
  resumeStream: () => void;
};

type UseChatOptions<M> = {
  id: string;
  messages: M[];
  generateId?: () => string;
  api?: string;
  onData?: (dataPart: any) => void;
  getPostBody?: (message: M, id: string) => any;
};

export function useChat<M extends ChatMessage>({
  id,
  messages: initialMessages,
  generateId = generateUUID,
  api = "/api/chat",
  onData,
  getPostBody,
}: UseChatOptions<M>): UseChatHelpers<M> {
  const [messages, setMessages] = useState<M[]>(initialMessages);
  const [status, setStatus] = useState<UseChatHelpers<M>["status"]>("idle");
  const abortRef = useRef<AbortController | null>(null);
  const lastUserMessageRef = useRef<M | null>(null);

  const setMessagesSafe = useCallback((updater: ((prev: M[]) => M[]) | M[]) => {
    setMessages((prev) =>
      typeof updater === "function" ? (updater as any)(prev) : (updater as any)
    );
  }, []);

  const stream = useCallback(
    async (body: any) => {
      setStatus("streaming");
      const controller = new AbortController();
      abortRef.current = controller;
      try {
        const response = await fetchWithErrorHandlers(api, {
          method: "POST",
          body: JSON.stringify(body),
          signal: controller.signal,
          headers: { "Content-Type": "application/json" },
        });
        if (!response.body) {
          setStatus("idle");
          return;
        }
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let assistantMessage: M | null = null;
        let assistantText = "";
        const assistantId = generateId();
        for (;;) {
          const { done, value } = await reader.read();
          if (done) {
            break;
          }
          buffer += decoder.decode(value, { stream: true });
          let idx = buffer.indexOf("\n\n");
          while (idx !== -1) {
            const raw = buffer.slice(0, idx).trim();
            buffer = buffer.slice(idx + 2);
            const dataLine = raw.startsWith("data:") ? raw.slice(5).trim() : raw;
            const maybeJson = dataLine.trim();
            if (maybeJson.startsWith("{") && maybeJson.endsWith("}")) {
              const json = JSON.parse(maybeJson);
              if (json.type === "text-delta" && typeof json.data === "string") {
                assistantText += json.data;
                if (!assistantMessage) {
                  assistantMessage = {
                    id: assistantId as any,
                    role: "assistant",
                    parts: [{ type: "text", text: "" }] as any,
                  } as M;
                  setMessagesSafe((prev) => [...prev, assistantMessage as M]);
                }
                setMessagesSafe((prev) =>
                  prev.map((m) => {
                    if ((m as any).id === assistantId) {
                      const parts = (m as any).parts.slice();
                      const textPartIndex = parts.findIndex(
                        (p: any) => p.type === "text"
                      );
                      if (textPartIndex >= 0) {
                        parts[textPartIndex] = {
                          ...parts[textPartIndex],
                          text: assistantText,
                        };
                      } else {
                        parts.push({ type: "text", text: assistantText });
                      }
                      return { ...(m as any), parts } as M;
                    }
                    return m;
                  })
                );
              } else if (json.type && onData) {
                onData(json);
              }
            }
            idx = buffer.indexOf("\n\n");
          }
        }
      } catch (e) {
        // reset status if any error occurs during streaming
      } finally {
        setStatus("idle");
        abortRef.current = null;
      }
    },
    [api, onData, setMessagesSafe, generateId]
  );

  const sendMessage = useCallback(
    async (message: M) => {
      setStatus("submitted");
      lastUserMessageRef.current = message;
      const msgWithId = {
        ...message,
        id: (message as any).id ?? generateId(),
      } as M;
      setMessagesSafe((prev) => [...prev, msgWithId]);
      try {
        const body =
          typeof getPostBody === "function"
            ? getPostBody(msgWithId, id)
            : { id, message: msgWithId };
        await stream(body);
      } catch (error) {
        if (error instanceof ChatSDKError) {
          setStatus("idle");
          throw error;
        }
        setStatus("idle");
        throw error;
      }
    },
    [generateId, id, setMessagesSafe, stream, getPostBody]
  );

  const stop = useCallback(() => {
    abortRef.current?.abort();
    setStatus("idle");
  }, []);

  const regenerate = useCallback(async () => {
    const lastUserMessage = lastUserMessageRef.current;
    if (!lastUserMessage) {
      return;
    }
    await sendMessage(lastUserMessage);
  }, [sendMessage]);

  const resumeStream = useCallback(async () => {
    await stream({ id, resume: true });
  }, [id, stream]);

  return useMemo(
    () => ({
      messages,
      setMessages: setMessagesSafe,
      sendMessage,
      status,
      stop,
      regenerate,
      resumeStream,
    }),
    [
      messages,
      regenerate,
      resumeStream,
      sendMessage,
      setMessagesSafe,
      status,
      stop,
    ]
  );
}
