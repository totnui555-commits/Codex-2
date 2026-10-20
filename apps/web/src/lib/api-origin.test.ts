import { describe, expect, it } from "vitest";
import { apiOrigin } from "./api-origin";
import { money } from "./domain";

describe("deployment routing and truthful costs", () => {
  it("accepts Render private hostport and explicit HTTPS origins", () => {
    expect(apiOrigin("company-os-api:10000")).toBe(
      "http://company-os-api:10000",
    );
    expect(apiOrigin("https://api.example.com/")).toBe(
      "https://api.example.com",
    );
    expect(apiOrigin()).toBe("http://127.0.0.1:8000");
  });
  it("rejects credentials, unsupported schemes and ambiguous API paths", () => {
    for (const value of [
      "https://user:secret@host",
      "file:///etc/passwd",
      "https://host/path",
      "https://host?token=secret",
    ]) {
      expect(() => apiOrigin(value)).toThrow();
    }
  });
  it("keeps measured sub-baht costs visible", () => {
    expect(money("0.0843")).toContain("0.0843");
    expect(money("1234.56")).toContain("1,234.56");
  });
});
