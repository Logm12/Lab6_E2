from flask import Blueprint, request, jsonify, Response, stream_with_context
from app.services.chat_service import chat_service
from app.services.rag.memory import EnhancedConversationMemory
from app.services.llm.client import llm_client_answer
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__)

# Simple in-memory session storage
sessions = {}

def get_memory(session_id: str = "default") -> EnhancedConversationMemory:
    if session_id not in sessions:
        sessions[session_id] = EnhancedConversationMemory(max_messages=10)
    return sessions[session_id]

def extract_question(data: dict) -> str:
    """Extract question from various input formats"""
    # 1. Direct 'question' field
    if data.get('question'):
        return data.get('question')
    
    # 2. 'messages' array (typical chat format)
    messages = data.get('messages', [])
    if isinstance(messages, list) and messages:
        last_message = messages[-1]
        
        # Handle { role, content } format
        if isinstance(last_message, dict):
            # Check for 'content' string
            if 'content' in last_message and isinstance(last_message['content'], str):
                return last_message['content']
            
            # Check for 'parts' array (Vercel AI SDK)
            if 'parts' in last_message and isinstance(last_message['parts'], list):
                text_parts = [p.get('text', '') for p in last_message['parts'] if p.get('type') == 'text']
                return "".join(text_parts)
    
    return None

@chat_bp.route('/chat', methods=['POST'])
def chat():
    """
    Chat endpoint (Non-streaming)
    """
    data = request.json or {}
    question = extract_question(data)
    session_id = data.get('session_id', data.get('id', 'default'))
    
    if not question:
        return jsonify({"error": "Question is required"}), 400
    
    memory = get_memory(session_id)
    result = chat_service.process_question(question, memory)
    
    response = {
        "answer": result['answer'],
        "sql": result['sql'],
        "data": result['df'].head(100).to_dict(orient='records') if result['df'] is not None else [],
        "row_count": result['row_count'],
        "conversation": {
            "session_id": session_id,
            "total_messages": len(memory.messages)
        }
    }
    
    return jsonify(response)

@chat_bp.route('/chat/stream', methods=['POST'])
def chat_stream():
    """
    Chat endpoint (Streaming SSE)
    """
    data = request.json or {}
    logger.info(f"Stream Request Data Keys: {data.keys()}")
    
    question = extract_question(data)
    session_id = data.get('session_id', data.get('id', 'default'))
    
    if not question:
        logger.error("No question found in request")
        return jsonify({"error": "Question is required. Send 'question' string or 'messages' array."}), 400

    memory = get_memory(session_id)

    def generate():
        try:
            # Seed memory with prior messages if provided by frontend
            try:
                incoming_messages = data.get('messages', [])
                if isinstance(incoming_messages, list) and incoming_messages:
                    def extract_text(msg: dict) -> str:
                        if 'content' in msg and isinstance(msg['content'], str):
                            return msg['content']
                        if 'parts' in msg and isinstance(msg['parts'], list):
                            texts = []
                            for p in msg['parts']:
                                if isinstance(p, dict) and p.get('type') == 'text':
                                    t = p.get('text')
                                    if isinstance(t, str):
                                        texts.append(t)
                            return "".join(texts)
                        return ""
                    
                    # Add all previous turns except the latest (which is `question`)
                    for prev in incoming_messages[:-1]:
                        role = prev.get('role', 'user')
                        content = extract_text(prev)
                        if isinstance(content, str) and content.strip():
                            memory.add_message(role, content.strip())
            except Exception as e:
                logger.warning(f"Failed to seed memory from incoming messages: {e}")

            # Delegate to ChatService which uses LangGraph
            yield from chat_service.process_question_stream(question, memory)

        except Exception as e:
            logger.error(f"Error in stream generation: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return Response(stream_with_context(generate()), content_type='text/event-stream')

@chat_bp.route('/title', methods=['POST'])
def generate_title():
    """
    Generate a short conversation title from text or messages.
    Compatible with frontend calling POST /ai/title.
    """
    data = request.json or {}
    text = data.get('text')
    if not text:
        msg = extract_question(data)
        text = msg or ""
    if not text:
        return jsonify({"error": "Text is required"}), 400

    system_prompt = (
        "Bạn là trợ lý đặt tiêu đề cuộc trò chuyện ngắn gọn (5-8 từ), "
        "rõ ràng, tiếng Việt, không dấu câu ở cuối."
    )
    user_prompt = f"Hãy đặt tiêu đề ngắn gọn cho nội dung: {text}"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    try:
        title = llm_client_answer.chat_completion(
            messages=messages,
            temperature=0.2,
            max_tokens=128,
            stream=False,
        ).strip()
        title = title.replace("\n", " ").strip().strip('"').strip("'")
        return jsonify({"title": title or "Cuộc trò chuyện"})
    except Exception as e:
        logger.exception("Generate title failed")
        return jsonify({"error": str(e)}), 400
