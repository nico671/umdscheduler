function trimTrailingSlash(url) {
    return String(url).replace(/\/+$/, "");
}

function parseBackendBaseUrl(rawValue) {
    const fallback = "http://localhost:8000";
    const source = rawValue && String(rawValue).trim().length > 0 ? rawValue : fallback;

    try {
        const parsed = new URL(source);
        if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
            throw new Error("must use http or https protocol");
        }
        return trimTrailingSlash(parsed.toString());
    } catch (error) {
        const detail = error instanceof Error ? error.message : "invalid URL";
        throw new Error(
            `Invalid VITE_API_BASE_URL value '${source}': ${detail}. ` +
            "Set VITE_API_BASE_URL to a valid backend base URL.",
        );
    }
}

const env = typeof import.meta !== "undefined" ? import.meta.env ?? {} : {};

export const runtimeConfig = {
    backendBaseUrl: parseBackendBaseUrl(env.VITE_API_BASE_URL),
};