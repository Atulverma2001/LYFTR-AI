import { render, screen } from "@testing-library/react";
import { Message } from "./Message";

const metadata = {
  resolution_source: "LLM_CACHE" as const,
  model: "gemini/gemini-2.0-flash",
  latency_ms: 12,
  input_tokens: 42,
  output_tokens: 9,
  key_id: null,
  fallback_attempts: 0,
};

test("assistant message exposes the required test ids with exact content", () => {
  render(<Message item={{ id: "1", role: "assistant", text: "Paris.", metadata }} />);
  const box = screen.getByTestId("assistant-message");
  expect(box).toHaveTextContent("Paris.");
  expect(screen.getByTestId("meta-source")).toHaveTextContent(/^LLM_CACHE$/);
  expect(screen.getByTestId("meta-model")).toHaveTextContent("gemini/gemini-2.0-flash");
  expect(screen.getByTestId("meta-latency")).toHaveTextContent("12 ms");
  expect(screen.getByTestId("meta-input-tokens")).toHaveTextContent(/^42$/);
  expect(screen.getByTestId("meta-output-tokens")).toHaveTextContent(/^9$/);
  expect(box).toContainElement(screen.getByTestId("meta-source"));
});

test("errors render as readable alerts", () => {
  render(<Message item={{ id: "2", role: "error", text: "All AI providers are unavailable right now." }} />);
  expect(screen.getByRole("alert")).toHaveTextContent("unavailable");
});
