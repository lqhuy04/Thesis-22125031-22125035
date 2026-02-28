import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

class Answer(BaseModel):
    """Structured answer from the LLM."""
    confidence: float
    output: str


load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=os.getenv("GEMINI_API_KEY"))
structured_llm = llm.with_structured_output(Answer)

SENTENCE_CONSTRAINT = "\n\nYêu cầu bắt buộc: Câu trả lời phải có đúng từ 3 đến 5 câu, không nhiều hơn, không ít hơn."

def generate_content(prompt: str, confidence_threshold: float = 0.7, max_retries: int = 3):
    """..."""
    constrained_prompt = prompt + SENTENCE_CONSTRAINT
    for attempt in range(max_retries):
        response = structured_llm.invoke(constrained_prompt)
        if response.confidence >= confidence_threshold:
            return {
                "confidence": response.confidence,
                "output": response.output
            }
        print(f"Attempt {attempt + 1}: confidence {response.confidence} below threshold {confidence_threshold}, retrying...")
    
    # Return the last response even if it didn't meet the threshold
    return {
        "confidence": response.confidence,
        "output": response.output
    }