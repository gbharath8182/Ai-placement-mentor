import asyncio
import json
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from backend.database import get_collection
from backend.models import AIRecommendRequest, AIChatRequest, AIExplainRequest
from backend.auth import get_current_user
from backend.config import settings
from bson import ObjectId

router = APIRouter(prefix="/ai", tags=["ai"])


def topic_learning_context(topic: dict) -> str:
    """Flatten the real lesson material; topics store it under subtopics."""
    sections = []
    for subtopic in topic.get("subtopics", []):
        parts = [f"Subtopic: {subtopic.get('title', '')}"]
        for block in subtopic.get("content_blocks", []):
            if block.get("type") in {"text", "heading", "list", "callout"}:
                value = block.get("value", "")
                if block.get("type") == "list":
                    value = "; ".join(block.get("items", []))
                parts.append(str(value))
        sections.append("\n".join(parts))
    return "\n\n".join(sections)[:14000] or json.dumps(topic.get("content_blocks", []))

async def call_groq_json(messages: list) -> str:
    if not settings.GROQ_API_KEY:
        return (
            "🤖 **[Demonstration Mode]**\n\n"
            "This is a simulated AI response because `GROQ_API_KEY` is not configured in your `.env` file.\n\n"
            "### Suggested Roadmap & Feedback:\n"
            "1. **Core Review**: Review variables, syntax, and conditionals.\n"
            "2. **Next Recommended Topic**: Control Flow or Data Structures.\n\n"
            "Please add your `GROQ_API_KEY` to `.env` to enable live Groq completions."
        )
        
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": settings.GROQ_PRIMARY_MODEL,
        "messages": messages,
        "temperature": 0.4,
        "stream": False
    }
    
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body, timeout=30.0)
            if r.status_code != 200:
                return f"⚠️ Groq API Error ({r.status_code}): {r.text}"
            res = r.json()
            return res["choices"][0]["message"]["content"]
        except Exception as e:
            return f"⚠️ Exception connecting to Groq: {str(e)}"

async def stream_groq(messages: list):
    if not settings.GROQ_API_KEY:
        mock_text = (
            "🤖 **[Demonstration Mode]**\n\n"
            "Hello! I am your AI learning assistant. Since `GROQ_API_KEY` is not set in `.env`, "
            "I'm operating in simulation mode. Here is what we can do once connected:\n\n"
            "- ⚡ **Interactive Q&A**: Ask me to explain code snippets, resolve errors, or give analogies.\n"
            "- 🎯 **Personalized quizzes**: Request mock questions tailored to your experience.\n"
            "- 📚 **Custom guidance**: Ask for real-world projects based on this topic.\n\n"
            "To connect to live Groq Llama-3.3 serving, add `GROQ_API_KEY=your_key` to `.env`!"
        )
        for word in mock_text.split(" "):
            yield f"data: {json.dumps({'choices': [{'delta': {'content': word + ' '}}]})}\n\n".encode('utf-8')
            await asyncio.sleep(0.04)
        yield b"data: [DONE]\n\n"
        return

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": settings.GROQ_PRIMARY_MODEL,
        "messages": messages,
        "temperature": 0.4,
        "stream": True
    }
    
    async with httpx.AsyncClient() as client:
        try:
            async with client.stream("POST", "https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body, timeout=30.0) as r:
                if r.status_code != 200:
                    err_body = await r.aread()
                    yield f"data: {json.dumps({'error': f'Groq API Error: {err_body.decode()}'})}\n\n".encode('utf-8')
                    return
                async for chunk in r.aiter_lines():
                    if chunk.strip():
                        yield f"{chunk}\n\n".encode('utf-8')
        except Exception as e:
            yield f"data: {json.dumps({'error': f'Exception: {str(e)}'})}\n\n".encode('utf-8')

@router.post("/recommend")
async def recommend_topics(req: AIRecommendRequest, current_user: dict = Depends(get_current_user)):
    topics_coll = get_collection("topics")
    topic = await topics_coll.find_one({"slug": req.topic_slug})
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
        
    content_blocks_str = topic_learning_context(topic)
    
    system_prompt = (
        f"You are an expert learning consultant. Based on the user's answers and progress for the topic '{topic.get('title')}', "
        "recommend the next topics and outline. Use the following context details:\n"
        f"Topic Content blocks: {content_blocks_str}\n"
        f"User level: {current_user.get('profile', {}).get('experience_level')}\n"
        f"User survey answers: {json.dumps(req.answers)}\n"
        "Provide: 1) Adapted roadmap for this topic, 2) Next 2 recommended topics and explanation why, "
        "3) Brief encouraging remarks. Keep it concise."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Suggest my learning roadmap based on my level and inputs."}
    ]
    
    recommendation = await call_groq_json(messages)
    return {"recommendation": recommendation}

@router.post("/explain")
async def explain_topic(req: AIExplainRequest, current_user: dict = Depends(get_current_user)):
    topics_coll = get_collection("topics")
    topic = await topics_coll.find_one({"slug": req.topic_slug})
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
        
    content_blocks_str = topic_learning_context(topic)
    
    system_prompt = (
        f"You are a computer science professor explaining the topic '{topic.get('title')}' "
        f"to a student with experience level: '{req.level}'.\n"
        f"Current Topic content blocks:\n{content_blocks_str}\n\n"
        "Adapt your language accordingly:\n"
        "- If 'fresher': Use simple terms, analogies, basic syntax explanations.\n"
        "- If 'intermediate': Focus on typical use cases, intermediate concepts, structures.\n"
        "- If 'experienced': Focus on optimization, memory layout, system implications, and code patterns.\n"
        "Ground your explanation in the provided content blocks, but enrich it with your knowledge. "
        "Use clear Markdown sections: Mental model, Step-by-step explanation, Worked example, Common pitfalls, and Quick self-check."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Please explain the topic '{topic.get('title')}' in detail for my level."}
    ]
    
    explanation = await call_groq_json(messages)
    return {"explanation": explanation}

@router.post("/chat")
async def chat_topic(req: AIChatRequest, current_user: dict = Depends(get_current_user)):
    topics_coll = get_collection("topics")
    topic = await topics_coll.find_one({"slug": req.topic_slug})
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
        
    content_blocks_str = topic_learning_context(topic)
    
    # Save chat session history
    chat_sessions_coll = get_collection("chat_sessions")
    session = await chat_sessions_coll.find_one({
        "user_id": ObjectId(current_user["id"]),
        "topic_slug": req.topic_slug
    })
    
    history_messages = []
    if session:
        # Convert messages from DB format to Groq API format
        for m in session.get("messages", [])[-10:]: # Keep last 10 messages for context
            history_messages.append({"role": m["role"], "content": m["content"]})
            
    system_prompt = (
        f"You are a helpful learning assistant for the topic '{topic.get('title')}' on our education platform.\n"
        f"Reference material (topic content blocks):\n{content_blocks_str}\n\n"
        f"The user's experience level is '{current_user.get('profile', {}).get('experience_level')}'.\n"
        "Answers must be grounded in this reference material. If the user asks about unrelated items, "
        "politely bring them back to the learning topic. Keep code snippets short and clean."
    )
    
    messages = [{"role": "system", "content": system_prompt}] + history_messages + [{"role": "user", "content": req.message}]
    
    # Append user's new message to database history in background
    new_message_user = {"role": "user", "content": req.message, "ts": asyncio.get_event_loop().time()}
    await chat_sessions_coll.update_one(
        {"user_id": ObjectId(current_user["id"]), "topic_slug": req.topic_slug},
        {"$push": {"messages": new_message_user}},
        upsert=True
    )
    
    # When streaming, the response needs to be captured so we can append the assistant's response to history.
    # To do this cleanly and keep streaming fast, we'll run a custom generator that yields the stream and 
    # saves the text at the end.
    
    async def log_and_stream():
        full_response = ""
        async for chunk in stream_groq(messages):
            yield chunk
            # Extract content if not mock and format matches SSE
            try:
                chunk_str = chunk.decode('utf-8')
                if chunk_str.startswith("data: "):
                    data_str = chunk_str[6:].strip()
                    if data_str == "[DONE]":
                        continue
                    data_json = json.loads(data_str)
                    content = data_json.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    full_response += content
            except Exception:
                pass
        
        # Save complete AI response if any content was gathered
        if not full_response:
            # Fallback text if we streamed mock text
            full_response = "Simulated Response"
            
        new_message_assistant = {"role": "assistant", "content": full_response, "ts": asyncio.get_event_loop().time()}
        await chat_sessions_coll.update_one(
            {"user_id": ObjectId(current_user["id"]), "topic_slug": req.topic_slug},
            {"$push": {"messages": new_message_assistant}},
            upsert=True
        )
        
    return StreamingResponse(log_and_stream(), media_type="text/event-stream")
