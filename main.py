
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from agent.graph import graph

app = FastAPI(
    title="RetailIQ Store Performance Intelligence",
    description="AI-powered retail performance investigation API",
    version="1.0.0",
)


class QuestionRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=5,
        description="A retail business question",
    )


class QuestionResponse(BaseModel):
    question: str
    answer: str


@app.get("/")
def home():
    return {
        "message": "RetailIQ Store Performance Intelligence API is running"
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=QuestionResponse)
def ask_question(request: QuestionRequest):
    try:
        result = graph.invoke({
            "question": request.question
        })
        
        answer = result.get(
            "final_answer",
            "The agent could not generate an answer.",
        )

        return QuestionResponse(
            question=request.question,
            answer=answer,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="The investigation failed. Check the application logs.",
        ) from exc
