/* ============================================
   Molam - Molecules And Metabolism
   3D Protein Ribbon Viewer Engine
   ============================================
   
   Requires: Three.js, OrbitControls
   
   Classes:
   - PDBParser: Parse PDB files
   - ArcMath: Circular arc computations
   - LocalFrameComputer: Compute Frenet frames
   - BiarcSegment3D: Biarc interpolation
   - RibbonGeometryBuilder: Build ribbon mesh
   - AtomRenderer: Instanced all-atom visualization
   - MolamScene: Three.js scene management
   - MolamApp: Main application
*/

// ============================================================
// CPK ATOM DATA (Colors & Van der Waals Radii)
// ============================================================

const CPK_ATOM_DATA = {
  'H': { color: 0xFFFFFF, radius: 1.20, atomicNumber: 1 },   // Hydrogen - White
  'C': { color: 0x909090, radius: 1.70, atomicNumber: 6 },   // Carbon - Gray
  'N': { color: 0x3050F8, radius: 1.55, atomicNumber: 7 },   // Nitrogen - Blue
  'O': { color: 0xFF0D0D, radius: 1.52, atomicNumber: 8 },   // Oxygen - Red
  'F': { color: 0x90E050, radius: 1.47, atomicNumber: 9 },   // Fluorine - Green
  'P': { color: 0xFF8000, radius: 1.80, atomicNumber: 15 },  // Phosphorus - Orange
  'S': { color: 0xFFFF30, radius: 1.80, atomicNumber: 16 },  // Sulfur - Yellow
  'CL': { color: 0x1FF01F, radius: 1.75, atomicNumber: 17 }, // Chlorine - Green
  'CA': { color: 0x3DFF00, radius: 2.00, atomicNumber: 20 }, // Calcium - Green
  'FE': { color: 0xE06633, radius: 2.00, atomicNumber: 26 }, // Iron - Orange
  'BR': { color: 0xA62929, radius: 1.85, atomicNumber: 35 }, // Bromine - Dark Red
  'I': { color: 0x940094, radius: 1.98, atomicNumber: 53 },  // Iodine - Purple
  'DEFAULT': { color: 0xFF1493, radius: 1.70, atomicNumber: 6 } // Unknown - Pink
};

const BOND_GREY = 0xC0C0C0; // Lighter grey than carbon for blending
const BOND_RING_PINK = 0xFF1493; // Neon pink for ring bonds (trumps grey)

// ============================================================
// VIEW PRESETS
// ============================================================

const MOLAM_PRESETS = {
  'Standard': {
    width: 0.35,
    thickness: 0.15,
    nodeScale: 0.5,
    controlNodeSize: 0,
    jointNodeSize: 0,
    smoothing: 0.5,
    controlNodeSmoothing: 0.5,
    normalIndicatorSize: 0,
    atomScale: 0.75,
    atomOpacity: 0.46,
    atomRangeStart: 0,
    atomRangeEnd: 100,
    bondOpacity: 0,
    bondRadius: 1.0,
    bondHalfColor: 0.5,
    bondGreyBlend: 0,
    bondRingPink: 0
  },
  'Ball and Stick': {
    width: 0,
    thickness: 0,
    nodeScale: 0,
    controlNodeSize: 0,
    jointNodeSize: 0,
    smoothing: 0.5,
    controlNodeSmoothing: 0.5,
    normalIndicatorSize: 0,
    atomScale: 0.75,
    atomOpacity: 1,
    atomRangeStart: 0,
    atomRangeEnd: 100,
    bondOpacity: 1,
    bondRadius: 1.0,
    bondHalfColor: 0.5,
    bondGreyBlend: 0,
    bondRingPink: 0
  },
  'All Atoms': {
    width: 0,
    thickness: 0,
    nodeScale: 0,
    controlNodeSize: 0,
    jointNodeSize: 0,
    smoothing: 0.5,
    controlNodeSmoothing: 0.5,
    normalIndicatorSize: 0,
    atomScale: 1.5,
    atomOpacity: 1,
    atomRangeStart: 0,
    atomRangeEnd: 100,
    bondOpacity: 0,
    bondRadius: 1.0,
    bondHalfColor: 0.5,
    bondGreyBlend: 0,
    bondRingPink: 0
  },
  'Ribbon + Atoms': {
    width: 0.35,
    thickness: 0.15,
    nodeScale: 0,
    controlNodeSize: 0,
    jointNodeSize: 0,
    smoothing: 0.5,
    controlNodeSmoothing: 0.5,
    normalIndicatorSize: 0,
    atomScale: 1.2,
    atomOpacity: 0.3,
    atomRangeStart: 0,
    atomRangeEnd: 100,
    bondOpacity: 0,
    bondRadius: 1.0,
    bondHalfColor: 0.5,
    bondGreyBlend: 0,
    bondRingPink: 0
  },
  'Spheres': {
    width: 0,
    thickness: 0,
    nodeScale: 0.66,
    controlNodeSize: 1,
    jointNodeSize: 0.8,
    smoothing: 0.5,
    controlNodeSmoothing: 0.5,
    normalIndicatorSize: 0,
    atomOpacity: 0,
    atomRangeStart: 0,
    atomRangeEnd: 100,
    bondOpacity: 0,
    bondRadius: 1.0,
    bondHalfColor: 0.5,
    bondGreyBlend: 0,
    bondRingPink: 0
  },
  'Beads': {
    width: 0.05,
    thickness: 0.05,
    nodeScale: 0.5,
    controlNodeSize: 0.5,
    jointNodeSize: 0.5,
    smoothing: 0.5,
    controlNodeSmoothing: 0.5,
    normalIndicatorSize: 0,
    atomOpacity: 0,
    atomRangeStart: 0,
    atomRangeEnd: 100,
    bondOpacity: 0,
    bondRadius: 1.0,
    bondHalfColor: 0.5,
    bondGreyBlend: 0,
    bondRingPink: 0
  },  
  'Bootlace': {
    width: 0.05,
    thickness: 0.05,
    nodeScale: 0.0,
    controlNodeSize: 0.5,
    jointNodeSize: 0.5,
    smoothing: 0.5,
    controlNodeSmoothing: 0.5,
    normalIndicatorSize: 0,
    atomOpacity: 0,
    atomRangeStart: 0,
    atomRangeEnd: 100,
    bondOpacity: 0,
    bondRadius: 1.0,
    bondHalfColor: 0.5,
    bondGreyBlend: 0,
    bondRingPink: 0
  },  
  'Bendix': {
    width: 0.4,
    thickness: 0.10,
    nodeScale: 0.5,
    controlNodeSize: 0.0,
    jointNodeSize: 0.0,
    smoothing: 0.8,
    controlNodeSmoothing: 0.8,
    normalIndicatorSize: 0,
    atomOpacity: 0,
    atomRangeStart: 0,
    atomRangeEnd: 100,
    bondOpacity: 0,
    bondRadius: 1.0,
    bondHalfColor: 0.5,
    bondGreyBlend: 0,
    bondRingPink: 0
  },
  'Bumpy': {
    width: 0.35,
    thickness: 0.15,
    nodeScale: 0.5,
    controlNodeSize: 0.5,
    jointNodeSize: 0.5,
    smoothing: 0.0,
    controlNodeSmoothing: 0.0,
    normalIndicatorSize: 0,
    atomOpacity: 0,
    atomRangeStart: 0,
    atomRangeEnd: 100,
    bondOpacity: 0,
    bondRadius: 1.0,
    bondHalfColor: 0.5,
    bondGreyBlend: 0,
    bondRingPink: 0
  },
  'Draggable': {
    width: 0.35,
    thickness: 0.15,
    nodeScale: 0.5,
    controlNodeSize: 0.5,
    jointNodeSize: 0.5,
    smoothing: 0.0,
    controlNodeSmoothing: 0.0,
    normalIndicatorSize: 0,
    atomOpacity: 0,
    atomRangeStart: 0,
    atomRangeEnd: 100,
    bondOpacity: 0,
    bondRadius: 1.0,
    bondHalfColor: 0.5,
    bondGreyBlend: 0,
    bondRingPink: 0
  },
  'Studded': {
    width: 0.35,
    thickness: 0.15,
    nodeScale: 0.5,
    controlNodeSize: 0.5,
    jointNodeSize: 0.5,
    smoothing: 0.5,
    controlNodeSmoothing: 0.5,
    normalIndicatorSize: 0,
    atomOpacity: 0,
    atomRangeStart: 0,
    atomRangeEnd: 100,
    bondOpacity: 0,
    bondRadius: 1.0,
    bondHalfColor: 0.5,
    bondGreyBlend: 0,
    bondRingPink: 0
  }  
};

// ============================================================
// PDB PARSER CLASS
// ============================================================

class PDBParser {
  static parse(pdbContent, includeAllAtoms = false) {
    const lines = pdbContent.split('\n');
    const chains = new Map();
    const allAtoms = []; // All atoms for visualization
    let title = '';
    
    for (const line of lines) {
      if (line.startsWith('TITLE')) {
        title += line.substring(10).trim() + ' ';
      }
      
      if (line.startsWith('ATOM') || line.startsWith('HETATM')) {
        const atom = this.parseAtomLine(line);
        if (!atom) continue;
        
        // Store all atoms if requested
        if (includeAllAtoms) {
          allAtoms.push(atom);
        }
        
        // Store backbone atoms for ribbon
        if (this.isBackboneAtom(atom)) {
          if (!chains.has(atom.chainId)) {
            chains.set(atom.chainId, []);
          }
          chains.get(atom.chainId).push(atom);
        }
      }
    }
    
    return {
      title: title.trim(),
      chains: chains,
      allAtoms: allAtoms,
      totalAtoms: Array.from(chains.values()).reduce((sum, c) => sum + c.length, 0),
      totalAllAtoms: allAtoms.length
    };
  }
  
  static parseAtomLine(line) {
    if (line.length < 54) return null;
    
    try {
      return {
        serial: parseInt(line.substring(6, 11).trim()),
        name: line.substring(12, 16).trim(),
        altLoc: line.substring(16, 17).trim(),
        resName: line.substring(17, 20).trim(),
        chainId: line.substring(21, 22).trim() || 'A',
        resSeq: parseInt(line.substring(22, 26).trim()),
        x: parseFloat(line.substring(30, 38).trim()),
        y: parseFloat(line.substring(38, 46).trim()),
        z: parseFloat(line.substring(46, 54).trim()),
        element: line.length >= 78 ? line.substring(76, 78).trim() : this.guessElement(line.substring(12, 16).trim())
      };
    } catch (e) {
      return null;
    }
  }
  
  static guessElement(atomName) {
    // Try to extract element from atom name
    const clean = atomName.replace(/[0-9'"]/g, '').trim();
    if (clean.length === 0) return 'C';
    
    // Common patterns: CA, CB, N, O, etc.
    const firstChar = clean[0].toUpperCase();
    const firstTwo = clean.substring(0, 2).toUpperCase();
    
    // Check two-letter elements first
    if (CPK_ATOM_DATA[firstTwo]) return firstTwo;
    if (CPK_ATOM_DATA[firstChar]) return firstChar;
    
    return 'C'; // Default to carbon
  }
  
  static isBackboneAtom(atom) {
    return atom.name === 'CA' && (!atom.altLoc || atom.altLoc === 'A');
  }
  
  static extractChainsCoords(structure, THREE) {
    const chainsCoords = new Map();
    
    for (const [cId, atoms] of structure.chains) {
      atoms.sort((a, b) => a.resSeq - b.resSeq);
      const coords = atoms.map(atom => new THREE.Vector3(atom.x, atom.y, atom.z));
      if (coords.length >= 2) {
        chainsCoords.set(cId, coords);
      }
    }
    
    return chainsCoords;
  }
  
  static normalizeChainsCoordinates(chainsCoords, THREE, targetSize = 15) {
    const allPoints = [];
    for (const coords of chainsCoords.values()) {
      allPoints.push(...coords);
    }
    
    if (allPoints.length === 0) return { chains: chainsCoords, scale: 1, centroid: new THREE.Vector3() };
    
    const centroid = new THREE.Vector3();
    for (const p of allPoints) {
      centroid.add(p);
    }
    centroid.divideScalar(allPoints.length);
    
    let maxDist = 0;
    for (const p of allPoints) {
      const d = p.clone().sub(centroid).length();
      maxDist = Math.max(maxDist, d);
    }
    
    const scale = maxDist > 0 ? targetSize / (2 * maxDist) : 1;
    
    const normalizedChains = new Map();
    for (const [cId, coords] of chainsCoords) {
      const normalized = coords.map(p => p.clone().sub(centroid).multiplyScalar(scale));
      normalizedChains.set(cId, normalized);
    }
    
    return { chains: normalizedChains, scale, centroid };
  }
  
  static normalizeAllAtoms(allAtoms, centroid, scale, THREE) {
    return allAtoms.map(atom => ({
      ...atom,
      x: (atom.x - centroid.x) * scale,
      y: (atom.y - centroid.y) * scale,
      z: (atom.z - centroid.z) * scale
    }));
  }
}

// ============================================================
// ATOM RENDERER CLASS
// ============================================================

class AtomRenderer {
  constructor(THREE, sceneManager) {
    this.THREE = THREE;
    this.sceneManager = sceneManager;
    this.instancedMeshes = new Map(); // element -> InstancedMesh
    this.atoms = [];
    this.totalAtomCount = 0;
    this.rangeStart = 0;
    this.rangeEnd = 1;
    this.opacity = 0;
  }
  
  setAtoms(atoms, scale) {
    this.clear();
    this.atoms = atoms;
    this.totalAtomCount = atoms.length;
    this.modelScale = scale;
    
    if (atoms.length === 0) return;
    
    // Group atoms by element
    const elementGroups = new Map();
    
    atoms.forEach((atom, index) => {
      const element = (atom.element || 'C').toUpperCase();
      if (!elementGroups.has(element)) {
        elementGroups.set(element, []);
      }
      elementGroups.get(element).push({ atom, index });
    });
    
    // Create InstancedMesh for each element
    const THREE = this.THREE;
    
    for (const [element, atomList] of elementGroups) {
      const atomData = CPK_ATOM_DATA[element] || CPK_ATOM_DATA['DEFAULT'];
      
      // Store base radius for later scaling updates
      const mesh = this.createInstancedMeshForElement(element, atomList, atomData, 1.0);
      this.instancedMeshes.set(element, mesh);
    }
    
    this.updateVisibility();
  }
  
  createInstancedMeshForElement(element, atomList, atomData, atomScale) {
    const THREE = this.THREE;
    
    // Base scale: Van der Waals radius * model scale * default multiplier * user scale
    // Increased from 0.1 to 0.35 for better visibility
    const radius = atomData.radius * this.modelScale * 0.35 * atomScale;
    
    const geometry = new THREE.SphereGeometry(radius, 16, 16);
    const material = new THREE.MeshStandardMaterial({
      color: atomData.color,
      metalness: 0.3,
      roughness: 0.4,
      transparent: true,
      opacity: this.opacity,
      side: THREE.FrontSide
    });
    
    const mesh = new THREE.InstancedMesh(geometry, material, atomList.length);
    mesh.frustumCulled = false;
    
    const matrix = new THREE.Matrix4();
    const position = new THREE.Vector3();
    
    atomList.forEach(({ atom, index: globalIndex }, localIndex) => {
      position.set(atom.x, atom.y, atom.z);
      matrix.setPosition(position);
      mesh.setMatrixAt(localIndex, matrix);
      mesh.setColorAt(localIndex, new THREE.Color(atomData.color));
      
      // Store mapping for filtering
      if (!mesh.userData.indexMap) {
        mesh.userData.indexMap = [];
      }
      mesh.userData.indexMap.push(globalIndex);
    });
    
    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    
    mesh.userData.element = element;
    mesh.userData.atomData = atomData;
    
    return mesh;
  }
  
  updateAtomScale(atomScale) {
    if (!this.modelScale || this.totalAtomCount === 0) return;
    
    const THREE = this.THREE;
    
    // Rebuild geometries with new scale
    for (const [element, mesh] of this.instancedMeshes) {
      const atomData = mesh.userData.atomData;
      const radius = atomData.radius * this.modelScale * 0.35 * atomScale;
      
      // Dispose old geometry and create new one
      mesh.geometry.dispose();
      mesh.geometry = new THREE.SphereGeometry(radius, 16, 16);
    }
    
    this.updateVisibility();
  }
  
  setOpacity(opacity) {
    this.opacity = opacity;
    this.updateVisibility();
  }
  
  setRange(startPercent, endPercent) {
    this.rangeStart = Math.max(0, Math.min(1, startPercent / 100));
    this.rangeEnd = Math.max(0, Math.min(1, endPercent / 100));
    this.updateVisibility();
  }
  
  updateVisibility() {
    const THREE = this.THREE;
    
    // Remove all meshes from scene
    for (const mesh of this.instancedMeshes.values()) {
      this.sceneManager.remove(mesh);
    }
    
    // If opacity is 0, don't add anything
    if (this.opacity <= 0 || this.totalAtomCount === 0) {
      return;
    }
    
    // Always use min to max (no BackSide rendering)
    const start = Math.min(this.rangeStart, this.rangeEnd);
    const end = Math.max(this.rangeStart, this.rangeEnd);
    
    const startIndex = Math.floor(start * this.totalAtomCount);
    const endIndex = Math.ceil(end * this.totalAtomCount);
    
    // Update each mesh
    for (const mesh of this.instancedMeshes.values()) {
      const indexMap = mesh.userData.indexMap;
      
      // CRITICAL: Restore ALL matrices, then hide out-of-range ones
      const dummy = new THREE.Object3D();
      const position = new THREE.Vector3();
      const matrix = new THREE.Matrix4();
      let visibleCount = 0;
      
      for (let i = 0; i < indexMap.length; i++) {
        const globalIndex = indexMap[i];
        const atom = this.atoms[globalIndex];
        const isInRange = globalIndex >= startIndex && globalIndex < endIndex;
        
        if (isInRange) {
          // Restore full matrix with position
          position.set(atom.x, atom.y, atom.z);
          matrix.setPosition(position);
          mesh.setMatrixAt(i, matrix);
          visibleCount++;
        } else {
          // Hide by scaling to 0
          dummy.position.set(0, 0, 0);
          dummy.scale.set(0, 0, 0);
          dummy.updateMatrix();
          mesh.setMatrixAt(i, dummy.matrix);
        }
      }
      
      mesh.instanceMatrix.needsUpdate = true;
      
      // Update material
      mesh.material.opacity = this.opacity;
      mesh.material.transparent = this.opacity < 1;
      mesh.material.side = THREE.FrontSide;
      mesh.material.needsUpdate = true;
      
      // Add to scene if any atoms are visible
      if (visibleCount > 0) {
        this.sceneManager.add(mesh);
      }
    }
  }
  
  clear() {
    for (const mesh of this.instancedMeshes.values()) {
      mesh.geometry.dispose();
      mesh.material.dispose();
      this.sceneManager.remove(mesh);
    }
    this.instancedMeshes.clear();
    this.atoms = [];
    this.totalAtomCount = 0;
  }
}

// ============================================================
// BOND RENDERER CLASS
// ============================================================

class BondRenderer {
  constructor(THREE, sceneManager) {
    this.THREE = THREE;
    this.sceneManager = sceneManager;
    this.bonds = [];
    this.bondMesh = null;
    this.atoms = [];
    this.atomRangeStart = 0;
    this.atomRangeEnd = 1;
    this.totalAtomCount = 0;
    this.opacity = 0;
    this.radius = 0.1;
    this.halfColor = 0.5;
    this.greyBlend = 0;
    this.ringPink = 0;
    this.modelScale = 1;
  }
  
  detectAndSetBonds(atoms, scale) {
    this.clear();
    this.atoms = atoms;
    this.totalAtomCount = atoms.length;
    this.modelScale = scale;
    
    if (atoms.length === 0) return;
    
    // Detect bonds using spatial grid
    this.bonds = this.detectBonds(atoms);
    console.log(`Detected ${this.bonds.length} bonds`);
    
    // Detect rings (5 and 6-member)
    if (this.bonds.length > 0) {
      this.detectRings();
      const ringBondCount = this.bonds.filter(b => b.isRing).length;
      console.log(`Detected ${ringBondCount} ring bonds`);
    }
    
    if (this.bonds.length > 0) {
      this.createBondGeometry();
    }
  }
  
  detectBonds(atoms) {
    const BOND_CUTOFF = 1.9; // Angstroms (in original PDB coordinates)
    const CELL_SIZE = 2.0;   // Slightly larger than cutoff
    const bonds = [];
    
    // Build spatial grid using original (non-normalized) coordinates
    const grid = new Map();
    
    atoms.forEach((atom, index) => {
      // Use original coordinates (before normalization was applied)
      // We need to reverse the normalization: normalized = (original - centroid) * scale
      // So: original = normalized / scale + centroid
      // But we don't have centroid here, so we work with normalized coords
      // Actually, bonds should be detected BEFORE normalization in distances
      // Let's use the scaled coordinates and scale the cutoff too
      
      const scaledCutoff = BOND_CUTOFF * this.modelScale;
      const scaledCellSize = CELL_SIZE * this.modelScale;
      
      const cellX = Math.floor(atom.x / scaledCellSize);
      const cellY = Math.floor(atom.y / scaledCellSize);
      const cellZ = Math.floor(atom.z / scaledCellSize);
      const key = `${cellX},${cellY},${cellZ}`;
      
      if (!grid.has(key)) {
        grid.set(key, []);
      }
      grid.get(key).push(index);
    });
    
    const scaledCutoffSq = Math.pow(BOND_CUTOFF * this.modelScale, 2);
    const checked = new Set();
    
    // Check each atom against its cell and neighboring cells
    atoms.forEach((atom1, i) => {
      const scaledCellSize = CELL_SIZE * this.modelScale;
      const cellX = Math.floor(atom1.x / scaledCellSize);
      const cellY = Math.floor(atom1.y / scaledCellSize);
      const cellZ = Math.floor(atom1.z / scaledCellSize);
      
      // Check 27 cells (3x3x3 including center)
      for (let dx = -1; dx <= 1; dx++) {
        for (let dy = -1; dy <= 1; dy++) {
          for (let dz = -1; dz <= 1; dz++) {
            const neighborKey = `${cellX + dx},${cellY + dy},${cellZ + dz}`;
            const neighbors = grid.get(neighborKey);
            
            if (!neighbors) continue;
            
            for (const j of neighbors) {
              if (j <= i) continue; // Only check each pair once
              
              const pairKey = `${i},${j}`;
              if (checked.has(pairKey)) continue;
              checked.add(pairKey);
              
              const atom2 = atoms[j];
              
              // Skip hydrogen bonds
              if (atom1.element === 'H' || atom2.element === 'H') continue;
              
              // Calculate distance
              const dx = atom2.x - atom1.x;
              const dy = atom2.y - atom1.y;
              const dz = atom2.z - atom1.z;
              const distSq = dx * dx + dy * dy + dz * dz;
              
              if (distSq <= scaledCutoffSq && distSq > 0.01) {
                bonds.push({
                  atomIndex1: i,
                  atomIndex2: j,
                  element1: atom1.element || 'C',
                  element2: atom2.element || 'C'
                });
              }
            }
          }
        }
      }
    });
    
    return bonds;
  }
  
  detectRings() {
    // Build adjacency list from bonds
    const adjacency = new Map();
    
    this.bonds.forEach((bond, bondIndex) => {
      const a1 = bond.atomIndex1;
      const a2 = bond.atomIndex2;
      
      if (!adjacency.has(a1)) adjacency.set(a1, []);
      if (!adjacency.has(a2)) adjacency.set(a2, []);
      
      adjacency.get(a1).push({ neighbor: a2, bondIndex });
      adjacency.get(a2).push({ neighbor: a1, bondIndex });
    });
    
    // Track which bonds are in rings
    const ringBonds = new Set();
    
    // For each bond, try to find a path back that forms a 5 or 6-member ring
    this.bonds.forEach((bond, bondIndex) => {
      const start = bond.atomIndex1;
      const end = bond.atomIndex2;
      
      // BFS to find shortest path from end back to start (not using the original bond)
      const queue = [{ atom: end, path: [end], bondPath: [] }];
      const visited = new Set([end]);
      
      while (queue.length > 0) {
        const { atom, path, bondPath } = queue.shift();
        
        // Check if we've returned to start
        if (atom === start && path.length >= 2) {
          const ringSize = path.length;
          
          // Only mark 5 or 6-member rings
          if (ringSize === 5 || ringSize === 6) {
            // Mark all bonds in this ring
            ringBonds.add(bondIndex); // Original bond
            bondPath.forEach(bi => ringBonds.add(bi));
          }
          
          break; // Found shortest path for this bond
        }
        
        // Don't search too deep (avoid exponential explosion)
        if (path.length > 6) continue;
        
        // Explore neighbors
        const neighbors = adjacency.get(atom) || [];
        for (const { neighbor, bondIndex: bi } of neighbors) {
          // Don't go back through the original bond
          if (bi === bondIndex) continue;
          
          // Don't revisit atoms
          if (visited.has(neighbor)) continue;
          
          visited.add(neighbor);
          queue.push({
            atom: neighbor,
            path: [...path, neighbor],
            bondPath: [...bondPath, bi]
          });
        }
      }
    });
    
    // Mark bonds as ring bonds
    this.bonds.forEach((bond, index) => {
      bond.isRing = ringBonds.has(index);
    });
  }
  
  createBondGeometry() {
    if (this.bonds.length === 0) return;
    
    const THREE = this.THREE;
    
    // Create one instanced mesh for all bond segments
    // We'll create TWO instances per bond for half-coloring
    const instanceCount = this.bonds.length * 2;
    
    const geometry = new THREE.CylinderGeometry(
      this.radius * this.modelScale * 0.1, // Base multiplier for reasonable bond size
      this.radius * this.modelScale * 0.1,
      1.0, // Unit height, will scale per instance
      8,   // Radial segments
      1,   // Height segments
      true // Open ended (no caps)
    );
    
    // Don't use vertexColors: true - that's for BufferGeometry, not InstancedMesh
    // Instance colors work automatically when you call setColorAt()
    const material = new THREE.MeshStandardMaterial({
      metalness: 0.3,
      roughness: 0.4,
      transparent: true,
      opacity: this.opacity,
      side: THREE.FrontSide
    });
    
    this.bondMesh = new THREE.InstancedMesh(geometry, material, instanceCount);
    this.bondMesh.frustumCulled = false;
    
    // Store bond info for later filtering
    this.bondMesh.userData.bonds = this.bonds;
    
    this.updateBondTransformsAndColors();
  }
  
  updateBondTransformsAndColors() {
    if (!this.bondMesh || this.bonds.length === 0) return;
    
    const THREE = this.THREE;
    const matrix = new THREE.Matrix4();
    const position = new THREE.Vector3();
    const quaternion = new THREE.Quaternion();
    const scale = new THREE.Vector3();
    const yAxis = new THREE.Vector3(0, 1, 0);
    const greyColor = new THREE.Color(BOND_GREY);
    const pinkColor = new THREE.Color(BOND_RING_PINK);
    
    this.bonds.forEach((bond, bondIndex) => {
      const atom1 = this.atoms[bond.atomIndex1];
      const atom2 = this.atoms[bond.atomIndex2];
      
      const start = new THREE.Vector3(atom1.x, atom1.y, atom1.z);
      const end = new THREE.Vector3(atom2.x, atom2.y, atom2.z);
      const direction = new THREE.Vector3().subVectors(end, start);
      const bondLength = direction.length();
      
      direction.normalize();
      quaternion.setFromUnitVectors(yAxis, direction);
      
      // Get atomic numbers for color ordering
      const data1 = CPK_ATOM_DATA[bond.element1.toUpperCase()] || CPK_ATOM_DATA['DEFAULT'];
      const data2 = CPK_ATOM_DATA[bond.element2.toUpperCase()] || CPK_ATOM_DATA['DEFAULT'];
      
      // Determine which is lower/higher atomic number
      const isAtom1Lower = data1.atomicNumber <= data2.atomicNumber;
      const lowerData = isAtom1Lower ? data1 : data2;
      const higherData = isAtom1Lower ? data2 : data1;
      const lowerStart = isAtom1Lower ? start : end;
      const higherStart = isAtom1Lower ? end : start;
      
      // Calculate split point based on halfColor slider
      const splitRatio = this.halfColor;
      const splitPoint = new THREE.Vector3().lerpVectors(lowerStart, higherStart, splitRatio);
      
      // First segment: lower atomic number end
      const length1 = lowerStart.distanceTo(splitPoint);
      const mid1 = new THREE.Vector3().lerpVectors(lowerStart, splitPoint, 0.5);
      
      position.copy(mid1);
      scale.set(1, length1, 1);
      matrix.compose(position, quaternion, scale);
      this.bondMesh.setMatrixAt(bondIndex * 2, matrix);
      
      // Color for first segment (with grey blending, then pink if ring)
      let color1 = new THREE.Color(lowerData.color).lerp(greyColor, this.greyBlend);
      if (bond.isRing && this.ringPink > 0) {
        color1.lerp(pinkColor, this.ringPink);
      }
      this.bondMesh.setColorAt(bondIndex * 2, color1);
      
      // Second segment: higher atomic number end
      const length2 = splitPoint.distanceTo(higherStart);
      const mid2 = new THREE.Vector3().lerpVectors(splitPoint, higherStart, 0.5);
      
      position.copy(mid2);
      scale.set(1, length2, 1);
      matrix.compose(position, quaternion, scale);
      this.bondMesh.setMatrixAt(bondIndex * 2 + 1, matrix);
      
      // Color for second segment (with grey blending, then pink if ring)
      let color2 = new THREE.Color(higherData.color).lerp(greyColor, this.greyBlend);
      if (bond.isRing && this.ringPink > 0) {
        color2.lerp(pinkColor, this.ringPink);
      }
      this.bondMesh.setColorAt(bondIndex * 2 + 1, color2);
    });
    
    this.bondMesh.instanceMatrix.needsUpdate = true;
    if (this.bondMesh.instanceColor) {
      this.bondMesh.instanceColor.needsUpdate = true;
    }
  }
  
  updateBondRadius(radius) {
    this.radius = radius;
    
    if (!this.bondMesh || this.bonds.length === 0) return;
    
    const THREE = this.THREE;
    
    // Rebuild geometry with new radius
    this.bondMesh.geometry.dispose();
    this.bondMesh.geometry = new THREE.CylinderGeometry(
      radius * this.modelScale * 0.1, // Base multiplier for reasonable bond size
      radius * this.modelScale * 0.1,
      1.0,
      8,
      1,
      true
    );
    
    this.updateVisibility();
  }
  
  setOpacity(opacity) {
    this.opacity = opacity;
    this.updateVisibility();
  }
  
  setRadius(radius) {
    this.updateBondRadius(radius);
  }
  
  setHalfColor(halfColor) {
    this.halfColor = halfColor;
    if (this.bondMesh && this.bonds.length > 0) {
      this.updateBondTransformsAndColors();
      this.updateVisibility();
    }
  }
  
  setGreyBlend(greyBlend) {
    this.greyBlend = greyBlend;
    if (this.bondMesh && this.bonds.length > 0) {
      this.updateBondTransformsAndColors();
      this.updateVisibility();
    }
  }
  
  setRingPink(ringPink) {
    this.ringPink = ringPink;
    if (this.bondMesh && this.bonds.length > 0) {
      this.updateBondTransformsAndColors();
      this.updateVisibility();
    }
  }
  
  setAtomRange(startPercent, endPercent) {
    this.atomRangeStart = Math.max(0, Math.min(1, startPercent / 100));
    this.atomRangeEnd = Math.max(0, Math.min(1, endPercent / 100));
    this.updateVisibility();
  }
  
  updateVisibility() {
    if (!this.bondMesh) return;
    
    const THREE = this.THREE;
    
    // Remove from scene
    this.sceneManager.remove(this.bondMesh);
    
    // If opacity is 0, don't add anything
    if (this.opacity <= 0 || this.bonds.length === 0) {
      return;
    }
    
    // Always use min to max (consistent with atoms)
    const start = Math.min(this.atomRangeStart, this.atomRangeEnd);
    const end = Math.max(this.atomRangeStart, this.atomRangeEnd);
    
    const startIndex = Math.floor(start * this.totalAtomCount);
    const endIndex = Math.ceil(end * this.totalAtomCount);
    
    // Recalculate ALL bond matrices (needed because we modify them to hide bonds)
    const matrix = new THREE.Matrix4();
    const position = new THREE.Vector3();
    const quaternion = new THREE.Quaternion();
    const scale = new THREE.Vector3();
    const yAxis = new THREE.Vector3(0, 1, 0);
    const greyColor = new THREE.Color(BOND_GREY);
    const pinkColor = new THREE.Color(BOND_RING_PINK);
    
    let visibleCount = 0;
    
    this.bonds.forEach((bond, bondIndex) => {
      const atom1 = this.atoms[bond.atomIndex1];
      const atom2 = this.atoms[bond.atomIndex2];
      const atom1InRange = bond.atomIndex1 >= startIndex && bond.atomIndex1 < endIndex;
      const atom2InRange = bond.atomIndex2 >= startIndex && bond.atomIndex2 < endIndex;
      
      if (atom1InRange && atom2InRange) {
        // Bond is visible - calculate proper transforms
        visibleCount++;
        
        const start = new THREE.Vector3(atom1.x, atom1.y, atom1.z);
        const end = new THREE.Vector3(atom2.x, atom2.y, atom2.z);
        const direction = new THREE.Vector3().subVectors(end, start);
        const bondLength = direction.length();
        
        direction.normalize();
        quaternion.setFromUnitVectors(yAxis, direction);
        
        // Get atomic data for colors
        const data1 = CPK_ATOM_DATA[bond.element1.toUpperCase()] || CPK_ATOM_DATA['DEFAULT'];
        const data2 = CPK_ATOM_DATA[bond.element2.toUpperCase()] || CPK_ATOM_DATA['DEFAULT'];
        
        const isAtom1Lower = data1.atomicNumber <= data2.atomicNumber;
        const lowerData = isAtom1Lower ? data1 : data2;
        const higherData = isAtom1Lower ? data2 : data1;
        const lowerStart = isAtom1Lower ? start : end;
        const higherStart = isAtom1Lower ? end : start;
        
        const splitRatio = this.halfColor;
        const splitPoint = new THREE.Vector3().lerpVectors(lowerStart, higherStart, splitRatio);
        
        // First segment
        const length1 = lowerStart.distanceTo(splitPoint);
        const mid1 = new THREE.Vector3().lerpVectors(lowerStart, splitPoint, 0.5);
        
        position.copy(mid1);
        scale.set(1, length1, 1);
        matrix.compose(position, quaternion, scale);
        this.bondMesh.setMatrixAt(bondIndex * 2, matrix);
        
        let color1 = new THREE.Color(lowerData.color).lerp(greyColor, this.greyBlend);
        if (bond.isRing && this.ringPink > 0) {
          color1.lerp(pinkColor, this.ringPink);
        }
        this.bondMesh.setColorAt(bondIndex * 2, color1);
        
        // Second segment
        const length2 = splitPoint.distanceTo(higherStart);
        const mid2 = new THREE.Vector3().lerpVectors(splitPoint, higherStart, 0.5);
        
        position.copy(mid2);
        scale.set(1, length2, 1);
        matrix.compose(position, quaternion, scale);
        this.bondMesh.setMatrixAt(bondIndex * 2 + 1, matrix);
        
        let color2 = new THREE.Color(higherData.color).lerp(greyColor, this.greyBlend);
        if (bond.isRing && this.ringPink > 0) {
          color2.lerp(pinkColor, this.ringPink);
        }
        this.bondMesh.setColorAt(bondIndex * 2 + 1, color2);
        
      } else {
        // Bond is hidden - set scale to 0
        const dummy = new THREE.Object3D();
        dummy.position.set(0, 0, 0);
        dummy.scale.set(0, 0, 0);
        dummy.updateMatrix();
        this.bondMesh.setMatrixAt(bondIndex * 2, dummy.matrix);
        this.bondMesh.setMatrixAt(bondIndex * 2 + 1, dummy.matrix);
      }
    });
    
    this.bondMesh.instanceMatrix.needsUpdate = true;
    if (this.bondMesh.instanceColor) {
      this.bondMesh.instanceColor.needsUpdate = true;
    }
    
    // Update material
    this.bondMesh.material.opacity = this.opacity;
    this.bondMesh.material.transparent = this.opacity < 1;
    this.bondMesh.material.needsUpdate = true;
    
    // Add to scene if any bonds are visible
    if (visibleCount > 0) {
      this.sceneManager.add(this.bondMesh);
    }
  }
  
  clear() {
    if (this.bondMesh) {
      this.bondMesh.geometry.dispose();
      this.bondMesh.material.dispose();
      this.sceneManager.remove(this.bondMesh);
      this.bondMesh = null;
    }
    this.bonds = [];
    this.atoms = [];
    this.totalAtomCount = 0;
  }
}

// ============================================================
// ARC MATH CLASS
// ============================================================

class ArcMath {
  static computeArc(P0, T0, P1, THREE) {
    const chord = new THREE.Vector3().subVectors(P1, P0);
    const chordLength = chord.length();
    
    if (chordLength < 0.0001) return null;
    
    const chordDir = chord.clone().normalize();
    const dot = T0.dot(chordDir);
    
    if (Math.abs(dot) > 0.9999999) {
      return this.createLineArc(P0, P1, T0, chordLength);
    }
    
    const planeNormal = new THREE.Vector3().crossVectors(T0, chordDir).normalize();
    const N0 = new THREE.Vector3().crossVectors(planeNormal, T0).normalize();
    
    const c_x = chord.dot(T0);
    const c_y = chord.dot(N0);
    
    if (Math.abs(c_y) < 0.000001) {
      return this.createLineArc(P0, P1, T0, chordLength);
    }
    
    const r = (c_x * c_x + c_y * c_y) / (2 * c_y);
    const radius = Math.abs(r);
    const center = P0.clone().addScaledVector(N0, r);
    
    const fromCenter0 = new THREE.Vector3().subVectors(P0, center);
    const fromCenter1 = new THREE.Vector3().subVectors(P1, center);
    
    let angle = Math.acos(THREE.MathUtils.clamp(
      fromCenter0.dot(fromCenter1) / (radius * radius), -1, 1
    ));
    
    if (c_x < 0) angle = 2 * Math.PI - angle;
    
    const sign = Math.sign(r);
    const T1 = new THREE.Vector3().crossVectors(planeNormal, fromCenter1).normalize();
    if (sign < 0) T1.negate();
    
    return {
      type: 'arc',
      P0: P0.clone(),
      P1: P1.clone(),
      T0: T0.clone(),
      T1: T1,
      center: center,
      radius: radius,
      angle: angle * sign,
      planeNormal: planeNormal,
      length: radius * Math.abs(angle)
    };
  }
  
  static createLineArc(P0, P1, T0, length) {
    return {
      type: 'line',
      P0: P0.clone(),
      P1: P1.clone(),
      T0: T0.clone(),
      T1: T0.clone(),
      length: length
    };
  }
  
  static sampleArc(arc, t, THREE) {
    if (t <= 0) return arc.P0.clone();
    if (t >= 1) return arc.P1.clone();
    
    if (arc.type === 'line') {
      return new THREE.Vector3().lerpVectors(arc.P0, arc.P1, t);
    }
    
    const theta = arc.angle * t;
    const fromCenter0 = new THREE.Vector3().subVectors(arc.P0, arc.center);
    const rotated = fromCenter0.clone().applyAxisAngle(arc.planeNormal, theta);
    return arc.center.clone().add(rotated);
  }
  
  static sampleArcTangent(arc, t) {
    if (arc.type === 'line') return arc.T0.clone();
    
    const theta = arc.angle * t;
    return arc.T0.clone().applyAxisAngle(arc.planeNormal, theta);
  }
  
  static transportBinormal(arc, B0) {
    if (arc.type === 'line') return B0.clone();
    return B0.clone().applyAxisAngle(arc.planeNormal, arc.angle);
  }
}

// ============================================================
// LOCAL FRAME COMPUTER CLASS
// ============================================================

class LocalFrameComputer {
  static computeTangent(points, i, THREE) {
    const n = points.length;
    let T;
    
    if (i === 0) {
      T = new THREE.Vector3().subVectors(points[1], points[0]);
    } else if (i === n - 1) {
      T = new THREE.Vector3().subVectors(points[n - 1], points[n - 2]);
    } else {
      T = new THREE.Vector3().subVectors(points[i + 1], points[i - 1]);
    }
    
    return T.normalize();
  }
  
  static computeBinormal(points, i, tangent, THREE) {
    const n = points.length;
    let B;
    
    if (i === 0) {
      if (n >= 3) {
        const v1 = new THREE.Vector3().subVectors(points[1], points[0]);
        const v2 = new THREE.Vector3().subVectors(points[2], points[0]);
        B = new THREE.Vector3().crossVectors(v1, v2);
      } else {
        B = this.getDefaultBinormal(tangent, THREE);
      }
    } else if (i === n - 1) {
      if (n >= 3) {
        const v1 = new THREE.Vector3().subVectors(points[n - 2], points[n - 3]);
        const v2 = new THREE.Vector3().subVectors(points[n - 1], points[n - 3]);
        B = new THREE.Vector3().crossVectors(v1, v2);
      } else {
        B = this.getDefaultBinormal(tangent, THREE);
      }
    } else {
      const v1 = new THREE.Vector3().subVectors(points[i], points[i - 1]);
      const v2 = new THREE.Vector3().subVectors(points[i + 1], points[i - 1]);
      B = new THREE.Vector3().crossVectors(v1, v2);
    }
    
    if (B.length() < 0.0001) {
      B = this.getDefaultBinormal(tangent, THREE);
    }
    
    B.normalize();
    B.addScaledVector(tangent, -B.dot(tangent)).normalize();
    
    return B;
  }
  
  static getDefaultBinormal(tangent, THREE) {
    const T = tangent.clone().normalize();
    let refUp = new THREE.Vector3(0, 1, 0);
    
    if (Math.abs(T.y) > 0.95) {
      refUp = new THREE.Vector3(0, 0, 1);
    }
    
    let B = new THREE.Vector3().crossVectors(T, refUp);
    if (B.length() < 0.001) {
      B = new THREE.Vector3().crossVectors(T, new THREE.Vector3(1, 0, 0));
    }
    return B.normalize();
  }
  
  static computeFrame(points, i, THREE) {
    const T = this.computeTangent(points, i, THREE);
    const B = this.computeBinormal(points, i, T, THREE);
    const N = new THREE.Vector3().crossVectors(B, T).normalize();
    
    return { T, B, N };
  }
  
  static computeAllFrames(points, THREE) {
    const frames = [];
    
    for (let i = 0; i < points.length; i++) {
      frames.push(this.computeFrame(points, i, THREE));
    }
    
    for (let i = 1; i < frames.length; i++) {
      if (frames[i].B.dot(frames[i - 1].B) < 0) {
        frames[i].B.negate();
        frames[i].N.negate();
      }
    }
    
    return frames;
  }
}

// ============================================================
// BIARC SEGMENT 3D CLASS
// ============================================================

class BiarcSegment3D {
  constructor(P0, P1, frame0, frame1, THREE) {
    this.THREE = THREE;
    this.P0 = P0.clone();
    this.P1 = P1.clone();
    this.T0 = frame0.T.clone();
    this.T1 = frame1.T.clone();
    this.B0 = frame0.B.clone();
    this.B1 = frame1.B.clone();
    
    this.computeJointAndArcs();
    this.computeTorsion();
  }
  
  computeJointAndArcs() {
    const THREE = this.THREE;
    const chord = new THREE.Vector3().subVectors(this.P1, this.P0);
    const chordLength = chord.length();
    
    if (chordLength < 0.0001) {
      this.J = this.P0.clone();
      this.T_J = this.T0.clone();
      this.arc1 = ArcMath.createLineArc(this.P0, this.J, this.T0, 0);
      this.arc2 = ArcMath.createLineArc(this.J, this.P1, this.T_J, 0);
      this.length = 0;
      return;
    }
    
    const chordDir = chord.clone().normalize();
    const midpoint = new THREE.Vector3().addVectors(this.P0, this.P1).multiplyScalar(0.5);
    
    const avgT = new THREE.Vector3().addVectors(this.T0, this.T1);
    let planeNormal = new THREE.Vector3().crossVectors(chordDir, avgT);
    
    if (planeNormal.length() < 0.001) {
      this.J = midpoint.clone();
      this.arc1 = ArcMath.computeArc(this.P0, this.T0, this.J, THREE);
      this.T_J = this.arc1 ? this.arc1.T1.clone() : this.T0.clone();
      this.arc2 = ArcMath.computeArc(this.J, this.T_J, this.P1, THREE);
      this.length = (this.arc1 ? this.arc1.length : 0) + (this.arc2 ? this.arc2.length : 0);
      return;
    }
    
    planeNormal.normalize();
    
    const yAxis = new THREE.Vector3().crossVectors(planeNormal, chordDir).normalize();
    
    const t0_x = this.T0.dot(chordDir);
    const t0_y = this.T0.dot(yAxis);
    const t1_x = this.T1.dot(chordDir);
    const t1_y = this.T1.dot(yAxis);
    
    const angle0 = Math.atan2(t0_y, t0_x);
    const angle1 = Math.atan2(t1_y, t1_x);
    
    let thetaDiff = angle0 - angle1;
    while (thetaDiff > Math.PI) thetaDiff -= 2 * Math.PI;
    while (thetaDiff < -Math.PI) thetaDiff += 2 * Math.PI;
    
    const thetaError = thetaDiff * 0.25;
    const c = Math.tan(thetaError) * 0.5 * chordLength;
    
    this.J = midpoint.clone().addScaledVector(yAxis, c);
    
    this.arc1 = ArcMath.computeArc(this.P0, this.T0, this.J, THREE);
    this.T_J = this.arc1 ? this.arc1.T1.clone() : this.T0.clone();
    this.arc2 = ArcMath.computeArc(this.J, this.T_J, this.P1, THREE);
    
    this.length = (this.arc1 ? this.arc1.length : 0) + (this.arc2 ? this.arc2.length : 0);
  }
  
  computeTorsion() {
    const THREE = this.THREE;
    if (!this.arc1 || !this.arc2) {
      this.totalTorsion = 0;
      return;
    }
    
    let B_transported = this.B0.clone();
    B_transported = ArcMath.transportBinormal(this.arc1, B_transported);
    B_transported = ArcMath.transportBinormal(this.arc2, B_transported);
    
    this.totalTorsion = this.computeTwistAngle(B_transported, this.B1, this.T1);
  }
  
  computeTwistAngle(B1, B2, T) {
    const THREE = this.THREE;
    const projB1 = B1.clone().addScaledVector(T, -B1.dot(T)).normalize();
    const projB2 = B2.clone().addScaledVector(T, -B2.dot(T)).normalize();
    
    let angle = Math.acos(THREE.MathUtils.clamp(projB1.dot(projB2), -1, 1));
    
    const cross = new THREE.Vector3().crossVectors(projB1, projB2);
    if (cross.dot(T) < 0) angle = -angle;
    
    return angle;
  }
  
  getPointAt(t) {
    const THREE = this.THREE;
    if (!this.arc1 || !this.arc2 || this.length === 0) {
      return new THREE.Vector3().lerpVectors(this.P0, this.P1, t);
    }
    
    const arc1Ratio = this.arc1.length / this.length;
    
    if (t <= arc1Ratio) {
      const localT = arc1Ratio > 0 ? t / arc1Ratio : 0;
      return ArcMath.sampleArc(this.arc1, localT, THREE);
    } else {
      const localT = (1 - arc1Ratio) > 0 ? (t - arc1Ratio) / (1 - arc1Ratio) : 1;
      return ArcMath.sampleArc(this.arc2, localT, THREE);
    }
  }
  
  getTangentAt(t) {
    if (!this.arc1 || !this.arc2 || this.length === 0) {
      return this.T0.clone();
    }
    
    const arc1Ratio = this.arc1.length / this.length;
    
    if (t <= arc1Ratio) {
      const localT = arc1Ratio > 0 ? t / arc1Ratio : 0;
      return ArcMath.sampleArcTangent(this.arc1, localT);
    } else {
      const localT = (1 - arc1Ratio) > 0 ? (t - arc1Ratio) / (1 - arc1Ratio) : 1;
      return ArcMath.sampleArcTangent(this.arc2, localT);
    }
  }
  
  getFrameAt(t) {
    const THREE = this.THREE;
    const P = this.getPointAt(t);
    const T = this.getTangentAt(t).normalize();
    
    if (!this.arc1 || !this.arc2 || this.length === 0) {
      const B = this.B0.clone();
      B.addScaledVector(T, -B.dot(T)).normalize();
      const N = new THREE.Vector3().crossVectors(B, T).normalize();
      return { P, T, N, B };
    }
    
    let B = this.B0.clone();
    const arc1Ratio = this.arc1.length / this.length;
    
    if (t <= arc1Ratio) {
      const localT = arc1Ratio > 0 ? t / arc1Ratio : 0;
      if (this.arc1.type === 'arc') {
        const partialAngle = this.arc1.angle * localT;
        B.applyAxisAngle(this.arc1.planeNormal, partialAngle);
      }
    } else {
      B = ArcMath.transportBinormal(this.arc1, B);
      
      const localT = (1 - arc1Ratio) > 0 ? (t - arc1Ratio) / (1 - arc1Ratio) : 1;
      if (this.arc2.type === 'arc') {
        const partialAngle = this.arc2.angle * localT;
        B.applyAxisAngle(this.arc2.planeNormal, partialAngle);
      }
    }
    
    const twist = this.totalTorsion * t;
    B.applyAxisAngle(T, twist);
    
    B.addScaledVector(T, -B.dot(T)).normalize();
    const N = new THREE.Vector3().crossVectors(B, T).normalize();
    
    return { P, T, N, B };
  }
  
  getLength() {
    return this.length;
  }
  
  getJointPoint() {
    return this.J ? this.J.clone() : null;
  }
}

// ============================================================
// RIBBON GEOMETRY BUILDER CLASS
// ============================================================

class RibbonGeometryBuilder {
  static build(segments, width, thickness, samplesPerSegment, THREE) {
    const halfW = width / 2;
    const halfT = thickness / 2;
    
    const samples = this.sampleAllSegments(segments, samplesPerSegment);
    
    return this.buildGeometryFromSamples(samples, halfW, halfT, THREE);
  }
  
  static sampleAllSegments(segments, samplesPerSegment) {
    const samples = [];
    let cumulativeLength = 0;
    const totalLength = segments.reduce((sum, seg) => sum + seg.getLength(), 0);
    
    for (let segIdx = 0; segIdx < segments.length; segIdx++) {
      const segment = segments[segIdx];
      const segLength = segment.getLength();
      
      const startI = (segIdx === 0) ? 0 : 1;
      
      for (let i = startI; i <= samplesPerSegment; i++) {
        const t = i / samplesPerSegment;
        const frame = segment.getFrameAt(t);
        
        samples.push({
          P: frame.P,
          T: frame.T,
          N: frame.N,
          B: frame.B,
          u: totalLength > 0 ? (cumulativeLength + segLength * t) / totalLength : 0
        });
      }
      
      cumulativeLength += segLength;
    }
    
    return samples;
  }
  
  static buildGeometryFromSamples(samples, halfW, halfT, THREE) {
    const positions = [];
    const normals = [];
    const uvs = [];
    const indices = [];
    
    const addQuad = (v0, v1, v2, v3, normal, u0, u1) => {
      const base = positions.length / 3;
      
      positions.push(v0.x, v0.y, v0.z);
      positions.push(v1.x, v1.y, v1.z);
      positions.push(v2.x, v2.y, v2.z);
      positions.push(v3.x, v3.y, v3.z);
      
      for (let j = 0; j < 4; j++) {
        normals.push(normal.x, normal.y, normal.z);
      }
      
      uvs.push(0, u0, 1, u0, 1, u1, 0, u1);
      
      indices.push(base, base + 1, base + 2);
      indices.push(base, base + 2, base + 3);
    };
    
    const addEndCap = (s, hw, ht, flip) => {
      const base = positions.length / 3;
      const normal = flip ? s.T.clone().negate() : s.T.clone();
      
      const corners = [
        new THREE.Vector3().copy(s.P).addScaledVector(s.N, ht).addScaledVector(s.B, -hw),
        new THREE.Vector3().copy(s.P).addScaledVector(s.N, ht).addScaledVector(s.B, hw),
        new THREE.Vector3().copy(s.P).addScaledVector(s.N, -ht).addScaledVector(s.B, hw),
        new THREE.Vector3().copy(s.P).addScaledVector(s.N, -ht).addScaledVector(s.B, -hw)
      ];
      
      corners.forEach(c => positions.push(c.x, c.y, c.z));
      for (let j = 0; j < 4; j++) normals.push(normal.x, normal.y, normal.z);
      uvs.push(0, 0, 1, 0, 1, 1, 0, 1);
      
      if (flip) {
        indices.push(base, base + 2, base + 1);
        indices.push(base, base + 3, base + 2);
      } else {
        indices.push(base, base + 1, base + 2);
        indices.push(base, base + 2, base + 3);
      }
    };
    
    for (let i = 0; i < samples.length - 1; i++) {
      const s0 = samples[i];
      const s1 = samples[i + 1];
      
      const corners0 = [
        new THREE.Vector3().copy(s0.P).addScaledVector(s0.N, halfT).addScaledVector(s0.B, -halfW),
        new THREE.Vector3().copy(s0.P).addScaledVector(s0.N, halfT).addScaledVector(s0.B, halfW),
        new THREE.Vector3().copy(s0.P).addScaledVector(s0.N, -halfT).addScaledVector(s0.B, halfW),
        new THREE.Vector3().copy(s0.P).addScaledVector(s0.N, -halfT).addScaledVector(s0.B, -halfW)
      ];
      
      const corners1 = [
        new THREE.Vector3().copy(s1.P).addScaledVector(s1.N, halfT).addScaledVector(s1.B, -halfW),
        new THREE.Vector3().copy(s1.P).addScaledVector(s1.N, halfT).addScaledVector(s1.B, halfW),
        new THREE.Vector3().copy(s1.P).addScaledVector(s1.N, -halfT).addScaledVector(s1.B, halfW),
        new THREE.Vector3().copy(s1.P).addScaledVector(s1.N, -halfT).addScaledVector(s1.B, -halfW)
      ];
      
      const topNormal = s0.N.clone().lerp(s1.N, 0.5).normalize();
      addQuad(corners0[0], corners0[1], corners1[1], corners1[0], topNormal, s0.u, s1.u);
      
      const bottomNormal = topNormal.clone().negate();
      addQuad(corners0[3], corners1[3], corners1[2], corners0[2], bottomNormal, s0.u, s1.u);
      
      const rightNormal = s0.B.clone().lerp(s1.B, 0.5).normalize();
      addQuad(corners0[1], corners0[2], corners1[2], corners1[1], rightNormal, s0.u, s1.u);
      
      const leftNormal = rightNormal.clone().negate();
      addQuad(corners0[0], corners1[0], corners1[3], corners0[3], leftNormal, s0.u, s1.u);
    }
    
    addEndCap(samples[0], halfW, halfT, true);
    addEndCap(samples[samples.length - 1], halfW, halfT, false);
    
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geometry.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
    geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
    geometry.setIndex(indices);
    
    return geometry;
  }
}

// ============================================================
// MOLAM SCENE MANAGER CLASS
// ============================================================

class MolamScene {
  constructor(container, THREE, OrbitControls) {
    this.THREE = THREE;
    this.container = container;
    
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0f0f23);
    
    this.camera = new THREE.PerspectiveCamera(
      60, container.clientWidth / container.clientHeight, 0.1, 1000
    );
    this.camera.position.set(10, 8, 12);
    
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setSize(container.clientWidth, container.clientHeight);
    this.renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(this.renderer.domElement);
    
    this.setupControls(OrbitControls);
    this.setupLighting();
    this.setupHelpers();
  }
  
  setupControls(OrbitControls) {
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.05;
    this.controls.mouseButtons = {
      LEFT: this.THREE.MOUSE.ROTATE,
      MIDDLE: this.THREE.MOUSE.DOLLY,
      RIGHT: null
    };
  }
  
  setupLighting() {
    const THREE = this.THREE;
    
    const ambientLight = new THREE.AmbientLight(0x404040, 0.4);
    this.scene.add(ambientLight);
    
    const mainLight = new THREE.DirectionalLight(0xffffff, 1.2);
    mainLight.position.set(5, 15, 10);
    this.scene.add(mainLight);
    
    const fillLight = new THREE.DirectionalLight(0x4488ff, 0.5);
    fillLight.position.set(-10, 5, -5);
    this.scene.add(fillLight);
    
    const rimLight = new THREE.DirectionalLight(0xff8844, 0.3);
    rimLight.position.set(0, -5, 10);
    this.scene.add(rimLight);
  }
  
  setupHelpers() {
    const THREE = this.THREE;
    
    this.gridHelper = new THREE.GridHelper(20, 20, 0x444444, 0x333333);
    this.gridHelper.position.y = -4;
    this.scene.add(this.gridHelper);
    
    const axesHelper = new THREE.AxesHelper(2);
    axesHelper.position.set(-9, -3.9, -9);
    this.scene.add(axesHelper);
  }
  
  add(object) { this.scene.add(object); }
  remove(object) { this.scene.remove(object); }
  
  onResize() {
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }
  
  setAtomUpdateCallback(callback) {
    this.atomUpdateCallback = callback;
  }
  
  render() {
    this.controls.update();
    
    // Update atom visualization if callback is set
    if (this.atomUpdateCallback) {
      this.atomUpdateCallback();
    }
    
    this.renderer.render(this.scene, this.camera);
  }
  
  resetCamera() {
    this.camera.position.set(10, 8, 12);
    this.controls.target.set(0, 0, 0);
    this.controls.update();
  }
}

// ============================================================
// MOLAM APPLICATION CLASS
// ============================================================

class MolamApp {
  constructor(sceneManager, base, THREE, pdbId) {
    this.sceneManager = sceneManager;
    this.base = base;
    this.THREE = THREE;
    
    // Default control points (demo mode)
    this.controlPoints = [
      new THREE.Vector3(-6, 0, 0),
      new THREE.Vector3(-3, 2, 2),
      new THREE.Vector3(0, -1, -1),
      new THREE.Vector3(3, 1, 2),
      new THREE.Vector3(6, 0, 0)
    ];
    
    this.controlPointRolls = [0, 0, 0, 0, 0];
    this.isProteinMode = false;
    
    this.chains = null;
    this.modelScale = 1;
    this.currentPdbId = pdbId;
    this.atomToChainMap = [];
    
    this.setupMaterials();
    
    this.controlAtoms = [];
    this.intermediateAtoms = [];
    this.normalIndicators = [];
    this.ribbonMeshes = [];
    
    this.baseNodeRadius = { control: 0.25, intermediate: 0.2 };
    this.samplesPerSegment = 40;
    
    // Atom renderer
    this.atomRenderer = new AtomRenderer(THREE, sceneManager);
    
    // Bond renderer
    this.bondRenderer = new BondRenderer(THREE, sceneManager);
    
    // Register atom and bond update callback with scene manager
    sceneManager.setAtomUpdateCallback(() => {
      this.updateAtomVisualization();
      this.updateBondVisualization();
    });
    
    this.createControlAtoms();
    this.setupInteraction();
  }
  
  setupMaterials() {
    const THREE = this.THREE;
    
    this.chainColors = [
      0x4fc3f7, 0xff6b6b, 0x95e1d3, 0xf38181, 0xaa96da,
      0xfcbad3, 0xa8d8ea, 0xf9ed69, 0x6a0572, 0xf85f73
    ];
    
    this.materials = {
      controlNode: new THREE.MeshStandardMaterial({
        color: 0xff6b6b, metalness: 0.3, roughness: 0.4, emissive: 0x331111
      }),
      controlNodeHover: new THREE.MeshStandardMaterial({
        color: 0xffaa00, metalness: 0.3, roughness: 0.4, emissive: 0x442200
      }),
      intermediateNode: new THREE.MeshStandardMaterial({
        color: 0x6bff6b, metalness: 0.3, roughness: 0.4, emissive: 0x113311
      }),
      ribbon: new THREE.MeshStandardMaterial({
        color: 0x4fc3f7, metalness: 0.4, roughness: 0.35, side: THREE.FrontSide
      })
    };
  }
  
  getEffectiveNodeRadius(type) {
    const params = this.base.getParams();
    const baseRadius = this.baseNodeRadius[type];
    const globalScale = Math.max(0.01, params.nodeScale);
    const typeScale = type === 'control' 
      ? params.controlNodeSize 
      : params.jointNodeSize;
    return baseRadius * globalScale * typeScale * 2;
  }
  
  createControlAtoms() {
    const THREE = this.THREE;
    this.controlAtoms.forEach(atom => this.sceneManager.remove(atom));
    this.controlAtoms = [];
    
    const radius = this.getEffectiveNodeRadius('control');
    const visible = radius > 0.001;
    
    const geometry = visible 
      ? new THREE.SphereGeometry(radius, 32, 32)
      : new THREE.SphereGeometry(0.001, 4, 4);
    
    this.controlPoints.forEach((point, index) => {
      const sphere = new THREE.Mesh(
        geometry,
        this.materials.controlNode.clone()
      );
      sphere.position.copy(point);
      sphere.userData.index = index;
      sphere.userData.isControl = true;
      sphere.visible = visible;
      this.sceneManager.add(sphere);
      this.controlAtoms.push(sphere);
    });
  }
  
  updateControlAtomSizes() {
    const THREE = this.THREE;
    const radius = this.getEffectiveNodeRadius('control');
    const visible = radius > 0.001;
    
    const geometry = visible 
      ? new THREE.SphereGeometry(radius, 32, 32)
      : new THREE.SphereGeometry(0.001, 4, 4);
    
    this.controlAtoms.forEach(atom => {
      atom.geometry.dispose();
      atom.geometry = geometry;
      atom.visible = visible;
    });
  }
  
  updateIntermediateAtoms(jointPositions) {
    const THREE = this.THREE;
    this.intermediateAtoms.forEach(atom => {
      atom.geometry.dispose();
      this.sceneManager.remove(atom);
    });
    this.intermediateAtoms = [];
    
    const radius = this.getEffectiveNodeRadius('intermediate');
    const visible = radius > 0.001;
    
    if (!visible) return;
    
    const geometry = new THREE.SphereGeometry(radius, 32, 32);
    
    jointPositions.forEach(pos => {
      const sphere = new THREE.Mesh(
        geometry,
        this.materials.intermediateNode.clone()
      );
      sphere.position.copy(pos);
      sphere.userData.isIntermediate = true;
      sphere.visible = visible;
      this.sceneManager.add(sphere);
      this.intermediateAtoms.push(sphere);
    });
  }
  
  updateNormalIndicators(frames, positions) {
    const THREE = this.THREE;
    const params = this.base.getParams();
    
    this.normalIndicators.forEach(obj => this.sceneManager.remove(obj));
    this.normalIndicators = [];
    
    const size = params.normalIndicatorSize * params.nodeScale;
    if (size < 0.01) return;
    
    const arrowLength = 0.8 * size * 2;
    const headLength = 0.15 * size * 2;
    const headWidth = 0.1 * size * 2;
    
    for (let i = 0; i < frames.length; i++) {
      const pos = positions[i];
      const { T, B, N } = frames[i];
      
      const normalArrow = new THREE.ArrowHelper(N, pos, arrowLength, 0xc9a66b, headLength, headWidth);
      this.sceneManager.add(normalArrow);
      this.normalIndicators.push(normalArrow);
      
      const binormalArrow = new THREE.ArrowHelper(B, pos, arrowLength, 0x7eb5a6, headLength, headWidth);
      this.sceneManager.add(binormalArrow);
      this.normalIndicators.push(binormalArrow);
    }
  }
  
  applySmoothing(originalPoints, weight) {
    const THREE = this.THREE;
    const smoothed = [];
    const n = originalPoints.length;
    
    for (let i = 0; i < n; i++) {
      if (i === 0 || i === n - 1) {
        smoothed.push(originalPoints[i].clone());
      } else {
        const P = originalPoints[i];
        const A = originalPoints[i - 1];
        const B = originalPoints[i + 1];
        
        const AB = new THREE.Vector3().subVectors(B, A);
        const AP = new THREE.Vector3().subVectors(P, A);
        const abLengthSq = AB.lengthSq();
        
        let nearestPoint;
        if (abLengthSq < 0.0001) {
          nearestPoint = A.clone();
        } else {
          const t = AP.dot(AB) / abLengthSq;
          const tClamped = Math.max(0, Math.min(1, t));
          nearestPoint = A.clone().addScaledVector(AB, tClamped);
        }
        
        const smoothedPoint = P.clone().lerp(nearestPoint, weight);
        smoothed.push(smoothedPoint);
      }
    }
    
    return smoothed;
  }
  
  rebuildRibbon() {
    const THREE = this.THREE;
    const params = this.base.getParams();
    
    this.ribbonMeshes.forEach(mesh => {
      mesh.geometry.dispose();
      this.sceneManager.remove(mesh);
    });
    this.ribbonMeshes = [];
    
    if (this.chains && this.chains.size > 0) {
      this.rebuildMultiChainRibbon();
    } else {
      this.rebuildSingleRibbon();
    }
  }
  
  rebuildSingleRibbon() {
    const THREE = this.THREE;
    const params = this.base.getParams();
    
    let workingPoints = this.controlPoints.map(p => p.clone());
    if (params.smoothing > 0) {
      workingPoints = this.applySmoothing(this.controlPoints, params.smoothing);
    }
    
    let displayPositions = this.controlPoints;
    if (params.controlNodeSmoothing > 0) {
      displayPositions = this.applySmoothing(this.controlPoints, params.controlNodeSmoothing);
    }
    displayPositions.forEach((p, i) => {
      if (this.controlAtoms[i]) {
        this.controlAtoms[i].position.copy(p);
      }
    });
    
    const result = this.buildRibbonForChain(workingPoints, this.controlPointRolls, 0);
    if (result) {
      if (params.width > 0.01 && params.thickness > 0.01) {
        const ribbonMesh = new THREE.Mesh(result.geometry, this.materials.ribbon);
        this.sceneManager.add(ribbonMesh);
        this.ribbonMeshes.push(ribbonMesh);
      }
      
      this.updateIntermediateAtoms(result.jointPositions);
      this.updateNormalIndicators(result.frames, workingPoints);
      
      return {
        segmentCount: result.segments.length,
        pointCount: workingPoints.length,
        chainCount: 1
      };
    }
    return null;
  }
  
  rebuildMultiChainRibbon() {
    const THREE = this.THREE;
    const params = this.base.getParams();
    
    const allJointPositions = [];
    let totalSegments = 0;
    let totalResidues = 0;
    
    let chainIndex = 0;
    for (const [chainId, chainData] of this.chains) {
      let workingPoints = chainData.points.map(p => p.clone());
      
      if (params.smoothing > 0) {
        workingPoints = this.applySmoothing(chainData.points, params.smoothing);
      }
      
      const result = this.buildRibbonForChain(workingPoints, chainData.rolls, chainIndex);
      if (result) {
        if (params.width > 0.01 && params.thickness > 0.01) {
          const color = this.chainColors[chainIndex % this.chainColors.length];
          const material = new THREE.MeshStandardMaterial({
            color: color,
            metalness: 0.4,
            roughness: 0.35,
            side: THREE.FrontSide
          });
          
          const mesh = new THREE.Mesh(result.geometry, material);
          this.sceneManager.add(mesh);
          this.ribbonMeshes.push(mesh);
        }
        
        allJointPositions.push(...result.jointPositions);
        totalSegments += result.segments.length;
        totalResidues += workingPoints.length;
      }
      
      chainIndex++;
    }
    
    this.updateControlAtomPositions();
    this.updateIntermediateAtoms(allJointPositions);
    
    return {
      segmentCount: totalSegments,
      pointCount: totalResidues,
      chainCount: this.chains.size
    };
  }
  
  updateControlAtomPositions() {
    const params = this.base.getParams();
    if (!this.chains) return;
    
    let atomIndex = 0;
    for (const [chainId, chainData] of this.chains) {
      let displayPositions = chainData.points;
      
      if (params.controlNodeSmoothing > 0) {
        displayPositions = this.applySmoothing(chainData.points, params.controlNodeSmoothing);
      }
      
      for (let i = 0; i < chainData.points.length; i++) {
        if (this.controlAtoms[atomIndex]) {
          this.controlAtoms[atomIndex].position.copy(displayPositions[i]);
        }
        atomIndex++;
      }
    }
  }
  
  buildRibbonForChain(points, rolls, chainIndex) {
    const THREE = this.THREE;
    const params = this.base.getParams();
    
    if (points.length < 2) return null;
    
    const frames = LocalFrameComputer.computeAllFrames(points, THREE);
    
    for (let i = 0; i < frames.length; i++) {
      const roll = rolls[i] || 0;
      if (roll !== 0) {
        const rollRad = THREE.MathUtils.degToRad(roll);
        frames[i].B.applyAxisAngle(frames[i].T, rollRad);
        frames[i].N = new THREE.Vector3().crossVectors(frames[i].B, frames[i].T).normalize();
      }
    }
    
    const segments = [];
    const jointPositions = [];
    
    for (let i = 0; i < points.length - 1; i++) {
      const segment = new BiarcSegment3D(
        points[i],
        points[i + 1],
        frames[i],
        frames[i + 1],
        THREE
      );
      segments.push(segment);
      
      const joint = segment.getJointPoint();
      if (joint) {
        jointPositions.push(joint);
      }
    }
    
    if (segments.length === 0) return null;
    
    const geometry = RibbonGeometryBuilder.build(
      segments,
      params.width,
      params.thickness,
      this.samplesPerSegment,
      THREE
    );
    
    return { geometry, jointPositions, segments, frames };
  }
  
  updateControlPointCount(newCount) {
    const THREE = this.THREE;
    const oldCount = this.controlPoints.length;
    
    if (newCount > oldCount) {
      for (let i = oldCount; i < newCount; i++) {
        const lastPoint = this.controlPoints[this.controlPoints.length - 1];
        const secondLast = this.controlPoints[this.controlPoints.length - 2];
        const dir = new THREE.Vector3().subVectors(lastPoint, secondLast).normalize();
        const newPoint = lastPoint.clone().addScaledVector(dir, 3);
        newPoint.y += (Math.random() - 0.5) * 2;
        newPoint.z += (Math.random() - 0.5) * 2;
        this.controlPoints.push(newPoint);
        this.controlPointRolls.push(0);
      }
    } else if (newCount < oldCount) {
      this.controlPoints = this.controlPoints.slice(0, newCount);
      this.controlPointRolls = this.controlPointRolls.slice(0, newCount);
    }
    
    this.createControlAtoms();
  }
  
  updateAtomVisualization() {
    const params = this.base.getParams();
    
    // Update scale if atomScale parameter exists
    if (params.atomScale !== undefined) {
      this.atomRenderer.updateAtomScale(params.atomScale);
    }
    
    this.atomRenderer.setOpacity(params.atomOpacity);
    this.atomRenderer.setRange(params.atomRangeStart, params.atomRangeEnd);
  }
  
  updateBondVisualization() {
    const params = this.base.getParams();
    
    // Update bond parameters
    if (params.bondRadius !== undefined) {
      this.bondRenderer.setRadius(params.bondRadius);
    }
    
    if (params.bondHalfColor !== undefined) {
      this.bondRenderer.setHalfColor(params.bondHalfColor);
    }
    
    if (params.bondGreyBlend !== undefined) {
      this.bondRenderer.setGreyBlend(params.bondGreyBlend);
    }
    
    if (params.bondRingPink !== undefined) {
      this.bondRenderer.setRingPink(params.bondRingPink);
    }
    
    this.bondRenderer.setOpacity(params.bondOpacity);
    this.bondRenderer.setAtomRange(params.atomRangeStart, params.atomRangeEnd);
  }
  
  setupInteraction() {
    const THREE = this.THREE;
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    let selectedAtom = null;
    let isDragging = false;
    const dragPlane = new THREE.Plane();
    const intersection = new THREE.Vector3();
    let dragStartVisualPos = new THREE.Vector3();
    
    // Prevent context menu on right-click
    this.sceneManager.renderer.domElement.addEventListener('contextmenu', (event) => {
      event.preventDefault();
    });
    
    const onMouseDown = (event) => {
      if (event.button !== 2) return; //right mouse button only
      
      const rect = this.sceneManager.renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      
      raycaster.setFromCamera(mouse, this.sceneManager.camera);
      const intersects = raycaster.intersectObjects(
        this.controlAtoms.filter(a => a.visible)
      );
      
      if (intersects.length > 0) {
        selectedAtom = intersects[0].object;
        selectedAtom.material = this.materials.controlNodeHover.clone();
        isDragging = true;
        this.sceneManager.controls.enabled = false;
        
        dragStartVisualPos.copy(selectedAtom.position);
        
        // Set drag plane perpendicular to camera view direction
        const cameraDirection = new THREE.Vector3();
        this.sceneManager.camera.getWorldDirection(cameraDirection);
        dragPlane.setFromNormalAndCoplanarPoint(cameraDirection, selectedAtom.position);
      }
    };
    
    const onMouseMove = (event) => {
      const rect = this.sceneManager.renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      
      if (isDragging && selectedAtom) {
        const params = this.base.getParams();
        raycaster.setFromCamera(mouse, this.sceneManager.camera);
        
        if (raycaster.ray.intersectPlane(dragPlane, intersection)) {
          const newVisualPos = intersection.clone();
          
          const visualDelta = newVisualPos.clone().sub(dragStartVisualPos);
          
          const w = params.controlNodeSmoothing;
          const inverseFactor = w < 0.95 ? 1 / (1 - w) : 20;
          const underlyingDelta = visualDelta.clone().multiplyScalar(inverseFactor);
          
          const atomIndex = selectedAtom.userData.index;
          
          if (this.chains && this.atomToChainMap[atomIndex]) {
            const mapping = this.atomToChainMap[atomIndex];
            const chainData = this.chains.get(mapping.chainId);
            if (chainData) {
              chainData.points[mapping.localIndex].add(underlyingDelta);
            }
          } else if (!this.isProteinMode) {
            this.controlPoints[atomIndex].add(underlyingDelta);
          }
          
          dragStartVisualPos.copy(newVisualPos);
          
          this.base.render();
        }
      }
    };
    
    const onMouseUp = () => {
      if (selectedAtom) {
        selectedAtom.material = this.materials.controlNode.clone();
        selectedAtom = null;
      }
      isDragging = false;
      this.sceneManager.controls.enabled = true;
    };
    
    this.sceneManager.renderer.domElement.addEventListener('mousedown', onMouseDown);
    this.sceneManager.renderer.domElement.addEventListener('mousemove', onMouseMove);
    this.sceneManager.renderer.domElement.addEventListener('mouseup', onMouseUp);
    this.sceneManager.renderer.domElement.addEventListener('mouseleave', onMouseUp);
  }
  
  async loadProtein(pdbId) {
    const THREE = this.THREE;
    
    this.base.setStatus(`Fetching ${pdbId} structure...`);
    this.base.clearInfo();
    this.base.setControlEnabled('proteinSelector', false);
    
    try {
      const response = await fetch(`https://files.rcsb.org/download/${pdbId}.pdb`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const pdbContent = await response.text();
      this.base.setStatus('Parsing PDB file...');
      
      const structure = PDBParser.parse(pdbContent, true);
      const chainsCoords = PDBParser.extractChainsCoords(structure, THREE);
      const chainIds = Array.from(chainsCoords.keys());
      
      if (chainIds.length === 0) {
        throw new Error('Not enough backbone atoms found');
      }
      
      const { chains: normalizedChains, scale, centroid } = PDBParser.normalizeChainsCoordinates(chainsCoords, THREE, 15);
      
      this.modelScale = scale;
      
      // Normalize all atoms
      const normalizedAllAtoms = PDBParser.normalizeAllAtoms(structure.allAtoms, centroid, scale, THREE);
      
      this.chains = new Map();
      this.atomToChainMap = [];
      this.currentPdbId = pdbId;
      let totalResidues = 0;
      
      for (const [chainId, coords] of normalizedChains) {
        this.chains.set(chainId, {
          points: coords,
          originalPoints: coords.map(p => p.clone()),
          rolls: new Array(coords.length).fill(0)
        });
        for (let i = 0; i < coords.length; i++) {
          this.atomToChainMap.push({ chainId, localIndex: i });
        }
        totalResidues += coords.length;
      }
      
      this.controlPoints = [];
      this.controlPointRolls = [];
      this.isProteinMode = true;
      
      const allPoints = [];
      for (const chainData of this.chains.values()) {
        allPoints.push(...chainData.points);
      }
      this.controlPoints = allPoints;
      
      this.base.setControlEnabled('numPoints', false);
      
      this.createControlAtoms();
      
      // Set up atom visualization
      this.atomRenderer.setAtoms(normalizedAllAtoms, scale);
      this.updateAtomVisualization();
      
      // Detect and render bonds
      this.bondRenderer.detectAndSetBonds(normalizedAllAtoms, scale);
      this.updateBondVisualization();
      
      this.sceneManager.resetCamera();
      
      const chainInfo = chainIds.map(cId => {
        const count = this.chains.get(cId).points.length;
        return `${cId}: ${count}`;
      }).join(', ');
      
      this.base.setInfo(`
        <strong>PDB ID: ${pdbId}</strong><br>
        Chains: ${chainIds.join(', ')} (${chainIds.length} separate)<br>
        Residues per chain: ${chainInfo}<br>
        Total residues: ${totalResidues}<br>
        Total atoms: ${structure.totalAllAtoms}<br>
        ${structure.title ? `<br>${structure.title}` : ''}
      `);
      
      this.base.setStatus(`${pdbId} loaded! (${chainIds.length} chain${chainIds.length > 1 ? 's' : ''}, ${structure.totalAllAtoms} atoms)`);
      
      return { success: true, totalResidues, chainIds, totalAtoms: structure.totalAllAtoms };
      
    } catch (error) {
      console.error(`Error loading ${pdbId}:`, error);
      this.base.setStatus(`Error: ${error.message}`, true);
      return { success: false, error: error.message };
    } finally {
      this.base.setControlEnabled('proteinSelector', true);
    }
  }
  
  resetToDemo() {
    const THREE = this.THREE;
    
    this.isProteinMode = false;
    this.chains = null;
    this.atomToChainMap = [];
    this.currentPdbId = null;
    this.modelScale = 1;
    
    this.controlPoints = [
      new THREE.Vector3(-6, 0, 0),
      new THREE.Vector3(-3, 2, 2),
      new THREE.Vector3(0, -1, -1),
      new THREE.Vector3(3, 1, 2),
      new THREE.Vector3(6, 0, 0)
    ];
    
    this.controlPointRolls = [0, 0, 0, 0, 0];
    
    this.base.setControlEnabled('numPoints', true);
    this.base.setSelectValue('proteinSelector', '');
    
    this.createControlAtoms();
    this.atomRenderer.clear();
    this.bondRenderer.clear();
    this.sceneManager.resetCamera();
    
    this.base.clearInfo();
    this.base.clearStatus();
  }
}

// Export for global scope
if (typeof window !== 'undefined') {
  window.CPK_ATOM_DATA = CPK_ATOM_DATA;
  window.BOND_GREY = BOND_GREY;
  window.BOND_RING_PINK = BOND_RING_PINK;
  window.MOLAM_PRESETS = MOLAM_PRESETS;
  window.PDBParser = PDBParser;
  window.ArcMath = ArcMath;
  window.LocalFrameComputer = LocalFrameComputer;
  window.BiarcSegment3D = BiarcSegment3D;
  window.RibbonGeometryBuilder = RibbonGeometryBuilder;
  window.AtomRenderer = AtomRenderer;
  window.BondRenderer = BondRenderer;
  window.MolamScene = MolamScene;
  window.MolamApp = MolamApp;
}