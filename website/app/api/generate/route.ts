import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const specUrl = body.specUrl?.trim();

    if (!specUrl) {
      return NextResponse.json(
        { error: "specUrl is required." },
        { status: 400 }
      );
    }

    const backendUrl = process.env.GENERATOR_API_URL;

    if (!backendUrl) {
      return NextResponse.json(
        { error: "GENERATOR_API_URL is not set." },
        { status: 500 }
      );
    }

    const response = await fetch(`${backendUrl}/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      cache: "no-store",
    });

    const text = await response.text();

    return new NextResponse(text, {
      status: response.status,
      headers: {
        "Content-Type": "application/json",
      },
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unknown error occurred.";

    return NextResponse.json({ error: message }, { status: 500 });
  }
}