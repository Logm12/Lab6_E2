import { createDocumentHandler } from "@/lib/artifacts/server";

export const sheetDocumentHandler = createDocumentHandler<"sheet">({
  kind: "sheet",
  onCreateDocument: ({ title, dataStream }) => {
    dataStream.write({
      type: "data-sheetDelta",
      data: title,
      transient: true,
    });
    return Promise.resolve(title);
  },
  onUpdateDocument: ({ document, description, dataStream }) => {
    const content = description || document.content || "";
    dataStream.write({
      type: "data-sheetDelta",
      data: content,
      transient: true,
    });
    return Promise.resolve(content);
  },
});
