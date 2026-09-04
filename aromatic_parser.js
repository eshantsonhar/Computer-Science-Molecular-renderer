// JavaScript implementation of the C++ aromatic parser
// Ported from aromatic_parser.cpp to maintain exact functionality

class AromaticParser {
    constructor() {
        // IUPAC Substituent database
        this.substituentMap = {
            "methyl": "methyl",
            "ethyl": "ethyl",
            "propyl": "propyl",
            "butyl": "butyl",
            "pentyl": "pentyl",
            "hexyl": "hexyl",
            "heptyl": "heptyl",
            "octyl": "octyl",
            "nonyl": "nonyl",
            "decyl": "decyl",
            "fluoro": "fluoro",
            "chloro": "chloro",
            "bromo": "bromo",
            "iodo": "iodo",
            "hydroxy": "hydroxy",
            "methoxy": "methoxy",
            "ethoxy": "ethoxy",
            "nitro": "nitro",
            "cyano": "cyano",
            "amino": "amino",
            "dimethylamino": "dimethylamino",
            "phenyl": "phenyl",
            "bromophenyl": "bromophenyl",
            "chlorophenyl": "chlorophenyl",
            "methylphenyl": "methylphenyl",
            "carboxylic_acid": "carboxylic_acid",
            "aldehyde": "aldehyde",
            "ketone": "ketone",
            "thiol": "thiol",
            "carboxyl": "carboxyl"
        };

        // IUPAC Parent Hydride Database
        this.parentHydrideDatabase = {
            "benzene": "benzene",
            "naphthalene": "naphthalene",
            "anthracene": "anthracene",
            "phenanthrene": "phenanthrene",
            "furan": "furan",
            "thiophene": "thiophene",
            "pyrrole": "pyrrole",
            "oxazole": "oxazole",
            "thiazole": "thiazole",
            "imidazole": "imidazole",
            "pyrazole": "pyrazole",
            "isoxazole": "isoxazole",
            "isothiazole": "isothiazole",
            "pyridine": "pyridine",
            "pyrimidine": "pyrimidine",
            "pyrazine": "pyrazine",
            "pyridazine": "pyridazine",
            "azine": "azine",
            "oxazine": "oxazine",
            "thiazine": "thiazine",
            "azepine": "azepine",
            "oxepine": "oxepine",
            "thiepine": "thiepine",
            "quinoline": "quinoline",
            "isoquinoline": "isoquinoline",
            "acridine": "acridine",
            "phenanthridine": "phenanthridine",
            "naphthyridine": "naphthyridine",
            "quinazoline": "quinazoline",
            "quinoxaline": "quinoxaline",
            "cinnoline": "cinnoline",
            "indole": "indole",
            "isoindole": "isoindole",
            "benzofuran": "benzofuran",
            "benzothiophene": "benzothiophene",
            "indolizine": "indolizine",
            "purine": "purine",
            "biphenylene": "biphenylene",
            "biphenyl": "biphenyl",
            "bipyridine": "bipyridine",
            "bithiophene": "bithiophene",
            "biquinoline": "biquinoline",
            "bithiazole": "bithiazole",
            "furopyridine": "furopyridine",
            "furothiophene": "furothiophene",
            "benzimidazole": "benzimidazole",
            "benzoxazole": "benzoxazole",
            "benzothiazole": "benzothiazole",
            "phenol": "phenol",
            "aniline": "aniline",
            "toluene": "toluene",
            "benzaldehyde": "benzaldehyde",
            "benzonitrile": "benzonitrile",
            "pyridinium": "pyridinium",
            "pyridin-1-ium": "pyridinium",
            "quinolinium": "quinolinium",
            "imidazolium": "imidazolium",
            "imidazol-3-ium": "imidazolium",
            "thiazolium": "thiazolium"
        };
    }

    // Helper function to check if string contains only numbers and commas
    containsOnlyNumbersAndCommas(str) {
        if (str.length === 0) return false;
        for (const char of str) {
            if (!this.isDigit(char) && char !== ',') return false;
        }
        return true;
    }

    isDigit(char) {
        return char >= '0' && char <= '9';
    }

    // Helper function to convert comma-separated string to array of integers
    stringToVector(s) {
        const result = [];
        const segments = s.split(',');
        
        for (const segment of segments) {
            if (segment.trim().length > 0) {
                const num = parseInt(segment.trim(), 10);
                if (!isNaN(num)) {
                    result.push(num);
                }
            }
        }
        
        return result;
    }

    // Find parent hydride in the name
    findParentHydride(name) {
        // Sort by length (longest first) to match complex names first
        const sortedParents = Object.keys(this.parentHydrideDatabase).sort((a, b) => b.length - a.length);
        
        for (const parent of sortedParents) {
            if (name.includes(parent)) {
                return parent;
            }
        }
        return "benzene"; // Default fallback
    }

    // Parse substituents from the name
    parseSubstituents(name, parentHydride) {
        const substituents = [];
        const nameWithoutParent = name.replace(parentHydride, "").trim();
        
        // If there's nothing left after removing parent, no substituents
        if (nameWithoutParent.length === 0) {
            return substituents;
        }
        
        // Split by hyphens to get substituent blocks
        const blocks = nameWithoutParent.split('-').filter(block => block.length > 0);
        
        let currentLocants = [];
        
        for (const block of blocks) {
            if (this.containsOnlyNumbersAndCommas(block)) {
                // This is a locant or set of locants
                currentLocants = this.stringToVector(block);
            } else {
                // This should be a substituent type
                for (const sub in this.substituentMap) {
                    if (block.includes(sub)) {
                        // Only process if we have explicit locants
                        if (currentLocants.length > 0) {
                            // Handle multiplicative prefixes (di, tri, tetra, etc.)
                            const multiPrefix = block.match(/^(di|tri|tetra|penta|hexa)(.*)/);
                            if (multiPrefix) {
                                // If we have multiple locants, map them to the substituent
                                for (let i = 0; i < currentLocants.length; i++) {
                                    substituents.push({
                                        position: currentLocants[i],
                                        type: this.substituentMap[sub]
                                    });
                                }
                            } else if (currentLocants.length > 1) {
                                // Multiple locants without explicit multiplicative prefix
                                for (const locant of currentLocants) {
                                    substituents.push({
                                        position: locant,
                                        type: this.substituentMap[sub]
                                    });
                                }
                            } else {
                                // Single substituent
                                for (const locant of currentLocants) {
                                    substituents.push({
                                        position: locant,
                                        type: this.substituentMap[sub]
                                    });
                                }
                            }
                        }
                        
                        currentLocants = []; // Reset for next substituent
                        break;
                    }
                }
            }
        }
        
        return substituents;
    }

    // Main parse function
    parse(name) {
        const parentHydride = this.findParentHydride(name);
        
        // Special handling: if the name exactly matches a parent hydride in the database
        // (including functionalized ones like phenol, aniline, toluene, benzaldehyde)
        // return it as the parent with empty substituents
        if (this.parentHydrideDatabase[name] === name) {
            return {
                type: name,
                substituents: []
            };
        }
        
        const substituents = this.parseSubstituents(name, parentHydride);
        
        // Return in the same format as C++ parser
        return {
            type: parentHydride,
            substituents: substituents.map(sub => ({
                position: sub.position,
                type: sub.type
            }))
        };
    }
}

// Export for use in Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AromaticParser;
}