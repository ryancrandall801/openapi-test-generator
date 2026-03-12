import { NextRequest, NextResponse } from "next/server";
import { mkdtemp, readFile, rm, access } from "fs/promises";
import { join } from "path";
import { tmpdir } from "os";
import { spawn } from "child_process";

export const runtime = "nodejs";

type CommandResult = {
  stdout: string;
  stderr: string;
};

function runCommand(
  command: string,
  args: string[],
  cwd: string
): Promise<CommandResult> {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd,
      shell: false,
      stdio: ["ignore", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });

    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });

    child.on("error", (error) => {
      reject(error);
    });

    child.on("close", (code) => {
      if (code === 0) {
        resolve({ stdout, stderr });
        return;
      }

      reject(
        new Error(
          `Generator failed with exit code ${code}\n\nSTDOUT:\n${stdout}\n\nSTDERR:\n${stderr}`
        )
      );
    });
  });
}

export async function POST(request: NextRequest) {
  let tempDir: string | null = null;

  try {
    const body = await request.json();

    const specUrl = body.specUrl?.trim();
    const methods = body.methods?.trim();
    const tags = body.tags?.trim();

    if (!specUrl) {
      return NextResponse.json(
        { error: "specUrl is required." },
        { status: 400 }
      );
    }

    const repoRoot = join(process.cwd(), "..");

    tempDir = await mkdtemp(join(tmpdir(), "openapi-testgen-"));
    const outputPath = join(tempDir, "generated_api_tests.py");

    const args = [
      "-m",
      "openapi_test_generator.cli",
      specUrl,
      "--output",
      outputPath,
    ];

    if (methods) {
      args.push("--methods", methods);
    }

    if (tags) {
      args.push("--tags", tags);
    }

    const result = await runCommand("python", args, repoRoot);

    try {
      await access(outputPath);
    } catch {
      throw new Error(
        `Generator completed but no output file was created.

Expected file:
${outputPath}

STDOUT:
${result.stdout}

STDERR:
${result.stderr}`
      );
    }

    const generatedCode = await readFile(outputPath, "utf-8");

    return NextResponse.json({
      generatedCode,
      stdout: result.stdout,
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unknown error occurred.";

    return NextResponse.json(
      { error: message },
      { status: 500 }
    );
  } finally {
    if (tempDir) {
      await rm(tempDir, { recursive: true, force: true });
    }
  }
}