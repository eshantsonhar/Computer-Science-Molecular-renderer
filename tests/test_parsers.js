const assert = require('node:assert/strict');

const AromaticParser = require('../aromatic_parser');
const StraightChainParser = require('../straight_chain_parser');

const chainParser = new StraightChainParser();
assert.deepEqual(chainParser.parse('ethanol'), [
    { locantnumber: '1', group: 'alcohol' },
    { locantnumber: '0', numberofatoms: '2' }
]);
assert.deepEqual(chainParser.parse('prop-1-ene'), [
    { bondtype: '2', yposfrom: '1', yposto: '2' },
    { locantnumber: '0', numberofatoms: '3' }
]);
assert.deepEqual(chainParser.parse('2-methylpropane'), [
    { locantnumber: '2', numberofatoms: '1' },
    { locantnumber: '0', numberofatoms: '3' }
]);

const aromaticParser = new AromaticParser();
for (const name of ['chlorobenzene', 'nitrobenzene', 'benzaldehyde', 'benzonitrile']) {
    assert.equal(aromaticParser.parse(name).type, name);
}
