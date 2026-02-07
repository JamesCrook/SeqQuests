// ============================================================
// Mini Vector Library
// ============================================================

const V = {
  create: (x, y) => ({ x, y }),
  add: (a, b) => ({ x: a.x + b.x, y: a.y + b.y }),
  sub: (a, b) => ({ x: a.x - b.x, y: a.y - b.y }),
  scale: (v, s) => ({ x: v.x * s, y: v.y * s }),
  lerp: (a, b, t) => ({ x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t }),
  dist: (a, b) => Math.hypot(b.x - a.x, b.y - a.y),
  fromPolar: (r, angle) => ({ x: r * Math.cos(angle), y: r * Math.sin(angle) }),
  addPolar: (center, r, angle) => V.add(center, V.fromPolar(r, angle)),
  mid: (a, b) => V.scale(V.add(a, b), 0.5),
  perp: (v) => ({ x: -v.y, y: v.x }),
  normalize: (v) => {
    const len = Math.hypot(v.x, v.y);
    return len > 0 ? V.scale(v, 1 / len) : { x: 0, y: 0 };
  },
  rotate: (v, center, angle) => {
    const cos = Math.cos(angle), sin = Math.sin(angle);
    const d = V.sub(v, center);
    return V.add(center, { x: d.x * cos - d.y * sin, y: d.x * sin + d.y * cos });
  }
};

// Scalar lerp utility
const lerp = (a, b, t) => a + (b - a) * t;


// ============================================================
// WarpedPolygon - Unified quadrilateral with bend-based arc edges
// ============================================================

const WarpedPolygon = {
  path(corners, bends) {
    let d = `M ${corners[0].x} ${corners[0].y}`;
    l = corners.length;
    for (let i = 0; i < l; i++) {
      d += this._edge(corners[i], corners[(i + 1) % l], bends[i]);
    }
    return d + ' Z';
  },
  
  topPath(corners, bends) {
    l = corners.length;
    const p1 = corners[2%l], p2 = corners[3%l];
    return `M ${p1.x} ${p1.y}` + this._edge(p1, p2, bends[2%l]);
  },
  
  _getArcParams(p1, p2, bend) {
    const chord = V.sub(p2, p1);
    const chordLength = Math.hypot(chord.x, chord.y);
    const midpoint = V.mid(p1, p2);
    
    const halfBend = Math.abs(bend) / 2;
    const sinHalf = Math.sin(halfBend);
    if (sinHalf < 0.0001) return null;
    
    const radius = chordLength / (2 * sinHalf);
    const distToCenter = radius * Math.cos(halfBend);
    const perp = V.normalize(V.perp(chord));
    const sign = bend > 0 ? 1 : -1;
    const center = V.add(midpoint, V.scale(perp, -sign * distToCenter));
    
    const startAngle = Math.atan2(p1.y - center.y, p1.x - center.x);
    const endAngle = Math.atan2(p2.y - center.y, p2.x - center.x);
    const counterclockwise = bend > 0;
    
    return { center, radius, startAngle, endAngle, counterclockwise };
  },
  
  _edge(p1, p2, bend) {
    const chord = V.dist(p1, p2);
    if (chord < 0.001) return '';
    
    if (!bend || Math.abs(bend) < 0.01) {
      return ` L ${p2.x} ${p2.y}`;
    }
    
    const arcParams = this._getArcParams(p1, p2, bend);
    if (!arcParams) {
      return ` L ${p2.x} ${p2.y}`;
    }
    
    const { radius, counterclockwise, startAngle, endAngle } = arcParams;
    
    if (radius > chord * 100) {
      return ` L ${p2.x} ${p2.y}`;
    }
    
    let angleDiff = endAngle - startAngle;
    if (counterclockwise) {
      if (angleDiff < 0) angleDiff += Math.PI * 2;
    } else {
      if (angleDiff > 0) angleDiff -= Math.PI * 2;
    }
    const largeArc = Math.abs(angleDiff) > Math.PI ? 0 : 1;
    const sweep = counterclockwise ? 0 : 1;
    
    return ` A ${radius} ${radius} 0 ${largeArc} ${sweep} ${p2.x} ${p2.y}`;
  }
};
