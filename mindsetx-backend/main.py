from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import time

app = FastAPI(title="MindsetX API")

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev only, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ThoughtInput(BaseModel):
    thought: str

class ReframeResponse(BaseModel):
    pattern: str
    reframed_thought: str
    suggestion: str

@app.get("/")
def read_root():
    return {"status": "ok", "message": "MindsetX API is running securely."}

@app.post("/api/reframe", response_model=ReframeResponse)
def reframe_thought(input_data: ThoughtInput):
    # Security: validate input
    if len(input_data.thought) < 10:
        raise HTTPException(status_code=400, detail="Thought too short")
    
    # Mocking AI response for MVP. 
    # In production, this integrates with OpenAI API and strips identifiers.
    # time.sleep(1.5) # Simulate API delay
    
    return ReframeResponse(
        pattern="Overthinking / Self-doubt",
        reframed_thought="I'm facing a challenge, but I can approach it one step at a time.",
        suggestion="Write down 1 small step you can take right now."
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
