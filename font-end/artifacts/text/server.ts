import { createDocumentHandler } from "@/lib/artifacts/server";

export const textDocumentHandler = createDocumentHandler<"text">({
  kind: "text",
  onCreateDocument: ({ title, dataStream }) => {
    dataStream.write({
      type: "data-textDelta",
      data: title,
      transient: true,
    });
    return Promise.resolve(title);
  },
  onUpdateDocument: ({ document, description, dataStream }) => {
    const content = description || document.content || "";
    dataStream.write({
      type: "data-textDelta",
      data: content,
      transient: true,
    });
    return Promise.resolve(content);
  },
});
