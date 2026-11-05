(function (global) {
    global.requestMolecularGeometry = async function (payload) {
        const response = await fetch('/api/geometry', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        let result;
        try {
            result = await response.json();
        } catch (error) {
            throw new Error(`Geometry service returned invalid JSON: ${error.message}`);
        }

        if (!response.ok) {
            throw new Error(result.error || `Geometry service failed (${response.status}).`);
        }
        if (!Array.isArray(result.atoms) || !Array.isArray(result.bonds) || !result.metadata) {
            throw new Error('Geometry service returned an incomplete molecular structure.');
        }
        return result;
    };
})(window);
