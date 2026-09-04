// JavaScript implementation of the C++ straight chain parser
// Ported from aldehyde.cpp to maintain exact functionality

class StraightChainParser {
    constructor() {
        // Prefixes matching the C++ version
        this.numberPrefixes = [
            { key: "meth", value: 1 },
            { key: "eth", value: 2 },
            { key: "prop", value: 3 },
            { key: "but", value: 4 },
            { key: "pent", value: 5 },
            { key: "hex", value: 6 },
            { key: "hept", value: 7 },
            { key: "oct", value: 8 },
            { key: "non", value: 9 },
            { key: "dec", value: 10 }
        ];
    }

    // Break down string by hyphens (matching C++ BreakDownString)
    breakDownString(name) {
        let immediateString = "";
        const stringVector = [];
        
        for (const char of name) {
            if (char !== '-') {
                immediateString += char;
            } else if (immediateString.length > 0) {
                stringVector.push(immediateString);
                immediateString = "";
            }
        }
        
        return stringVector;
    }

    // Check if string contains only numbers and commas (matching C++ containsOnlyNumbersAndCommas)
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

    // Convert raw locants to raw pairs (matching C++ ConvertFromRawLocantToRawPair)
    convertFromRawLocantToRawPair(inputLocants) {
        const rawLocantPairs = [];
        let currentPair = { key: "", value: "" };
        
        for (const item of inputLocants) {
            if (this.containsOnlyNumbersAndCommas(item)) {
                currentPair.key = item;
            } else {
                currentPair.value = item;
                rawLocantPairs.push({ ...currentPair });
                currentPair = { key: "", value: "" };
            }
        }
        
        return rawLocantPairs;
    }

    // Convert string to vector of integers (matching C++ stringToVector)
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

    // Convert raw locant pairs to locant pairs (matching C++ ConvertFromRawLocantPairToLocantPair)
    convertFromRawLocantPairToLocantPair(rawLocantPairs) {
        const locantPairs = [];
        
        for (const raw of rawLocantPairs) {
            locantPairs.push({
                key: this.stringToVector(raw.key),
                value: raw.value
            });
        }
        
        return locantPairs;
    }

    // Find parent prefix numbers (matching C++ FindParentPrefix)
    findParentPrefix(rawName) {
        const foundNumbers = [];
        
        for (const prefix of this.numberPrefixes) {
            if (rawName.includes(prefix.key)) {
                foundNumbers.push(prefix.value);
            }
        }
        
        return foundNumbers;
    }

    // Check if string ends with specific characters (matching C++ endsWithNChars)
    endsWithNChars(mainStr, subStr, n) {
        if (mainStr.length >= n && subStr.length === n) {
            return mainStr.substring(mainStr.length - n) === subStr;
        }
        return false;
    }

    // Convert string names to carbon atoms and create write data (matching C++ ConvertStringNamesIntoNumberOfCarbonAtomsAndCreateWriteData)
    convertStringNamesIntoNumberOfCarbonAtomsAndCreateWriteData(parentNums, locantPairs) {
        const finalVector = [];
        
        for (let i = 0; i < locantPairs.length; i++) {
            const val = locantPairs[i].value;
            
            if (val.includes("ene") || val.includes("en")) {
                for (const pos of locantPairs[i].key) {
                    finalVector.push({
                        type: 1, // Double bond
                        bondtype: "2",
                        yposfrom: pos.toString(),
                        yposto: (pos + 1).toString()
                    });
                }
            } else if (val.includes("yne") || val.includes("yn")) {
                for (const pos of locantPairs[i].key) {
                    finalVector.push({
                        type: 2, // Triple bond
                        bondtype: "3",
                        yposfrom: pos.toString(),
                        yposto: (pos + 1).toString()
                    });
                }
            } else if (val.includes("ol") || val.includes("hydroxy")) {
                for (const pos of locantPairs[i].key) {
                    finalVector.push({
                        type: 3, // Alcohol
                        locantnumber: pos.toString(),
                        group: "alcohol"
                    });
                }
            } else if (val.includes("on") || val.includes("one") || val.includes("keto")) {
                for (const pos of locantPairs[i].key) {
                    finalVector.push({
                        type: 4, // Ketone
                        locantnumber: pos.toString(),
                        group: "ketone"
                    });
                }
            } else if (val.includes("epoxy") || val.includes("epox")) {
                finalVector.push({
                    type: 5, // Epoxide
                    group: "epoxy",
                    yposfrom: locantPairs[i].key[0].toString(),
                    yposto: (locantPairs[i].key[0] + 1).toString()
                });
            } else if (val.includes("fluoro")) {
                for (const pos of locantPairs[i].key) {
                    finalVector.push({
                        type: 6, // Fluoro
                        locantnumber: pos.toString(),
                        group: "fluoro"
                    });
                }
            } else if (val.includes("bromo")) {
                for (const pos of locantPairs[i].key) {
                    finalVector.push({
                        type: 7, // Bromo
                        locantnumber: pos.toString(),
                        group: "bromo"
                    });
                }
            } else if (val.includes("iodo")) {
                for (const pos of locantPairs[i].key) {
                    finalVector.push({
                        type: 8, // Iodo
                        locantnumber: pos.toString(),
                        group: "iodo"
                    });
                }
            } else if (val.includes("chloro")) {
                for (const pos of locantPairs[i].key) {
                    finalVector.push({
                        type: 9, // Chloro
                        locantnumber: pos.toString(),
                        group: "chloro"
                    });
                }
            } else if (val.includes("al") || val.includes("formyl") || val.includes("oxo")) {
                for (const pos of locantPairs[i].key) {
                    finalVector.push({
                        type: 10, // Aldehyde
                        locantnumber: pos.toString(),
                        group: "aldehyde"
                    });
                }
            } else {
                for (const pos of locantPairs[i].key) {
                    finalVector.push({
                        type: 0, // JSON object
                        locantnumber: pos.toString(),
                        numberofatoms: parentNums[i].toString()
                    });
                }
            }
        }

        // Add main parent chain
        if (parentNums.length > 0) {
            finalVector.push({
                type: 0,
                locantnumber: "0",
                numberofatoms: parentNums[parentNums.length - 1].toString()
            });
        }

        return finalVector;
    }

    // Write data to JSON format (matching C++ WriteDataToFile)
    writeDataToFile(data) {
        const jsonArray = [];
        
        for (let i = 0; i < data.length; i++) {
            const item = data[i];
            let obj = {};
            
            if (item.type === 0) {
                obj = {
                    locantnumber: item.locantnumber,
                    numberofatoms: item.numberofatoms
                };
            } else if (item.type === 1) {
                obj = {
                    bondtype: item.bondtype,
                    yposfrom: item.yposfrom,
                    yposto: item.yposto
                };
            } else if (item.type === 2) {
                obj = {
                    bondtype: item.bondtype,
                    yposfrom: item.yposfrom,
                    yposto: item.yposto
                };
            } else if (item.type === 3) {
                obj = {
                    locantnumber: item.locantnumber,
                    group: "alcohol"
                };
            } else if (item.type === 4) {
                obj = {
                    locantnumber: item.locantnumber,
                    group: "ketone"
                };
            } else if (item.type === 5) {
                obj = {
                    group: "epoxy",
                    yposfrom: item.yposfrom,
                    yposto: item.yposto
                };
            } else if (item.type === 6) {
                obj = {
                    locantnumber: item.locantnumber,
                    group: "fluoro"
                };
            } else if (item.type === 7) {
                obj = {
                    locantnumber: item.locantnumber,
                    group: "bromo"
                };
            } else if (item.type === 8) {
                obj = {
                    locantnumber: item.locantnumber,
                    group: "iodo"
                };
            } else if (item.type === 9) {
                obj = {
                    locantnumber: item.locantnumber,
                    group: "chloro"
                };
            } else if (item.type === 10) {
                obj = {
                    locantnumber: item.locantnumber,
                    group: "aldehyde"
                };
            }
            
            jsonArray.push(obj);
        }
        
        return jsonArray;
    }

    // Main parser function (matching C++ AldehydeParser)
    parse(name) {
        let processedName = name + "-";
        
        // Handle common names first
        if (processedName === "methanol-") {
            processedName = "methan-1-ol-";
        } else if (processedName === "ethanol-") {
            processedName = "ethan-1-ol-";
        } else if (processedName === "propanol-") {
            processedName = "propan-1-ol-";
        }
        
        // Special exceptions for methane molecules
        if (this.endsWithNChars(processedName, "methane-", 8)) {
            return this.parseMethaneVariant(processedName);
        } else if (this.endsWithNChars(processedName, "methan-1-ol-", 12)) {
            return this.parseMethaneVariant(processedName);
        } else if (this.endsWithNChars(processedName, "methan-1-one-", 13)) {
            return this.parseMethaneVariant(processedName);
        } else if (this.endsWithNChars(processedName, "methan-1-al-", 12)) {
            return this.parseMethaneVariant(processedName);
        } else {
            return this.parseStandardMolecule(processedName);
        }
    }

    parseMethaneVariant(name) {
        const brokenDown = this.breakDownString(name);
        const locants = this.convertFromRawLocantToRawPair(brokenDown);
        const rLocants = this.convertFromRawLocantPairToLocantPair(locants);
        const numbers = this.findParentPrefix(name);
        const finalObjects = this.convertStringNamesIntoNumberOfCarbonAtomsAndCreateWriteData(numbers, rLocants);
        
        // Set main chain to 1 carbon for methane variants
        finalObjects[finalObjects.length - 1].numberofatoms = "1";
        
        return this.writeDataToFile(finalObjects);
    }

    parseStandardMolecule(name) {
        const brokenDown = this.breakDownString(name);
        const locants = this.convertFromRawLocantToRawPair(brokenDown);
        const rLocants = this.convertFromRawLocantPairToLocantPair(locants);
        const numbers = this.findParentPrefix(name);
        const finalObjects = this.convertStringNamesIntoNumberOfCarbonAtomsAndCreateWriteData(numbers, rLocants);
        
        return this.writeDataToFile(finalObjects);
    }
}

// Export for use in Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StraightChainParser;
}