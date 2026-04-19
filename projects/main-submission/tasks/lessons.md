# Project Lessons

- When parsing MCP or FastMCP tool responses, prefer `result.structuredContent` first and keep legacy `result.content` / top-level `content` parsing only as compatibility fallback.
- When a Slack brief is user-supplied, treat any non-dict payload as malformed and return `False` instead of assuming dict-like access.
