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
                cwd=".",
            )

            if result.returncode != 0:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        f"Generator failed with exit code {result.returncode}\n\n"
                        f"STDOUT:\n{result.stdout}\n\n"
                        f"STDERR:\n{result.stderr}"
                    ),
                )

            if not output_path.exists():
                raise HTTPException(
                    status_code=500,
                    detail=(
                        "Generator completed but no output file was created.\n\n"
                        f"Expected file: {output_path}\n\n"
                        f"STDOUT:\n{result.stdout}\n\n"
                        f"STDERR:\n{result.stderr}"
                    ),
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