// A serverless proxy function to handle CORS issues

export default async function handler(req, res) {
    // Only allow POST requests
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed. Only POST requests are supported.' });
    }

    try {
        // Forward the request exactly as received to the backend
        console.log('Forwarding request to backend:', JSON.stringify(req.body));

        const response = await fetch('https://umdscheduler.onrender.com/schedule', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(req.body),
        });

        // Get response data
        let data;
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            data = await response.text();
            console.log('Non-JSON response:', data);
        }

        // Return the response from the backend
        if (!response.ok) {
            return res.status(response.status).json({
                error: typeof data === 'string' ? data : 'Failed to generate schedules',
                details: typeof data === 'string' ? undefined : data
            });
        }

        // Success - return the data
        return res.status(200).json(data);
    } catch (error) {
        console.error('Proxy error:', error);
        return res.status(500).json({
            error: 'Failed to communicate with the scheduling server',
            details: error.message
        });
    }
}
