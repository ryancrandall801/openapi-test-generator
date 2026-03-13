from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://openapi-test-generator.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    specUrl: str
    methods: Optional[str] = None
    tags: Optional[str] = None

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/generate")
async def generate_tests(body: GenerateRequest):
    try:
        spec_url = body.specUrl.strip()
        methods = body.methods.strip() if body.methods else None
        tags = body.tags.strip() if body.tags else None

        if not spec_url:
            raise HTTPException(status_code=400, detail="specUrl is required.")

        # Replace this with your real generator call
        generated_code = f'''# Generated pytest tests
# specUrl={spec_url}
# methods={methods}
# tags={tags}

def test_placeholder():
    assert True
'''

        return {
            "generatedCode": generated_code,
            "stdout": "Generation completed."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))