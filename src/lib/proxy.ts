/**
 * Utility to handle API connections with the backend
 */
export async function fetchWithProxy<T>(path: string, options: RequestInit = {}): Promise<T> {
    // Connect directly to the backend server
    const apiUrl = 'http://127.0.0.1:5000';
    const normalizedPath = path.startsWith('/') ? path : `/${path}`;
    const fullUrl = `${apiUrl}${normalizedPath}`;

    console.log(`Making request to backend: ${fullUrl}`);

    try {
        const response = await fetch(fullUrl, {
            ...options,
            headers: {
                ...options.headers,
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Origin': 'http://localhost:5173'
            },
            credentials: 'omit',
            mode: 'cors'
        });

        if (!response.ok) {
            let errorDetails = '';
            try {
                // Try to parse as JSON first
                const errorJson = await response.json();
                errorDetails = JSON.stringify(errorJson);
            } catch {
                // If not JSON, get as text
                errorDetails = await response.text();
            }

            throw new Error(`API Error: ${response.status} - ${errorDetails}`);
        }

        return await response.json();
    } catch (error) {
        console.error("API connection error:", error);
        throw error;
    }
}

// Make sure the export is default and named
export default { fetchWithProxy };
