// Render's fromService.hostport omits the HTTP scheme.
export function apiOrigin(value?: string): string {
  const raw = value?.trim() || "http://127.0.0.1:8000";
  const qualified = /^[a-z][a-z\d+.-]*:\/\//i.test(raw) ? raw : `http://${raw}`;
  const url = new URL(qualified);
  if (
    !["http:", "https:"].includes(url.protocol) ||
    url.username ||
    url.password ||
    url.pathname !== "/" ||
    url.search ||
    url.hash
  ) {
    throw new Error(
      "API_URL must be an HTTP(S) origin without credentials, a path or query",
    );
  }
  return url.origin;
}
