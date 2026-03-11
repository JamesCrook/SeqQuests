#!/usr/bin/env python3
"""
Generate a zig-zag (extended) PDB file for any amino acid sequence.

Backbone follows a planar zig-zag in the XY plane with characteristic
peptide bond angles. Side chains branch off CA in ±Z, rotated 90° about
the CA-CB axis (except proline). Carbonyl oxygens are pushed outward to
avoid false bonding to the next residue's nitrogen.
"""

import math
import sys

# --- Amino acid data ---

AA_1TO3 = {
    'G': 'GLY', 'A': 'ALA', 'V': 'VAL', 'L': 'LEU', 'I': 'ILE',
    'P': 'PRO', 'F': 'PHE', 'W': 'TRP', 'M': 'MET', 'S': 'SER',
    'T': 'THR', 'C': 'CYS', 'Y': 'TYR', 'H': 'HIS', 'D': 'ASP',
    'E': 'GLU', 'N': 'ASN', 'Q': 'GLN', 'K': 'LYS', 'R': 'ARG',
}

# Simplified side-chain atoms beyond CB.
# Each entry: list of (atom_name, dx, dy, dz) relative to CB position.
SIDECHAIN_EXTRA = {
    'GLY': [],
    'ALA': [],
    'VAL': [(' CG1', 0.0, 1.2, 0.5), (' CG2', 0.0, -1.2, 0.5)],
    'LEU': [(' CG ', 0.0, 0.0, 1.5), (' CD1', 0.0, 1.2, 2.2), (' CD2', 0.0, -1.2, 2.2)],
    'ILE': [(' CG1', 0.0, 1.0, 1.0), (' CG2', 0.0, -1.2, 0.5), (' CD1', 0.0, 1.0, 2.5)],
    'PRO': [(' CG ', 1.0, 0.0, 1.0), (' CD ', 1.5, 0.0, 0.0)],
    'PHE': [(' CG ', 0.0, 0.0, 1.4), (' CD1', 0.0, 1.2, 2.1), (' CD2', 0.0, -1.2, 2.1),
            (' CE1', 0.0, 1.2, 3.5), (' CE2', 0.0, -1.2, 3.5), (' CZ ', 0.0, 0.0, 4.2)],
    'TRP': [(' CG ', 0.0, 0.0, 1.4), (' CD1', 0.0, 1.1, 2.1), (' CD2', 0.0, -0.7, 2.3),
            (' NE1', 0.0, 0.7, 3.2), (' CE2', 0.0, -0.4, 3.5), (' CE3', 0.0, -1.9, 2.8),
            (' CZ2', 0.0, -1.4, 4.4), (' CZ3', 0.0, -2.7, 3.7), (' CH2', 0.0, -2.4, 4.7)],
    'MET': [(' CG ', 0.0, 0.0, 1.5), (' SD ', 0.0, 0.0, 3.0), (' CE ', 0.0, 1.2, 3.8)],
    'SER': [(' OG ', 0.0, 0.0, 1.4)],
    'THR': [(' OG1', 0.0, 1.1, 0.8), (' CG2', 0.0, -1.1, 0.8)],
    'CYS': [(' SG ', 0.0, 0.0, 1.8)],
    'TYR': [(' CG ', 0.0, 0.0, 1.4), (' CD1', 0.0, 1.2, 2.1), (' CD2', 0.0, -1.2, 2.1),
            (' CE1', 0.0, 1.2, 3.5), (' CE2', 0.0, -1.2, 3.5), (' CZ ', 0.0, 0.0, 4.2),
            (' OH ', 0.0, 0.0, 5.6)],
    'HIS': [(' CG ', 0.0, 0.0, 1.4), (' ND1', 0.0, 1.0, 2.2), (' CD2', 0.0, -0.8, 2.3),
            (' CE1', 0.0, 0.6, 3.4), (' NE2', 0.0, -0.6, 3.4)],
    'ASP': [(' CG ', 0.0, 0.0, 1.5), (' OD1', 0.0, 1.1, 2.2), (' OD2', 0.0, -1.1, 2.2)],
    'GLU': [(' CG ', 0.0, 0.0, 1.5), (' CD ', 0.0, 0.0, 3.0),
            (' OE1', 0.0, 1.1, 3.7), (' OE2', 0.0, -1.1, 3.7)],
    'ASN': [(' CG ', 0.0, 0.0, 1.5), (' OD1', 0.0, 1.1, 2.2), (' ND2', 0.0, -1.1, 2.2)],
    'GLN': [(' CG ', 0.0, 0.0, 1.5), (' CD ', 0.0, 0.0, 3.0),
            (' OE1', 0.0, 1.1, 3.7), (' NE2', 0.0, -1.1, 3.7)],
    'LYS': [(' CG ', 0.0, 0.0, 1.5), (' CD ', 0.0, 0.0, 3.0),
            (' CE ', 0.0, 0.0, 4.5), (' NZ ', 0.0, 0.0, 5.8)],
    'ARG': [(' CG ', 0.0, 0.0, 1.5), (' CD ', 0.0, 0.0, 3.0),
            (' NE ', 0.0, 0.0, 4.5), (' CZ ', 0.0, 0.0, 5.5),
            (' NH1', 0.0, 1.1, 6.2), (' NH2', 0.0, -1.1, 6.2)],
}

# --- Backbone geometry ---
BOND_N_CA  = 1.47
BOND_CA_C  = 1.52
BOND_C_N   = 1.33     # peptide bond
BOND_C_O   = 2.50     # pushed out (real ~1.24) to avoid false O–N bonding
BOND_CA_CB = 1.52

# Bond angles at backbone atoms (degrees)
ANGLE_AT_N  = 121.0   # C(prev)–N–CA
ANGLE_AT_CA = 111.0   # N–CA–C   (near tetrahedral)
ANGLE_AT_C  = 116.0   # CA–C–N(next)


def pdb_atom_line(serial, name, resname, chain, resseq, x, y, z, element=None):
    """Format one ATOM record in PDB fixed-width format."""
    if element is None:
        element = name.strip()[0]
    return (
        f"ATOM  {serial:5d} {name:4s} {resname:3s} {chain:1s}{resseq:4d}    "
        f"{x:8.3f}{y:8.3f}{z:8.3f}{1.00:6.2f}{0.00:6.2f}          {element:>2s}\n"
    )


def _angle_diff(a, b):
    """Signed angular difference, wrapped to [-pi, pi]."""
    d = a - b
    while d > math.pi:
        d -= 2 * math.pi
    while d < -math.pi:
        d += 2 * math.pi
    return d


def generate_linear_pdb(sequence, chain='A'):
    """
    Build a zig-zag PDB string for the given one-letter amino acid sequence.

    Backbone zig-zags in the XY plane with characteristic peptide angles.
    Side chains branch off CA in ±Z (alternating), rotated 90° about CA-CB
    (except proline).  Carbonyl O is pushed outward to prevent false bonds.
    """
    lines = []
    lines.append("REMARK   Zig-zag synthetic structure for viewer testing\n")
    lines.append(f"REMARK   Sequence: {''.join(sequence)}\n")

    serial = 0

    # Running position and heading in the XY plane
    x, y = 0.0, 0.0
    heading = math.radians(-32.0)  # offset so chain runs ~along X, zig-zag in Y
    turn_sign = 1        # +1 = turn CCW, -1 = turn CW; alternates at each atom

    for i, aa1 in enumerate(sequence):
        resname = AA_1TO3.get(aa1.upper())
        if resname is None:
            print(f"Warning: unknown amino acid '{aa1}', skipping", file=sys.stderr)
            continue
        resseq = i + 1
        side_z = 1.0 if (i % 2 == 0) else -1.0  # alternating Z for sidechain

        # ── N ──
        nx, ny = x, y
        serial += 1
        lines.append(pdb_atom_line(serial, ' N  ', resname, chain, resseq,
                                   nx, ny, 0.0, 'N'))

        # ── CA ── (advance along current heading from N)
        x += BOND_N_CA * math.cos(heading)
        y += BOND_N_CA * math.sin(heading)
        cax, cay = x, y
        serial += 1
        lines.append(pdb_atom_line(serial, ' CA ', resname, chain, resseq,
                                   cax, cay, 0.0, 'C'))

        # Deflect at CA  (N–CA–C angle)
        deflection = math.radians(180.0 - ANGLE_AT_CA)
        heading += turn_sign * deflection
        turn_sign *= -1

        # ── C ──
        x += BOND_CA_C * math.cos(heading)
        y += BOND_CA_C * math.sin(heading)
        cx, cy = x, y
        serial += 1
        lines.append(pdb_atom_line(serial, ' C  ', resname, chain, resseq,
                                   cx, cy, 0.0, 'C'))

        # Deflect at C  (CA–C–N angle) — sets heading toward next N
        deflection = math.radians(180.0 - ANGLE_AT_C)
        heading += turn_sign * deflection
        turn_sign *= -1

        # ── O ── perpendicular to the outgoing C→N direction, on the side
        # AWAY from CA (follows zig-zag, stays far from next N).
        out_heading = heading
        perp_a = out_heading + math.pi / 2
        perp_b = out_heading - math.pi / 2
        to_ca = math.atan2(cay - cy, cax - cx)
        # pick the perpendicular direction more opposite to CA
        if abs(_angle_diff(perp_a, to_ca)) > abs(_angle_diff(perp_b, to_ca)):
            o_dir = perp_a
        else:
            o_dir = perp_b
        ox = cx + BOND_C_O * math.cos(o_dir)
        oy = cy + BOND_C_O * math.sin(o_dir)
        serial += 1
        lines.append(pdb_atom_line(serial, ' O  ', resname, chain, resseq,
                                   ox, oy, 0.0, 'O'))

        # ── Side chain ──
        if resname != 'GLY':
            cb_z = BOND_CA_CB * side_z
            serial += 1
            lines.append(pdb_atom_line(serial, ' CB ', resname, chain, resseq,
                                       cax, cay, cb_z, 'C'))

            extras = SIDECHAIN_EXTRA.get(resname, [])
            for atom_name, dx, dy, dz in extras:
                if resname == 'PRO':
                    # Proline: keep original orientation (ring back to N)
                    sx = cax + dx
                    sy = cay + dy
                else:
                    # Rotate 90° CCW about the CA–CB axis (Z):
                    #   (dx, dy) → (-dy, dx)
                    sx = cax + (-dy)
                    sy = cay + dx
                sz = cb_z + dz * side_z
                elem = atom_name.strip()[0]
                serial += 1
                lines.append(pdb_atom_line(serial, atom_name, resname, chain, resseq,
                                           sx, sy, sz, elem))

        # ── Advance to next N position (peptide bond) ──
        x += BOND_C_N * math.cos(heading)
        y += BOND_C_N * math.sin(heading)

        # Deflect at N for the next residue
        if i < len(sequence) - 1:
            deflection = math.radians(180.0 - ANGLE_AT_N)
            heading += turn_sign * deflection
            turn_sign *= -1

    lines.append("END\n")
    return ''.join(lines)


# --- Main ---
if __name__ == '__main__':
    DEFAULT_SEQ = list('GATSDEQNVLIKRMCFYWHP')

    if len(sys.argv) > 1:
        seq = list(sys.argv[1].upper())
    else:
        seq = DEFAULT_SEQ

    out_file = sys.argv[2] if len(sys.argv) > 2 else 'linear_protein.pdb'

    pdb_text = generate_linear_pdb(seq)
    with open(out_file, 'w') as f:
        f.write(pdb_text)
    print(f"Wrote {out_file}  ({len(seq)} residues, chain A)")