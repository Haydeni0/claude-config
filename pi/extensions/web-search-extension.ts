/**
 * Web Search Extension for pi
 *
 * Registers two tools the LLM can call directly:
 *   - web_search:  query the web, return ranked results (title, url, snippet)
 *   - web_fetch:   fetch a URL and return clean readable text/markdown
 *
 * Backends:
 *   - search (default, no key):  DuckDuckGo HTML endpoint
 *       Set WEB_SEARCH_PROVIDER=brave   + BRAVE_API_KEY   -> Brave Search API
 *       Set WEB_SEARCH_PROVIDER=tavily  + TAVILY_API_KEY  -> Tavily
 *   - fetch  (default, no key):  Jina AI Reader (https://r.jina.ai/<url>)
 *       Returns clean markdown of the page; free for light use.
 *
 * Lives in ~/.claude/pi/extensions (source of truth). pi reads it directly via the
 * pointer in ~/.pi/agent/settings.json, so after editing run /reload in pi — no re-sync.
 *
 * Output is truncated to pi's built-in limits (50KB / 2000 lines) so search results
 * never overwhelm the LLM context.
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import {
	DEFAULT_MAX_BYTES,
	DEFAULT_MAX_LINES,
	formatSize,
	truncateHead,
} from "@earendil-works/pi-coding-agent";
import { Text } from "@earendil-works/pi-tui";
import { Type } from "typebox";

const SEARCH_TIMEOUT_MS = 15_000;
const FETCH_TIMEOUT_MS = 30_000;
const MAX_RESULTS = 10;

type SearchHit = { title: string; url: string; snippet: string };

// ---- shared helpers -------------------------------------------------------

/** Merge a pi abort signal with a timeout into one signal. */
function withTimeout(signal: AbortSignal | undefined, ms: number) {
	const controller = new AbortController();
	const timer = setTimeout(() => controller.abort(), ms);
	if (signal) {
		if (signal.aborted) controller.abort();
		else signal.addEventListener("abort", () => controller.abort(), { once: true });
	}
	return { signal: controller.signal, clear: () => clearTimeout(timer) };
}

function decodeHtmlEntities(s: string): string {
	return s
		.replace(/&amp;/g, "&")
		.replace(/&lt;/g, "<")
		.replace(/&gt;/g, ">")
		.replace(/&quot;/g, '"')
		.replace(/&#0?39;/g, "'")
		.replace(/&#x27;/g, "'")
		.replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(Number(n)));
}

// ---- DuckDuckGo backend (no API key) -------------------------------------
// NOTE: HTML scraping is fragile. If DDG changes their markup, switch to
// WEB_SEARCH_PROVIDER=brave (free tier: 2000 queries/month).

async function searchDuckDuckGo(query: string, signal?: AbortSignal): Promise<SearchHit[]> {
	const url = `https://html.duckduckgo.com/html/?q=${encodeURIComponent(query)}`;
	const t = withTimeout(signal, SEARCH_TIMEOUT_MS);
	try {
		const res = await fetch(url, {
			headers: {
				"User-Agent":
					"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
				Accept: "text/html",
			},
			signal: t.signal,
		});
		if (!res.ok) throw new Error(`DuckDuckGo returned HTTP ${res.status}`);
		return parseDdgHtml(await res.text());
	} finally {
		t.clear();
	}
}

function parseDdgHtml(html: string): SearchHit[] {
	const hits: SearchHit[] = [];
	const linkRe =
		/<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]*)"[^>]*>([\s\S]*?)<\/a>/g;
	let m: RegExpExecArray | null;
	while ((m = linkRe.exec(html)) && hits.length < MAX_RESULTS) {
		const url = decodeDdgHref(m[1]);
		if (!url) continue;
		const title = decodeHtmlEntities(m[2].replace(/<[^>]*>/g, "").trim());
		// Grab the snippet text between this result link and the next one.
		const rest = html.slice(m.index + m[0].length);
		const nextLink = rest.search(/<a[^>]*class="[^"]*result__a/);
		const block = nextLink === -1 ? rest : rest.slice(0, nextLink);
		const snip = block.match(
			/<a[^>]*class="[^"]*result__snippet[^"]*"[^>]*>([\s\S]*?)<\/a>/,
		);
		const snippet = snip ? decodeHtmlEntities(snip[1].replace(/<[^>]*>/g, "").trim()) : "";
		hits.push({ title, url, snippet });
	}
	return hits;
}

function decodeDdgHref(href: string): string | undefined {
	// DDG redirects through /l/?uddg=<encoded real url>
	const uddg = href.match(/[?&]uddg=([^&]+)/);
	if (uddg) {
		try {
			return decodeURIComponent(uddg[1]);
		} catch {
			return undefined;
		}
	}
	return href.startsWith("http") ? href : undefined;
}

// ---- Brave backend (free tier, needs BRAVE_API_KEY) -----------------------

async function searchBrave(query: string, apiKey: string, signal?: AbortSignal): Promise<SearchHit[]> {
	const url = `https://api.search.brave.com/res/v1/web/search?q=${encodeURIComponent(query)}&count=${MAX_RESULTS}`;
	const t = withTimeout(signal, SEARCH_TIMEOUT_MS);
	try {
		const res = await fetch(url, {
			headers: { "X-Subscription-Token": apiKey, Accept: "application/json" },
			signal: t.signal,
		});
		if (!res.ok) throw new Error(`Brave returned HTTP ${res.status}`);
		const data = (await res.json()) as any;
		const results = (data?.web?.results ?? []) as any[];
		return results.map((r) => ({
			title: r.title ?? "",
			url: r.url ?? "",
			snippet: (r.description ?? "").toString(),
		}));
	} finally {
		t.clear();
	}
}

// ---- Tavily backend (needs TAVILY_API_KEY) --------------------------------

async function searchTavily(query: string, apiKey: string, signal?: AbortSignal): Promise<SearchHit[]> {
	const t = withTimeout(signal, SEARCH_TIMEOUT_MS);
	try {
		const res = await fetch("https://api.tavily.com/search", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ api_key: apiKey, query, max_results: MAX_RESULTS }),
			signal: t.signal,
		});
		if (!res.ok) throw new Error(`Tavily returned HTTP ${res.status}`);
		const data = (await res.json()) as any;
		const results = (data?.results ?? []) as any[];
		return results.map((r) => ({
			title: r.title ?? "",
			url: r.url ?? "",
			snippet: (r.content ?? "").toString(),
		}));
	} finally {
		t.clear();
	}
}

// ---- search dispatcher ----------------------------------------------------

async function webSearch(query: string, signal?: AbortSignal): Promise<SearchHit[]> {
	const provider = (process.env.WEB_SEARCH_PROVIDER ?? "duckduckgo").toLowerCase();
	if (provider === "brave") {
		const key = process.env.BRAVE_API_KEY;
		if (!key) throw new Error("WEB_SEARCH_PROVIDER=brave but BRAVE_API_KEY is not set");
		return searchBrave(query, key, signal);
	}
	if (provider === "tavily") {
		const key = process.env.TAVILY_API_KEY;
		if (!key) throw new Error("WEB_SEARCH_PROVIDER=tavily but TAVILY_API_KEY is not set");
		return searchTavily(query, key, signal);
	}
	return searchDuckDuckGo(query, signal);
}

// ---- fetch backend (Jina AI Reader, no key) -------------------------------

async function webFetch(target: string, signal?: AbortSignal): Promise<string> {
	const url = `https://r.jina.ai/${target}`;
	const t = withTimeout(signal, FETCH_TIMEOUT_MS);
	try {
		const res = await fetch(url, {
			headers: { Accept: "text/plain", "X-Return-Format": "markdown" },
			signal: t.signal,
		});
		if (!res.ok) throw new Error(`Reader returned HTTP ${res.status}`);
		return await res.text();
	} finally {
		t.clear();
	}
}

// ---- formatting -----------------------------------------------------------

function formatResults(hits: SearchHit[]): string {
	if (hits.length === 0) return "No results found.";
	return hits
		.map((h, i) => `${i + 1}. ${h.title}\n   ${h.url}${h.snippet ? `\n   ${h.snippet}` : ""}`)
		.join("\n\n");
}

// ---- extension entry point ------------------------------------------------

export default function (pi: ExtensionAPI) {
	pi.registerTool({
		name: "web_search",
		label: "Web Search",
		description:
			"Search the web and return ranked results (title, url, snippet). Use for finding current information, documentation, facts, or anything not already in the workspace.",
		promptSnippet: "Search the web for current information",
		promptGuidelines: [
			"Use web_search when the answer requires information outside the workspace (recent events, library docs, current facts).",
			"Follow up with web_fetch on a promising URL from web_search when you need the full page content.",
		],
		parameters: Type.Object({
			query: Type.String({ description: "Search query" }),
		}),
		async execute(_id, params, signal) {
			const query = (params.query as string).trim();
			if (!query) {
				return { content: [{ type: "text", text: "Error: empty query" }], details: {}, isError: true };
			}
			try {
				const hits = await webSearch(query, signal);
				const text = formatResults(hits);
				const truncation = truncateHead(text, {
					maxLines: DEFAULT_MAX_LINES,
					maxBytes: DEFAULT_MAX_BYTES,
				});
				return {
					content: [{ type: "text", text: truncation.content }],
					details: {
						query,
						provider: process.env.WEB_SEARCH_PROVIDER ?? "duckduckgo",
						count: hits.length,
						truncation,
					},
				};
			} catch (err: any) {
				return {
					content: [{ type: "text", text: `Search failed: ${err.message}` }],
					details: { query },
					isError: true,
				};
			}
		},
		renderCall(args, theme) {
			return new Text(
				theme.fg("toolTitle", theme.bold("web_search ")) + theme.fg("accent", `"${args.query}"`),
				0,
				0,
			);
		},
		renderResult(result, { isPartial }, theme) {
			if (isPartial) return new Text(theme.fg("warning", "Searching..."), 0, 0);
			const details = result.details as any;
			const count = details?.count ?? 0;
			if (count === 0) return new Text(theme.fg("dim", "No results"), 0, 0);
			return new Text(
				theme.fg("success", `${count} results`) +
					(details?.truncation?.truncated ? theme.fg("warning", " (truncated)") : ""),
				0,
				0,
			);
		},
	});

	pi.registerTool({
		name: "web_fetch",
		label: "Web Fetch",
		description:
			"Fetch a URL and return its content as clean readable text/markdown. Use to read a web page found via web_search or any URL the user provides.",
		promptSnippet: "Fetch and read a web page",
		parameters: Type.Object({
			url: Type.String({ description: "URL to fetch (https://...)" }),
		}),
		async execute(_id, params, signal) {
			const url = (params.url as string).trim();
			if (!/^https?:\/\//i.test(url)) {
				return {
					content: [{ type: "text", text: "Error: url must start with http:// or https://" }],
					details: { url },
					isError: true,
				};
			}
			try {
				const text = await webFetch(url, signal);
				const truncation = truncateHead(text, {
					maxLines: DEFAULT_MAX_LINES,
					maxBytes: DEFAULT_MAX_BYTES,
				});
				let out = truncation.content;
				if (truncation.truncated) {
					out += `\n\n[Output truncated: showing ${truncation.outputLines} of ${truncation.totalLines} lines (${formatSize(truncation.outputBytes)} of ${formatSize(truncation.totalBytes)}).]`;
				}
				return { content: [{ type: "text", text: out }], details: { url, truncation } };
			} catch (err: any) {
				return {
					content: [{ type: "text", text: `Fetch failed: ${err.message}` }],
					details: { url },
					isError: true,
				};
			}
		},
		renderCall(args, theme) {
			return new Text(
				theme.fg("toolTitle", theme.bold("web_fetch ")) + theme.fg("accent", args.url),
				0,
				0,
			);
		},
	});
}
