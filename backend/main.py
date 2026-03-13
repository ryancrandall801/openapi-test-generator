from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import tempfile
import subprocess
from pathlib import Path
import sys

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

@app.get("/")
def root():
    return {"message": "OpenAPI Test Generator backend is running."}

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

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "generated_api_tests.py"

            args = [
                sys.executable,
                "-m",
                "openapi_test_generator.cli",
                spec_url,
                "--output",
                str(output_path),
            ]

            if methods:
                args.extend(["--methods", methods])

            if tags:
                args.extend(["--tags", tags])

            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                print("Generator failed")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)

                stderr = (result.stderr or "").lower()

                if "modulenotfounderror" in stderr or "no module named" in stderr:
                    message = "The generator backend is missing a required dependency."
                elif "failed to establish a new connection" in stderr or "connection" in stderr:
                    message = "Could not fetch the OpenAPI spec from that URL."
                elif "timeout" in stderr:
                    message = "Fetching or generating tests took too long."
                elif "openapi" in stderr or "swagger" in stderr or "validation" in stderr:
                    message = "That document does not appear to be a valid OpenAPI spec."
                elif "recursionerror" in stderr or "maximum recursion depth exceeded" in stderr:
                    message = "This spec is too complex to generate fully right now. Try narrowing by method or tag."
                elif "keyerror" in stderr or "typeerror" in stderr or "attributeerror" in stderr:
                    message = "This spec uses schema patterns that are not fully supported yet."
                else:
                    message = "Test generation failed for this spec."

                raise HTTPException(status_code=500, detail=message)

            if not output_path.exists():
                print("Generator completed but no output file was created.")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)

                raise HTTPException(
                    status_code=500,
                    detail="Generation completed, but no test file was produced."
                )

            generated_code = output_path.read_text(encoding="utf-8")

            return {
                "generatedCode": generated_code,
                "stdout": result.stdout,
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))