const fs = require('fs');
const path = require('path');

// Read the elements data
const elementsData = JSON.parse(fs.readFileSync('elements_data.json', 'utf8'));

// Read the template
const template = fs.readFileSync('pages/element_template.html', 'utf8');

// Simple molecule structures for common compounds
const moleculeStructures = {
  'H₂O': [
    { element: 'O', x: 0, y: 0, z: 0, bonds: [1, 2] },
    { element: 'H', x: 0.96, y: 0, z: 0, bonds: [0] },
    { element: 'H', x: -0.96, y: 0, z: 0, bonds: [0] }
  ],
  'CO₂': [
    { element: 'C', x: 0, y: 0, z: 0, bonds: [1, 2] },
    { element: 'O', x: 1.16, y: 0, z: 0, bonds: [0] },
    { element: 'O', x: -1.16, y: 0, z: 0, bonds: [0] }
  ],
  'NH₃': [
    { element: 'N', x: 0, y: 0, z: 0, bonds: [1, 2, 3] },
    { element: 'H', x: 0.94, y: 0, z: 0.94, bonds: [0] },
    { element: 'H', x: -0.94, y: 0, z: 0.94, bonds: [0] },
    { element: 'H', x: 0, y: 0, z: -1.01, bonds: [0] }
  ],
  'NaCl': [
    { element: 'Na', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'Cl', x: 2.82, y: 0, z: 0, bonds: [0] }
  ],
  'MgO': [
    { element: 'Mg', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'O', x: 2.1, y: 0, z: 0, bonds: [0] }
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
  'Fe₂O₃': [
    { element: 'Fe', x: 0, y: 0, z: 0, bonds: [2, 3] },
    { element: 'Fe', x: 2.5, y: 0, z: 0, bonds: [4, 5] },
    { element: 'O', x: 1.25, y: 1.25, z: 0, bonds: [0] },
    { element: 'O', x: 1.25, y: -1.25, z: 0, bonds: [0] },
    { element: 'O', x: 3.75, y: 1.25, z: 0, bonds: [1] },
    { element: 'O', x: 3.75, y: -1.25, z: 0, bonds: [1] }
  ],
  'CuO': [
    { element: 'Cu', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'O', x: 1.85, y: 0, z: 0, bonds: [0] }
  ],
  'ZnO': [
    { element: 'Zn', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'O', x: 1.97, y: 0, z: 0, bonds: [0] }
  ],
  'XeF₂': [
    { element: 'Xe', x: 0, y: 0, z: 0, bonds: [1, 2] },
    { element: 'F', x: 1.96, y: 0, z: 0, bonds: [0] },
    { element: 'F', x: -1.96, y: 0, z: 0, bonds: [0] }
  ],
  'HF': [
    { element: 'H', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'F', x: 0.92, y: 0, z: 0, bonds: [0] }
  ],
  'NaBr': [
    { element: 'Na', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'Br', x: 2.98, y: 0, z: 0, bonds: [0] }
  ],
  'KI': [
    { element: 'K', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'I', x: 3.52, y: 0, z: 0, bonds: [0] }
  ],
  'CsCl': [
    { element: 'Cs', x: 0, y: 0, z: 0, bonds: [1] },
    { element: 'Cl', x: 3.57, y: 0, z: 0, bonds: [0] }
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
