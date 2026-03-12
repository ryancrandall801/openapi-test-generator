"use client";

import { useState } from "react";

export default function OpenApiTestGeneratorLandingPage() {
  const [specUrl, setSpecUrl] = useState(
    "https://petstore3.swagger.io/api/v3/openapi.json"
  );
  const [methods, setMethods] = useState("GET");
  const [tags, setTags] = useState("");
  const [generatedCode, setGeneratedCode] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  const fillDemo = (url: string, methodsValue = "GET", tagsValue = "") => {
    setSpecUrl(url);
    setMethods(methodsValue);
    setTags(tagsValue);
    setError("");
    setGeneratedCode("");
    setCopied(false);
  };

  const handleGenerate = async () => {
    const trimmedSpecUrl = specUrl.trim();

    if (!trimmedSpecUrl) {
      setError("Please enter an OpenAPI spec URL.");
      return;
    }

    setIsLoading(true);
    setError("");
    setGeneratedCode("");
    setCopied(false);

    try {
      const response = await fetch("/api/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          specUrl: trimmedSpecUrl,
          methods: methods.trim(),
          tags: tags.trim(),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to generate tests.");
      }

      setGeneratedCode(data.generatedCode);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = async () => {
    if (!generatedCode) return;

    try {
      await navigator.clipboard.writeText(generatedCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setError("Failed to copy generated tests.");
    }
  };

  const handleDownload = () => {
    if (!generatedCode) return;

    const blob = new Blob([generatedCode], { type: "text/x-python" });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = "generated_api_tests.py";
    link.click();

    URL.revokeObjectURL(url);
  };

  const features = [
    {
      title: "Generate real pytest code",
      body: "Turn an OpenAPI spec into a runnable Python API test suite in seconds.",
    },
    {
      title: "Includes useful validation",
      body: "Generate happy-path tests, negative tests, and JSON schema validation.",
    },
    {
      title: "Start small, expand later",
      body: "Generate GET smoke tests first, then grow into deeper API coverage.",
    },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <main className="mx-auto max-w-6xl px-6 py-12">

        {/* HERO */}
        <section className="max-w-3xl">
          <div className="inline-flex rounded-full bg-sky-400/10 px-4 py-1 text-sm text-sky-300">
            OpenAPI → pytest
          </div>

          <h1 className="mt-6 text-4xl font-semibold tracking-tight sm:text-5xl">
            Turn your OpenAPI spec into a runnable pytest suite.
          </h1>

          <p className="mt-4 text-lg text-slate-300">
            Generate API tests automatically from an OpenAPI spec with request
            payload generation, schema validation, negative tests, and
            auth-aware configuration.
          </p>
        </section>

        {/* DEMO */}
        <section className="mt-10 rounded-3xl border border-slate-800 bg-slate-900/60 p-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">

            <div>
              <h2 className="text-2xl font-semibold">Try the demo</h2>
              <p className="mt-1 text-sm text-slate-400">
                Paste a public OpenAPI URL and preview generated pytest code.
              </p>
            </div>

            <div className="flex flex-col gap-2">

            <div className="flex flex-wrap gap-2">
              <button
                onClick={() =>
                  fillDemo("https://petstore3.swagger.io/api/v3/openapi.json")
                }
                className="rounded-lg border border-slate-700 px-3 py-2 text-sm hover:bg-slate-900"
              >
                Petstore
              </button>

              <button
                onClick={() =>
                  fillDemo(
                    "https://raw.githubusercontent.com/github/rest-api-description/main/descriptions/api.github.com/api.github.com.json"
                  )
                }
                className="rounded-lg border border-slate-700 px-3 py-2 text-sm hover:bg-slate-900"
              >
                GitHub
              </button>
            </div>

            <p className="text-xs text-slate-500">
              Try these example APIs or paste your own OpenAPI spec.
            </p>

          </div>
          </div>

          <div className="mt-6 space-y-4">

            {/* Spec URL */}
            <div>
              <label className="mb-2 block text-sm text-slate-300">
                Spec URL
              </label>

              <input
                type="url"
                value={specUrl}
                onChange={(e) => setSpecUrl(e.target.value)}
                className="w-full rounded-xl border border-slate-800 bg-slate-950 px-4 py-3 text-sm text-slate-100 outline-none focus:border-sky-400"
              />
            </div>

            {/* Methods / Tags */}
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-2 block text-sm text-slate-300">
                  Methods
                </label>

                <input
                  type="text"
                  value={methods}
                  onChange={(e) => setMethods(e.target.value)}
                  placeholder="GET or GET,POST"
                  className="w-full rounded-xl border border-slate-800 bg-slate-950 px-4 py-3 text-sm text-slate-100 outline-none focus:border-sky-400"
                />
              </div>

              <div>
                <label className="mb-2 block text-sm text-slate-300">
                  Tags
                </label>

                <input
                  type="text"
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  placeholder="Optional"
                  className="w-full rounded-xl border border-slate-800 bg-slate-950 px-4 py-3 text-sm text-slate-100 outline-none focus:border-sky-400"
                />
              </div>
            </div>

            {/* Buttons */}
            <div className="flex flex-wrap gap-3">
              <button
                onClick={handleGenerate}
                disabled={isLoading}
                className="rounded-xl bg-sky-400 px-4 py-2 font-medium text-slate-950 disabled:opacity-60"
              >
                {isLoading ? "Generating..." : "Generate tests"}
              </button>

              <button
                onClick={handleCopy}
                disabled={!generatedCode}
                className="rounded-xl border border-slate-700 px-4 py-2 text-sm text-slate-200 hover:bg-slate-900 disabled:opacity-50"
              >
                {copied ? "Copied!" : "Copy tests"}
              </button>

              <button
                onClick={handleDownload}
                disabled={!generatedCode}
                className="rounded-xl border border-slate-700 px-4 py-2 text-sm text-slate-200 hover:bg-slate-900 disabled:opacity-50"
              >
                Download .py
              </button>
            </div>

            {error && (
              <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
                {error}
              </div>
            )}
          </div>

          {/* Output */}
          <div className="mt-6">
            <div className="mb-3 text-sm text-slate-400">
              Generated preview
            </div>

            <pre className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-950 p-4 text-sm leading-6 text-slate-200">
              <code>
                {generatedCode || "# Generated tests will appear here..."}
              </code>
            </pre>
          </div>
        </section>

        {/* FEATURES */}
        <section className="mt-10 grid gap-4 md:grid-cols-3">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5"
            >
              <h3 className="text-lg font-semibold">{feature.title}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-300">
                {feature.body}
              </p>
            </div>
          ))}
        </section>

      </main>
    </div>
  );
}