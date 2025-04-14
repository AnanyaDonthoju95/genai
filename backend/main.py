import os
import requests
import google.generativeai as genai
from fastapi import FastAPI
from pydantic import BaseModel
from pinecone import Pinecone, ServerlessSpec
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------- Configuration ----------
# Gemini LLM
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash-latest")
print("[DEBUG] Gemini model initialized.")

# Pinecone Setup
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY environment variable is not set")

pc = Pinecone(api_key=PINECONE_API_KEY)
index_name = "genai-intel-chat"
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=768,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
index = pc.Index(index_name)
print("[DEBUG] Pinecone index set up.")

# Serper API
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
if not SERPER_API_KEY:
    raise ValueError("SERPER_API_KEY environment variable is not set")

# FastAPI App
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
print("[DEBUG] FastAPI app initialized with CORS.")

# ---------- Schema ----------
class ChatRequest(BaseModel):
    user_id: str
    message: str

# ---------- Embedding & Memory ----------
def get_embedding(text):
    try:
        res = genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type="retrieval_document"
        )
        return res["embedding"]
    except Exception as e:
        print(f"[ERROR] Embedding failed: {e}")
        return None

def store_memory(user_id: str, topic: str, full_message: str):
    vector = get_embedding(full_message)
    if vector:
        try:
            index.upsert(vectors=[{
                "id": f"{user_id}:{topic}",
                "values": vector,
                "metadata": {
                    "user_id": user_id,
                    "topic": topic,
                    "content": full_message
                }
            }])
        except Exception as e:
            print(f"[ERROR] Memory store failed: {e}")

def retrieve_memory(user_id: str, query: str, top_k: int = 3):
    vector = get_embedding(query)
    if vector:
        try:
            result = index.query(
                vector=vector,
                top_k=top_k,
                include_metadata=True,
                filter={"user_id": {"$eq": user_id}}
            )
            return [match["metadata"]["content"] for match in result.get("matches", [])]
        except Exception as e:
            print(f"[ERROR] Memory retrieve failed: {e}")
    return []

# ---------- News ----------
def fetch_news(company):
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {"q": company}
    try:
        res = requests.post("https://google.serper.dev/news", headers=headers, json=payload)
        res.raise_for_status()
        return res.json().get("news", [])
    except Exception as e:
        print(f"[ERROR] News fetch failed: {e}")
        return []

def summarize_news(news_items):
    if not news_items:
        return "No news found."
    headlines = "\n".join([f"{n['title']}: {n['link']}" for n in news_items[:5]])
    prompt = f"Summarize the following headlines:\n{headlines}"
    try:
        return model.generate_content(prompt).text
    except Exception as e:
        print(f"[ERROR] News summary failed: {e}")
        return "Error summarizing news."

# ---------- Market Comparison ----------
def compare_market(company, competitors):
    prompt = f"Compare {company} with {', '.join(competitors)} in terms of market share and strategy."
    try:
        return model.generate_content(prompt).text
    except Exception as e:
        print(f"[ERROR] Comparison failed: {e}")
        return "Error comparing companies."

# ---------- Chat Endpoint ----------
@app.post("/chat")
async def chat(request: ChatRequest):
    user_id = request.user_id
    user_input = request.message

    try:
        # Check if the query is about the latest product launches
        if "latest product launches" in user_input.lower():
            company_name = user_input.split("by")[-1].strip()  # Extract company name from the query
            news_items = fetch_news(company_name)
            summarized_news = summarize_news(news_items)
            return {"response": summarized_news}

        # Retrieve memory for added context
        memory_contexts = retrieve_memory(user_id, user_input)
        memory_text = "\n".join(memory_contexts)

        # Construct prompt with memory
        prompt = f"You are a competitive intelligence chatbot.\n\nPrevious memory:\n{memory_text}\n\nUser: {user_input}\n\nAssistant:"
        response = model.generate_content(prompt).text

        # Store this message for future context
        store_memory(user_id, topic="chat", full_message=user_input)

        return {"response": response}

    except Exception as e:
        return {"response": f"Error: {str(e)}"}

# ---------- Root ----------
@app.get("/")
def home():
    return {"message": "AI Intel Agent Running 🚀"}
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
