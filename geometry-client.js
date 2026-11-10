(function (global) {
    global.requestMolecularGeometry = async function (payload) {
        let response;
        try {
            response = await fetch('/api/geometry', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        } catch (error) {
            if (error instanceof TypeError) {
                throw new Error('Could not reach the project geometry function at /api/geometry. Run the Vercel development server or check the deployment.');
            }
            throw error;
        }

        const contentType = response.headers.get('content-type') || 'unknown content type';
        const responseText = await response.text();
        if (!contentType.toLowerCase().includes('application/json')) {
            throw new Error(
                `Geometry function returned HTTP ${response.status} with ${contentType}, not JSON. ` +
                'The site may be running without its project API functions, or the deployment route may be misconfigured.'
            );
        }

        let result;
        try {
            result = JSON.parse(responseText);
        } catch {
            throw new Error(`Geometry function returned malformed JSON (HTTP ${response.status}).`);
        }

        if (!result || typeof result !== 'object' || Array.isArray(result)) {
            throw new Error(`Geometry function returned an invalid response shape (HTTP ${response.status}).`);
        }
        if (!response.ok) {
            const error = result.error;
            const message = typeof error === 'string' ? error : error?.message;
            const code = typeof error === 'object' ? error?.code : null;
            const requestId = result.requestId || (typeof error === 'object' ? error?.requestId : null);
            const context = [code, requestId && `request ${requestId}`].filter(Boolean).join('; ');
            throw new Error(
                `${message || `Geometry function failed (HTTP ${response.status}).`}` +
                (context ? ` (${context})` : '')
            );
        }
        if (!Array.isArray(result.atoms) || !Array.isArray(result.bonds) || !result.metadata) {
            throw new Error('Geometry function returned an incomplete molecular structure.');
        }
        if (typeof result.depictionSvg !== 'string' || !result.depictionSvg.includes('<svg')) {
            throw new Error('Geometry function returned no molecular structure depiction.');
        }
        return result;
    };
})(window);
