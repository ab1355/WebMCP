# AGENTS.md — Guide for AI Coding Agents

This document provides guidance for AI coding agents (e.g., GitHub Copilot, Claude, Cursor) working in this repository.

## Project Overview

**WebMCP** is a localhost WebSocket bridge that lets websites act as MCP (Model Context Protocol) servers. It exposes website tools, resources, and prompts to client-side LLMs without sharing API keys. The implementation is **not** compliant with the W3C WebMCP spec.

Key concepts:
- A **WebSocket server** runs locally and bridges MCP clients (like Claude Desktop, Cursor) to websites.
- Websites embed `webmcp.js` as a widget, obtain a registration token, and register their tools/resources/prompts with the local server.
- An **MCP server** communicates over stdio with MCP clients and forwards all requests through the WebSocket server to the relevant web page.

## Repository Structure

```
.
├── src/
│   ├── websocket-server.js   # Main entry point; daemon + WebSocket server logic
│   ├── server.js             # MCP stdio server; bridges MCP ↔ WebSocket
│   ├── tokens.js             # Token generation, storage, and validation
│   ├── config.js             # Config, env-loading, MCP client auto-install helpers
│   ├── iroh.js               # Optional iroh P2P/QUIC integration
│   └── webmcp.js             # Client-side widget (embedded in websites)
├── build.js                  # esbuild bundler for the distributable
├── index.html                # Demo / test page
├── Dockerfile                # Smithery deployment container
├── docker-compose.yml        # Docker Compose for running the WebSocket server
├── smithery.yaml             # Smithery MCP registry configuration
├── package.json
└── README.md
```

## Architecture

```
MCP Client (Claude Desktop, Cursor, etc.)
    │  stdio
    ▼
src/server.js  (MCP Server)
    │  WebSocket  ws://localhost:<port>/mcp
    ▼
src/websocket-server.js  (WebSocket Server)
    │  WebSocket  ws://localhost:<port>/<domain-channel>
    ▼
Website (webmcp.js widget in browser)
```

- Configuration and tokens are stored in `~/.webmcp/`.
- The server token is auto-generated and kept in `~/.webmcp/.env`.
- Per-channel session tokens are persisted in `~/.webmcp/.webmcp-tokens.json`.
- The iroh Ed25519 keypair (if used) is stored in `~/.webmcp/iroh.key`.

## Development Setup

```bash
# Install dependencies
npm install

# Build the distributable (outputs to build/)
npm run build

# Run the WebSocket daemon directly (no MCP stdio wrapper)
npm run start-daemon

# Run as MCP stdio server (what MCP clients call)
npm run start-mcp-client

# Stop the daemon
npm run stop-daemon

# Generate a new registration token manually
npm run authorize
```

No test suite exists yet (`npm test` exits with an error). Do not add tests unless the issue specifically requests it.

## Key Conventions

- **ES Modules**: The project uses `"type": "module"` — use `import`/`export`, not `require`.
- **Error logging**: Use `console.error(...)` for diagnostic output (stdout is reserved for MCP stdio protocol messages).
- **Token lifecycle**: Registration tokens are single-use and deleted immediately after a website connects. Session tokens persist across server restarts.
- **Channel naming**: Domain names are converted to safe channel paths via `formatChannel()` in `config.js` (dots and colons become underscores).
- **Tool name scoping**: Tools from websites are prefixed with their domain channel to avoid collisions (e.g., `localhost_3000__myTool`).
- **Timeouts**: Tool calls time out after 30 seconds; list operations after 10 seconds; sampling after 120 seconds.

## Security Considerations

- The WebSocket server only listens on `localhost` and requires token authentication for both MCP clients and web pages.
- Registration tokens are cryptographically random (16 bytes, hex-encoded) and single-use.
- When modifying authentication or token-handling code, be careful not to introduce token-reuse vulnerabilities or unauthenticated endpoints.
- The iroh integration adds authenticated encryption (QUIC/TLS 1.3) for any P2P connections.

## Making Changes

1. **Source changes**: Edit files under `src/`. The entry point for the CLI is `src/websocket-server.js`.
2. **Client widget changes**: Edit `src/webmcp.js` (embedded in websites via `<script src="webmcp.js">`).
3. **After changes**: Run `npm run build` to regenerate `build/` before testing CLI behavior end-to-end.
4. **Minimal changes**: Make the smallest change that satisfies the requirement. Avoid refactoring unrelated code.
