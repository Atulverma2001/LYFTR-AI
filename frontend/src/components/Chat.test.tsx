import { fireEvent, render, screen } from "@testing-library/react";
import { Chat } from "./Chat";

const props = { items: [], pending: false, health: null, systemPrompt: "", onSystemPrompt: () => {}, simulate: "", onSimulate: () => {} };

test("input and send button exist; Enter and click send then clear the input", () => {
  const onSend = vi.fn();
  render(<Chat {...props} onSend={onSend} />);
  const input = screen.getByTestId("chat-input") as HTMLTextAreaElement;
  expect(screen.getByTestId("send-button")).toBeInTheDocument();
  expect(screen.getByTestId("system-prompt-input")).toBeInTheDocument();
  fireEvent.change(input, { target: { value: "hello" } });
  fireEvent.keyDown(input, { key: "Enter" });
  expect(onSend).toHaveBeenCalledWith("hello");
  expect(input.value).toBe("");
  fireEvent.change(input, { target: { value: "again" } });
  fireEvent.click(screen.getByTestId("send-button"));
  expect(onSend).toHaveBeenLastCalledWith("again");
});
