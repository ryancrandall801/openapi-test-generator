"use client";

import { useState } from "react";

export default function OpenApiTestGeneratorLandingPage() {
  const [specUrl, setSpecUrl] = useState(
    "https://petstore3.swagger.io/api/v3/openapi.json"
  );
  const [methods, setMethods] = useState("");
  const [tags, setTags] = useState("");

  const [generatedCode, setGeneratedCode] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  const scrollToDemo = () => {
    document
      .getElementById("demo")
      ?.scrollIntoView({ behavior: "smooth" });
  };

  const fillDemoApi = () => {
    const demoUrl =
      "https://petstore3.swagger.io/api/v3/openapi.json";

    setSpecUrl(demoUrl);
    setMethods("GET");
    setTags("");
    setError("");
    setGeneratedCode("");

    setTimeout(() => {
      scrollToDemo();
    }, 0);
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
        throw new Error(
          data.error || "Failed to generate tests."
        );
      }

      setGeneratedCode(data.generatedCode);
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Something went wrong.";

      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = async () => {
    if (!generatedCode) {
      return;
    }

    try {
      await navigator.clipboard.writeText(generatedCode);
      setCopied(true);

      setTimeout(() => {
        setCopied(false);
      }, 1500);
    } catch {
      setError("Failed to copy generated tests.");
  }
};

  const features = [
    {
      title: "Generate pytest tests instantly",
      body: "Turn an OpenAPI spec into a runnable pytest API test suite in seconds.",
    },
    {
      title: "Built for real API workflows",
      body: "Supports request payloads, schema validation, authentication headers, and negative tests.",
    },
    {
      title: "Start simple, expand later",
      body: "Generate safe GET smoke tests first, then expand into full API coverage.",
    },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* HERO */}

      <section className="mx-auto max-w-6xl px-6 py-24">
        <div className="space-y-8">
          <div className="inline-flex rounded-full bg-sky-400/10 px-4 py-1 text-sm text-sky-300">
            OpenAPI → pytest
          </div>

          <h1 className="text-5xl font-semibold leading-tight">
            Turn your OpenAPI spec into a runnable pytest suite.
          </h1>

          <p className="max-w-2xl text-lg text-slate-300">
            Generate API tests automatically from your
            OpenAPI spec with request payload generation,
            schema validation, negative tests, and
            authentication support.
          </p>

          <div className="flex gap-4">
            <button
              onClick={scrollToDemo}
              className="rounded-xl bg-sky-400 px-6 py-3 font-medium text-slate-950 hover:scale-[1.02]"
            >
              Generate pytest tests
            </button>

            <button
              onClick={fillDemoApi}
              className="rounded-xl border border-slate-700 px-6 py-3 hover:bg-slate-900"
            >
              Try Demo API
            </button>
          </div>
        </div>
      </section>

      {/* FEATURES */}

      <section className="mx-auto max-w-6xl px-6 pb-20 grid gap-6 md:grid-cols-3">
        {features.map((feature) => (
          <div
            key={feature.title}
            className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6"
          >
            <h3 className="text-xl font-semibold">
              {feature.title}
            </h3>

            <p className="mt-3 text-slate-300">
              {feature.body}
            </p>
          </div>
        ))}
      </section>

      {/* DEMO */}

      <section
        id="demo"
        className="mx-auto max-w-6xl px-6 py-24"
      >
        <h2 className="text-3xl font-semibold">
          Try the Demo
        </h2>

        <p className="mt-3 text-slate-300">
          Paste an OpenAPI spec URL and preview the
          generated pytest tests.
        </p>

        <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-4">
          {/* SPEC URL */}

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

            <p className="mt-2 text-xs text-slate-500">
              Demo is preloaded with Swagger Petstore.
            </p>
          </div>

          {/* METHODS + TAGS */}

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="mb-2 block text-sm text-slate-300">
                Methods
              </label>

              <input
                type="text"
                value={methods}
                onChange={(e) =>
                  setMethods(e.target.value)
                }
                placeholder="GET"
                className="w-full rounded-xl border border-slate-800 bg-slate-950 px-4 py-3 text-sm text-slate-100"
              />
            </div>

            <div>
              <label className="mb-2 block text-sm text-slate-300">
                Tags
              </label>

              <input
                type="text"
                value={tags}
                onChange={(e) =>
                  setTags(e.target.value)
                }
                placeholder=""
                className="w-full rounded-xl border border-slate-800 bg-slate-950 px-4 py-3 text-sm text-slate-100"
              />
            </div>
          </div>

          {/* GENERATE BUTTON */}

          <button
            onClick={handleGenerate}
            disabled={isLoading}
            className="rounded-xl bg-sky-400 px-4 py-2 font-medium text-slate-950 disabled:opacity-60"
          >
            {isLoading
              ? "Generating..."
              : "Generate tests"}
          </button>

          {/* ERROR */}

          {error && (
            <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300 whitespace-pre-wrap">
              {error}
            </div>
          )}
        </div>

        {/* OUTPUT */}

        <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-950 p-6">
          <div className="mb-3 flex items-center justify-between">
            <div className="text-sm text-slate-400">
              Generated preview
            </div>

            <button
              onClick={handleCopy}
              disabled={!generatedCode}
              className="rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-200 hover:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {copied ? "Copied!" : "Copy tests"}
            </button>
          </div>

          <pre className="overflow-x-auto whitespace-pre-wrap text-sm text-slate-300">
            {generatedCode || "Generated tests will appear here..."}
          </pre>
        </div>
      </section>
    </div>
  );
}