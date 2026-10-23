const fs = require('fs');
const path = require('path');

// Read the elements data
const elementsData = JSON.parse(fs.readFileSync('elements_data.json', 'utf8'));

// Read the template
const template = fs.readFileSync('pages/element_template.html', 'utf8');

// Molecule structures for common compounds with proper bond configurations
const moleculeStructures = {
  'H₂O': [
    { element: 'O', x: 0, y: 0, z: 0, bonds: [1, 2] },
    { element: 'H', x: 0.96, y: 0, z: 0, bonds: [0] },
    { element: 'H', x: -0.96, y: 0, z: 0, bonds: [0] }
  ],
  'CO₂': [
    { element: 'C', x: 0, y: 0, z: 0, bonds: [1, 2], bondType: 2 },
    { element: 'O', x: 1.16, y: 0, z: 0, bonds: [0] },
    { element: 'O', x: -1.16, y: 0, z: 0, bonds: [0] }
  ],
  'NH₃': [
    { element: 'N', x: 0, y: 0, z: 0, bonds: [1, 2, 3] },
    { element: 'H', x: 0.94, y: 0, z: 0.94, bonds: [0] },
    { element: 'H', x: -0.94, y: 0, z: 0.94, bonds: [0] },
    { element: 'H', x: 0, y: 0, z: -1.01, bonds: [0] }
  ],
  'LiCl': [
    { element: 'Li', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'Cl', x: 2.82, y: 0, z: 0, bonds: [0] }
  ],
  'BeO': [
    { element: 'Be', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'O', x: 1.33, y: 0, z: 0, bonds: [0] }
  ],
  'H₃BO₃': [
    { element: 'B', x: 0, y: 0, z: 0, bonds: [1, 2, 3] },
    { element: 'O', x: 1.36, y: 0, z: 0, bonds: [0, 4] },
    { element: 'O', x: -0.68, y: 1.18, z: 0, bonds: [0, 5] },
    { element: 'O', x: -0.68, y: -1.18, z: 0, bonds: [0, 6] },
    { element: 'H', x: 2.36, y: 0, z: 0, bonds: [1] },
    { element: 'H', x: -1.68, y: 1.18, z: 0, bonds: [2] },
    { element: 'H', x: -1.68, y: -1.18, z: 0, bonds: [3] }
  ],
  'NaCl': [
    { element: 'Na', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'Cl', x: 2.82, y: 0, z: 0, bonds: [0] }
  ],
  'MgO': [
    { element: 'Mg', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'O', x: 2.1, y: 0, z: 0, bonds: [0] }
  ],
  'Al₂O₃': [
    { element: 'Al', x: 0, y: 0, z: 0, bonds: [2, 3] },
    { element: 'Al', x: 2.5, y: 0, z: 0, bonds: [4, 5] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] }
  ],
  'SiO₂': [
    { element: 'Si', x: 0, y: 0, z: 0, bonds: [1, 2], bondType: 2 },
    { element: 'O', x: 1.62, y: 0, z: 0, bonds: [0] },
    { element: 'O', x: -1.62, y: 0, z: 0, bonds: [0] }
  ],
  'H₃PO₄': [
    { element: 'P', x: 0, y: 0, z: 0, bonds: [1, 2, 3, 4] },
    { element: 'O', x: 1.5, y: 0, z: 0, bonds: [0, 5], bondType: 2 },
    { element: 'O', x: -0.75, y: 1.3, z: 0, bonds: [0, 6] },
    { element: 'O', x: -0.75, y: -1.3, z: 0, bonds: [0, 7] },
    { element: 'O', x: 0, y: 0, z: 1.5, bonds: [0, 8] },
    { element: 'H', x: 2.5, y: 0, z: 0, bonds: [1] },
    { element: 'H', x: -1.75, y: 1.3, z: 0, bonds: [2] },
    { element: 'H', x: -1.75, y: -1.3, z: 0, bonds: [3] },
    { element: 'H', x: 0, y: 0, z: 2.5, bonds: [4] }
  ],
  'H₂SO₄': [
    { element: 'S', x: 0, y: 0, z: 0, bonds: [1, 2, 3, 4] },
    { element: 'O', x: 1.43, y: 0, z: 0, bonds: [0, 5], bondType: 2 },
    { element: 'O', x: -1.43, y: 0, z: 0, bonds: [0, 6], bondType: 2 },
    { element: 'O', x: 0, y: 1.43, z: 0, bonds: [0, 7] },
    { element: 'O', x: 0, y: -1.43, z: 0, bonds: [0, 8] },
    { element: 'H', x: 2.43, y: 0, z: 0, bonds: [1] },
    { element: 'H', x: -2.43, y: 0, z: 0, bonds: [2] },
    { element: 'H', x: 0, y: 2.43, z: 0, bonds: [3] },
    { element: 'H', x: 0, y: -2.43, z: 0, bonds: [4] }
  ],
  'HF': [
    { element: 'H', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'F', x: 0.92, y: 0, z: 0, bonds: [0] }
  ],
  'KCl': [
    { element: 'K', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'Cl', x: 3.14, y: 0, z: 0, bonds: [0] }
  ],
  'CaCO₃': [
    { element: 'Ca', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'C', x: 1.5, y: 0, z: 0, bonds: [0, 2, 3, 4] },
    { element: 'O', x: 2.5, y: 0, z: 0, bonds: [1] },
    { element: 'O', x: 1.5, y: 1.2, z: 0, bonds: [1] },
    { element: 'O', x: 1.5, y: -1.2, z: 0, bonds: [1] }
  ],
  'Sc₂O₃': [
    { element: 'Sc', x: 0, y: 0, z: 0, bonds: [2, 3] },
    { element: 'Sc', x: 2.5, y: 0, z: 0, bonds: [4, 5] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] }
  ],
  'TiO₂': [
    { element: 'Ti', x: 0, y: 0, z: 0, bonds: [1, 2], bondType: 2 },
    { element: 'O', x: 1.62, y: 0, z: 0, bonds: [0] },
    { element: 'O', x: -1.62, y: 0, z: 0, bonds: [0] }
  ],
  'V₂O₅': [
    { element: 'V', x: 0, y: 0, z: 0, bonds: [2, 3, 4] },
    { element: 'V', x: 2.5, y: 0, z: 0, bonds: [5, 6, 7] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 0, y: 0, z: 1.5, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] },
    { element: 'O', x: 2.5, y: 0, z: 1.5, bonds: [1] }
  ],
  'Cr₂O₃': [
    { element: 'Cr', x: 0, y: 0, z: 0, bonds: [2, 3] },
    { element: 'Cr', x: 2.5, y: 0, z: 0, bonds: [4, 5] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] }
  ],
  'MnO₂': [
    { element: 'Mn', x: 0, y: 0, z: 0, bonds: [1, 2], bondType: 2 },
    { element: 'O', x: 1.5, y: 0, z: 0, bonds: [0] },
    { element: 'O', x: -1.5, y: 0, z: 0, bonds: [0] }
  ],
  'Fe₂O₃': [
    { element: 'Fe', x: 0, y: 0, z: 0, bonds: [2, 3] },
    { element: 'Fe', x: 2.5, y: 0, z: 0, bonds: [4, 5] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] }
  ],
  'CoO': [
    { element: 'Co', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'O', x: 1.8, y: 0, z: 0, bonds: [0] }
  ],
  'NiO': [
    { element: 'Ni', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'O', x: 1.8, y: 0, z: 0, bonds: [0] }
  ],
  'CuO': [
    { element: 'Cu', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'O', x: 1.85, y: 0, z: 0, bonds: [0] }
  ],
  'ZnO': [
    { element: 'Zn', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'O', x: 1.97, y: 0, z: 0, bonds: [0] }
  ],
  'GaAs': [
    { element: 'Ga', x: 0, y: 0, z: 0, bonds: [1, 2, 3, 4] },
    { element: 'As', x: 2.44, y: 0, z: 0, bonds: [0, 5, 6, 7] },
    { element: 'Ga', x: 0, y: 2.44, z: 0, bonds: [0] },
    { element: 'Ga', x: 0, y: -2.44, z: 0, bonds: [0] },
    { element: 'Ga', x: 0, y: 0, z: 2.44, bonds: [0] },
    { element: 'As', x: 2.44, y: 2.44, z: 0, bonds: [1] },
    { element: 'As', x: 2.44, y: -2.44, z: 0, bonds: [1] },
    { element: 'As', x: 2.44, y: 0, z: 2.44, bonds: [1] }
  ],
  'GeO₂': [
    { element: 'Ge', x: 0, y: 0, z: 0, bonds: [1, 2], bondType: 2 },
    { element: 'O', x: 1.74, y: 0, z: 0, bonds: [0] },
    { element: 'O', x: -1.74, y: 0, z: 0, bonds: [0] }
  ],
  'As₂O₃': [
    { element: 'As', x: 0, y: 0, z: 0, bonds: [2, 3] },
    { element: 'As', x: 2.5, y: 0, z: 0, bonds: [4, 5] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] }
  ],
  'SeO₂': [
    { element: 'Se', x: 0, y: 0, z: 0, bonds: [1, 2], bondType: 2 },
    { element: 'O', x: 1.64, y: 0, z: 0, bonds: [0] },
    { element: 'O', x: -1.64, y: 0, z: 0, bonds: [0] }
  ],
  'NaBr': [
    { element: 'Na', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'Br', x: 2.98, y: 0, z: 0, bonds: [0] }
  ],
  'KrF₂': [
    { element: 'Kr', x: 0, y: 0, z: 0, bonds: [1, 2] },
    { element: 'F', x: 1.89, y: 0, z: 0, bonds: [0] },
    { element: 'F', x: -1.89, y: 0, z: 0, bonds: [0] }
  ],
  'RbCl': [
    { element: 'Rb', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'Cl', x: 3.2, y: 0, z: 0, bonds: [0] }
  ],
  'SrCO₃': [
    { element: 'Sr', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'C', x: 1.8, y: 0, z: 0, bonds: [0, 2, 3, 4] },
    { element: 'O', x: 2.8, y: 0, z: 0, bonds: [1] },
    { element: 'O', x: 1.8, y: 1.2, z: 0, bonds: [1] },
    { element: 'O', x: 1.8, y: -1.2, z: 0, bonds: [1] }
  ],
  'Y₂O₃': [
    { element: 'Y', x: 0, y: 0, z: 0, bonds: [2, 3] },
    { element: 'Y', x: 2.5, y: 0, z: 0, bonds: [4, 5] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] }
  ],
  'ZrO₂': [
    { element: 'Zr', x: 0, y: 0, z: 0, bonds: [1, 2], bondType: 2 },
    { element: 'O', x: 1.78, y: 0, z: 0, bonds: [0] },
    { element: 'O', x: -1.78, y: 0, z: 0, bonds: [0] }
  ],
  'Nb₂O₅': [
    { element: 'Nb', x: 0, y: 0, z: 0, bonds: [2, 3, 4] },
    { element: 'Nb', x: 2.5, y: 0, z: 0, bonds: [5, 6, 7] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 0, y: 0, z: 1.5, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] },
    { element: 'O', x: 2.5, y: 0, z: 1.5, bonds: [1] }
  ],
  'MoS₂': [
    { element: 'Mo', x: 0, y: 0, z: 0, bonds: [1, 2] },
    { element: 'S', x: 2.08, y: 0, z: 0, bonds: [0] },
    { element: 'S', x: -2.08, y: 0, z: 0, bonds: [0] }
  ],
  'RuO₂': [
    { element: 'Ru', x: 0, y: 0, z: 0, bonds: [1, 2], bondType: 2 },
    { element: 'O', x: 1.7, y: 0, z: 0, bonds: [0] },
    { element: 'O', x: -1.7, y: 0, z: 0, bonds: [0] }
  ],
  'RhCl₃': [
    { element: 'Rh', x: 0, y: 0, z: 0, bonds: [1, 2, 3] },
    { element: 'Cl', x: 1.8, y: 0, z: 0, bonds: [0] },
    { element: 'Cl', x: -0.9, y: 1.56, z: 0, bonds: [0] },
    { element: 'Cl', x: -0.9, y: -1.56, z: 0, bonds: [0] }
  ],
  'PdCl₂': [
    { element: 'Pd', x: 0, y: 0, z: 0, bonds: [1, 2] },
    { element: 'Cl', x: 1.8, y: 0, z: 0, bonds: [0] },
    { element: 'Cl', x: -1.8, y: 0, z: 0, bonds: [0] }
  ],
  'AgNO₃': [
    { element: 'Ag', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'N', x: 1.5, y: 0, z: 0, bonds: [0, 2, 3] },
    { element: 'O', x: 2.5, y: 0, z: 0, bonds: [1, 4], bondType: 2 },
    { element: 'O', x: 1.5, y: 1.2, z: 0, bonds: [1] },
    { element: 'O', x: 1.5, y: -1.2, z: 0, bonds: [1] }
  ],
  'CdS': [
    { element: 'Cd', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'S', x: 2.52, y: 0, z: 0, bonds: [0] }
  ],
  'ITO': [
    { element: 'In', x: 0, y: 0, z: 0, bonds: [1, 2] },
    { element: 'Sn', x: 2.8, y: 0, z: 0, bonds: [0, 3, 4] },
    { element: 'O', x: 3.8, y: 0, z: 0, bonds: [1] },
    { element: 'O', x: 2.8, y: 1.2, z: 0, bonds: [1] },
    { element: 'O', x: 2.8, y: -1.2, z: 0, bonds: [1] }
  ],
  'SnO₂': [
    { element: 'Sn', x: 0, y: 0, z: 0, bonds: [1, 2], bondType: 2 },
    { element: 'O', x: 1.81, y: 0, z: 0, bonds: [0] },
    { element: 'O', x: -1.81, y: 0, z: 0, bonds: [0] }
  ],
  'Sb₂O₃': [
    { element: 'Sb', x: 0, y: 0, z: 0, bonds: [2, 3] },
    { element: 'Sb', x: 2.5, y: 0, z: 0, bonds: [4, 5] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] }
  ],
  'TeO₂': [
    { element: 'Te', x: 0, y: 0, z: 0, bonds: [1, 2], bondType: 2 },
    { element: 'O', x: 1.82, y: 0, z: 0, bonds: [0] },
    { element: 'O', x: -1.82, y: 0, z: 0, bonds: [0] }
  ],
  'KI': [
    { element: 'K', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'I', x: 3.52, y: 0, z: 0, bonds: [0] }
  ],
  'XeF₂': [
    { element: 'Xe', x: 0, y: 0, z: 0, bonds: [1, 2] },
    { element: 'F', x: 1.96, y: 0, z: 0, bonds: [0] },
    { element: 'F', x: -1.96, y: 0, z: 0, bonds: [0] }
  ],
  'CsCl': [
    { element: 'Cs', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'Cl', x: 3.57, y: 0, z: 0, bonds: [0] }
  ],
  'BaSO₄': [
    { element: 'Ba', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'S', x: 1.8, y: 0, z: 0, bonds: [0, 2, 3, 4] },
    { element: 'O', x: 2.8, y: 0, z: 0, bonds: [1] },
    { element: 'O', x: 1.8, y: 1.2, z: 0, bonds: [1] },
    { element: 'O', x: 1.8, y: -1.2, z: 0, bonds: [1] },
    { element: 'O', x: 1.8, y: 0, z: 1.2, bonds: [1] }
  ],
  'La₂O₃': [
    { element: 'La', x: 0, y: 0, z: 0, bonds: [2, 3] },
    { element: 'La', x: 2.5, y: 0, z: 0, bonds: [4, 5] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] }
  ],
  'CeO₂': [
    { element: 'Ce', x: 0, y: 0, z: 0, bonds: [1, 2], bondType: 2 },
    { element: 'O', x: 1.83, y: 0, z: 0, bonds: [0] },
    { element: 'O', x: -1.83, y: 0, z: 0, bonds: [0] }
  ],
  'Pr₆O₁₁': [
    { element: 'Pr', x: 0, y: 0, z: 0, bonds: [2, 3] },
    { element: 'Pr', x: 2.5, y: 0, z: 0, bonds: [4, 5] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] }
  ],
  'Nd₂O₃': [
    { element: 'Nd', x: 0, y: 0, z: 0, bonds: [2, 3] },
    { element: 'Nd', x: 2.5, y: 0, z: 0, bonds: [4, 5] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] }
  ],
  'Sm₂O₃': [
    { element: 'Sm', x: 0, y: 0, z: 0, bonds: [2, 3] },
    { element: 'Sm', x: 2.5, y: 0, z: 0, bonds: [4, 5] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] }
  ],
  'Eu₂O₃': [
    { element: 'Eu', x: 0, y: 0, z: 0, bonds: [2, 3] },
    { element: 'Eu', x: 2.5, y: 0, z: 0, bonds: [4, 5] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] }
  ],
  'Gd₂O₃': [
    { element: 'Gd', x: 0, y: 0, z: 0, bonds: [2, 3] },
    { element: 'Gd', x: 2.5, y: 0, z: 0, bonds: [4, 5] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] }
  ],
  'Tb₄O₇': [
    { element: 'Tb', x: 0, y: 0, z: 0, bonds: [2, 3] },
    { element: 'Tb', x: 2.5, y: 0, z: 0, bonds: [4, 5] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] }
  ],
  'Dy₂O₃': [
    { element: 'Dy', x: 0, y: 0, z: 0, bonds: [2, 3] },
    { element: 'Dy', x: 2.5, y: 0, z: 0, bonds: [4, 5] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] }
  ],
  'Ho₂O₃': [
    { element: 'Ho', x: 0, y: 0, z: 0, bonds: [2, 3] },
    { element: 'Ho', x: 2.5, y: 0, z: 0, bonds: [4, 5] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] }
  ],
  'Er₂O₃': [
    { element: 'Er', x: 0, y: 0, z: 0, bonds: [2, 3] },
    { element: 'Er', x: 2.5, y: 0, z: 0, bonds: [4, 5] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] }
  ],
  'Tm₂O₃': [
    { element: 'Tm', x: 0, y: 0, z: 0, bonds: [2, 3] },
    { element: 'Tm', x: 2.5, y: 0, z: 0, bonds: [4, 5] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] }
  ],
  'Yb₂O₃': [
    { element: 'Yb', x: 0, y: 0, z: 0, bonds: [2, 3] },
    { element: 'Yb', x: 2.5, y: 0, z: 0, bonds: [4, 5] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] }
  ],
  'Lu₂O₃': [
    { element: 'Lu', x: 0, y: 0, z: 0, bonds: [2, 3] },
    { element: 'Lu', x: 2.5, y: 0, z: 0, bonds: [4, 5] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] }
  ],
  'HfO₂': [
    { element: 'Hf', x: 0, y: 0, z: 0, bonds: [1, 2], bondType: 2 },
    { element: 'O', x: 1.78, y: 0, z: 0, bonds: [0] },
    { element: 'O', x: -1.78, y: 0, z: 0, bonds: [0] }
  ],
  'Ta₂O₅': [
    { element: 'Ta', x: 0, y: 0, z: 0, bonds: [2, 3, 4] },
    { element: 'Ta', x: 2.5, y: 0, z: 0, bonds: [5, 6, 7] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 0, y: 0, z: 1.5, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] },
    { element: 'O', x: 2.5, y: 0, z: 1.5, bonds: [1] }
  ],
  'WO₃': [
    { element: 'W', x: 0, y: 0, z: 0, bonds: [1, 2, 3] },
    { element: 'O', x: 1.74, y: 0, z: 0, bonds: [0], bondType: 2 },
    { element: 'O', x: -0.87, y: 1.51, z: 0, bonds: [0], bondType: 2 },
    { element: 'O', x: -0.87, y: -1.51, z: 0, bonds: [0], bondType: 2 }
  ],
  'Re₂O₇': [
    { element: 'Re', x: 0, y: 0, z: 0, bonds: [2, 3, 4] },
    { element: 'Re', x: 2.5, y: 0, z: 0, bonds: [5, 6, 7] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 0, y: 0, z: 1.5, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] },
    { element: 'O', x: 2.5, y: 0, z: 1.5, bonds: [1] }
  ],
  'OsO₄': [
    { element: 'Os', x: 0, y: 0, z: 0, bonds: [1, 2, 3, 4] },
    { element: 'O', x: 1.71, y: 0, z: 0, bonds: [0], bondType: 2 },
    { element: 'O', x: -1.71, y: 0, z: 0, bonds: [0], bondType: 2 },
    { element: 'O', x: 0, y: 1.71, z: 0, bonds: [0], bondType: 2 },
    { element: 'O', x: 0, y: 0, z: 1.71, bonds: [0], bondType: 2 }
  ],
  'IrO₂': [
    { element: 'Ir', x: 0, y: 0, z: 0, bonds: [1, 2], bondType: 2 },
    { element: 'O', x: 1.71, y: 0, z: 0, bonds: [0] },
    { element: 'O', x: -1.71, y: 0, z: 0, bonds: [0] }
  ],
  'PtCl₄': [
    { element: 'Pt', x: 0, y: 0, z: 0, bonds: [1, 2, 3, 4] },
    { element: 'Cl', x: 1.8, y: 0, z: 0, bonds: [0] },
    { element: 'Cl', x: -1.8, y: 0, z: 0, bonds: [0] },
    { element: 'Cl', x: 0, y: 1.8, z: 0, bonds: [0] },
    { element: 'Cl', x: 0, y: 0, z: 1.8, bonds: [0] }
  ],
  'AuCl₃': [
    { element: 'Au', x: 0, y: 0, z: 0, bonds: [1, 2, 3] },
    { element: 'Cl', x: 1.8, y: 0, z: 0, bonds: [0] },
    { element: 'Cl', x: -0.9, y: 1.56, z: 0, bonds: [0] },
    { element: 'Cl', x: -0.9, y: -1.56, z: 0, bonds: [0] }
  ],
  'HgO': [
    { element: 'Hg', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'O', x: 2.0, y: 0, z: 0, bonds: [0] }
  ],
  'Tl₂SO₄': [
    { element: 'Tl', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'S', x: 1.8, y: 0, z: 0, bonds: [0, 2, 3, 4] },
    { element: 'O', x: 2.8, y: 0, z: 0, bonds: [1] },
    { element: 'O', x: 1.8, y: 1.2, z: 0, bonds: [1] },
    { element: 'O', x: 1.8, y: -1.2, z: 0, bonds: [1] },
    { element: 'Tl', x: 1.8, y: 0, z: 2.5, bonds: [1] }
  ],
  'PbO': [
    { element: 'Pb', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'O', x: 2.2, y: 0, z: 0, bonds: [0] }
  ],
  'Bi₂O₃': [
    { element: 'Bi', x: 0, y: 0, z: 0, bonds: [2, 3] },
    { element: 'Bi', x: 2.5, y: 0, z: 0, bonds: [4, 5] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] }
  ],
  'PoO₂': [
    { element: 'Po', x: 0, y: 0, z: 0, bonds: [1, 2], bondType: 2 },
    { element: 'O', x: 1.8, y: 0, z: 0, bonds: [0] },
    { element: 'O', x: -1.8, y: 0, z: 0, bonds: [0] }
  ],
  'ThO₂': [
    { element: 'Th', x: 0, y: 0, z: 0, bonds: [1, 2], bondType: 2 },
    { element: 'O', x: 1.79, y: 0, z: 0, bonds: [0] },
    { element: 'O', x: -1.79, y: 0, z: 0, bonds: [0] }
  ],
  'Pa₂O₅': [
    { element: 'Pa', x: 0, y: 0, z: 0, bonds: [2, 3, 4] },
    { element: 'Pa', x: 2.5, y: 0, z: 0, bonds: [5, 6, 7] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 0, y: 0, z: 1.5, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] },
    { element: 'O', x: 2.5, y: 0, z: 1.5, bonds: [1] }
  ],
  'UO₂': [
    { element: 'U', x: 0, y: 0, z: 0, bonds: [1, 2], bondType: 2 },
    { element: 'O', x: 1.79, y: 0, z: 0, bonds: [0] },
    { element: 'O', x: -1.79, y: 0, z: 0, bonds: [0] }
  ],
  'NpO₂': [
    { element: 'Np', x: 0, y: 0, z: 0, bonds: [1, 2], bondType: 2 },
    { element: 'O', x: 1.79, y: 0, z: 0, bonds: [0] },
    { element: 'O', x: -1.79, y: 0, z: 0, bonds: [0] }
  ],
  'PuO₂': [
    { element: 'Pu', x: 0, y: 0, z: 0, bonds: [1, 2], bondType: 2 },
    { element: 'O', x: 1.79, y: 0, z: 0, bonds: [0] },
    { element: 'O', x: -1.79, y: 0, z: 0, bonds: [0] }
  ],
  'AmO₂': [
    { element: 'Am', x: 0, y: 0, z: 0, bonds: [1, 2], bondType: 2 },
    { element: 'O', x: 1.79, y: 0, z: 0, bonds: [0] },
    { element: 'O', x: -1.79, y: 0, z: 0, bonds: [0] }
  ],
  'CmO₂': [
    { element: 'Cm', x: 0, y: 0, z: 0, bonds: [1, 2], bondType: 2 },
    { element: 'O', x: 1.79, y: 0, z: 0, bonds: [0] },
    { element: 'O', x: -1.79, y: 0, z: 0, bonds: [0] }
  ],
  'BkO₂': [
    { element: 'Bk', x: 0, y: 0, z: 0, bonds: [1, 2], bondType: 2 },
    { element: 'O', x: 1.79, y: 0, z: 0, bonds: [0] },
    { element: 'O', x: -1.79, y: 0, z: 0, bonds: [0] }
  ],
  'CfCl₃': [
    { element: 'Cf', x: 0, y: 0, z: 0, bonds: [1, 2, 3] },
    { element: 'Cl', x: 1.8, y: 0, z: 0, bonds: [0] },
    { element: 'Cl', x: -0.9, y: 1.56, z: 0, bonds: [0] },
    { element: 'Cl', x: -0.9, y: -1.56, z: 0, bonds: [0] }
  ],
  'Es₂O₃': [
    { element: 'Es', x: 0, y: 0, z: 0, bonds: [2, 3] },
    { element: 'Es', x: 2.5, y: 0, z: 0, bonds: [4, 5] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] }
  ],
  'FmCl₃': [
    { element: 'Fm', x: 0, y: 0, z: 0, bonds: [1, 2, 3] },
    { element: 'Cl', x: 1.8, y: 0, z: 0, bonds: [0] },
    { element: 'Cl', x: -0.9, y: 1.56, z: 0, bonds: [0] },
    { element: 'Cl', x: -0.9, y: -1.56, z: 0, bonds: [0] }
  ],
  'MdCl₃': [
    { element: 'Md', x: 0, y: 0, z: 0, bonds: [1, 2, 3] },
    { element: 'Cl', x: 1.8, y: 0, z: 0, bonds: [0] },
    { element: 'Cl', x: -0.9, y: 1.56, z: 0, bonds: [0] },
    { element: 'Cl', x: -0.9, y: -1.56, z: 0, bonds: [0] }
  ],
  'NoCl₃': [
    { element: 'No', x: 0, y: 0, z: 0, bonds: [1, 2, 3] },
    { element: 'Cl', x: 1.8, y: 0, z: 0, bonds: [0] },
    { element: 'Cl', x: -0.9, y: 1.56, z: 0, bonds: [0] },
    { element: 'Cl', x: -0.9, y: -1.56, z: 0, bonds: [0] }
  ],
  'LrCl₃': [
    { element: 'Lr', x: 0, y: 0, z: 0, bonds: [1, 2, 3] },
    { element: 'Cl', x: 1.8, y: 0, z: 0, bonds: [0] },
    { element: 'Cl', x: -0.9, y: 1.56, z: 0, bonds: [0] },
    { element: 'Cl', x: -0.9, y: -1.56, z: 0, bonds: [0] }
  ],
  'default': [
    { element: 'X', x: 0, y: 0, z: 0, bonds: [] }
  ]
};

// Generate pages for each element
Object.keys(elementsData).forEach(atomicNumber => {
  const element = elementsData[atomicNumber];
  
  // Get molecule structure or use default
  const moleculeStructure = moleculeStructures[element.molecule_formula] || moleculeStructures['default'];
  
  // Replace placeholders in template
  let pageContent = template
    .replace(/ELEMENT_NAME/g, element.name)
    .replace(/ELEMENT_SYMBOL/g, element.symbol)
    .replace(/ATOMIC_NUMBER/g, element.atomic_number)
    .replace(/GROUP/g, element.group)
    .replace(/PERIOD/g, element.period)
    .replace(/CATEGORY/g, element.category)
    .replace(/MOLECULE_NAME/g, element.molecule_name)
    .replace(/MOLECULE_FORMULA/g, element.molecule_formula)
    .replace(/MOLECULE_DESCRIPTION/g, element.molecule_description)
    .replace(/ELEMENT_FACTS/g, element.element_facts)
    .replace(/MOLECULE_DATA/g, JSON.stringify(moleculeStructure));
  
  // Add unstable warning if needed
  if (element.is_unstable) {
    const warningSection = `
    <div class="unstable-warning">
      <p><strong>⚠️ Unstable Element:</strong> ${element.molecule_description}</p>
    </div>`;
    pageContent = pageContent.replace(
      /<div class="info-section">/,
      warningSection + '\n                <div class="info-section">'
    );
    
    // Hide renderer for unstable elements
    pageContent = pageContent.replace(
      /buildMolecule\(\);/,
      '// No molecule to render for unstable elements\n        // moleculeGroup.visible = false;'
    );
  }
  
  // Write the file
  const filename = `pages/element_${atomicNumber}.html`;
  fs.writeFileSync(filename, pageContent);
  console.log(`Generated ${filename}`);
});

console.log('All element pages generated successfully!');
