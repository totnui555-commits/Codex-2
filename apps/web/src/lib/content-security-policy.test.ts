import { describe, expect, it } from "vitest";
import { contentSecurityPolicy } from "./content-security-policy";

describe("request-scoped content security policy", () => {
  it("requires the supplied nonce for production scripts and denies eval", () => {
    const policy = contentSecurityPolicy("test-nonce", false);
    const scriptPolicy = policy
      .split(";")
      .find((directive) => directive.trimStart().startsWith("script-src"));
    expect(scriptPolicy).toContain(
      "script-src 'self' 'nonce-test-nonce' 'strict-dynamic'",
    );
    expect(scriptPolicy).not.toContain("'unsafe-inline'");
    expect(scriptPolicy).not.toContain("'unsafe-eval'");
    expect(policy).toContain("object-src 'none'");
    expect(policy).toContain("frame-ancestors 'none'");
  });

  it("allows development eval for React diagnostics only in development", () => {
    const development = contentSecurityPolicy("dev-nonce", true);
    const production = contentSecurityPolicy("prod-nonce", false);
    expect(development).toContain("'unsafe-eval'");
    expect(development).toContain("connect-src 'self' ws: wss:");
    expect(production).not.toContain("'unsafe-eval'");
    expect(production).toContain("connect-src 'self'");
    expect(production).not.toContain("ws:");
    expect(production).not.toContain("wss:");
  });
});
