/**
 * proteins.js
 * Centralized configuration for protein visualization colors and properties.
 */

const ProteinStyle = {
    // 1. Amino Acid Colors
    aaColors: {
        'G': '#FFFFFF', // White
        'A': '#CCCCCC', // Light Grey
        'T': '#ADD8E6', // Light Blue
        'S': '#9292FE', // Dark Blue
        'D': '#FF6666', // Red
        'E': '#FF0000', // Red (Darker)
        'Q': '#800080', // Purple
        'N': '#FF00FF', // Magenta
        'V': '#A2CA2E', // Green
        'L': '#32CD32', // Lime Green
        'I': '#ACF1AC', // Forest Green
        'K': '#00FFFF', // Cyan
        'R': '#00BFFF', // Deep Sky Blue
        'M': '#00FF70', // Sea Green
        'C': '#EEFF00', // Lime Yellow
        'F': '#D2691E', // Chocolate
        'Y': '#A0522D', // Sienna
        'W': '#FFA18A', // Salmon
        'H': '#4682B4', // Steel Blue
        'P': '#ffd142', // Gold
        'X': '#666666'  // Unknown
    },

    // 2. Periodicity Colors (Rainbow)
    periodColors: {
        0: '#444444', // Grey (None)
        2: '#FF4136', // Red
        3: '#FF851B', // Orange
        4: '#FFDC00', // Yellow
        5: '#2ECC40', // Green
        6: '#0074D9', // Blue
        7: '#B10DC9'  // Violet
    },

    // 3. Feature Colors (Domains, Regions, etc.)
    featureColors: {
        CHAIN: '#d1d5db',
        DOMAIN: '#3b82f6',
        REGION: '#f59e0b',
        COILED: '#22c55e',
        COMPBIAS: '#a855f7',
        MOD_RES: '#ef4444',
        TRANSMEM: '#06b6d4',
        REPEAT: '#ec4899',
        ZN_FING: '#8b5cf6',
        MOTIF: '#14b8a6',
        BINDING: '#f97316',
        ACT_SITE: '#dc2626',
        CONFLICT: '#6b7280',
        SIGNAL: '#84cc16',
        PROPEP: '#a3a3a3',
        ALIGN: '#93c5fd'
    },

    // 4. Canonical Sort Order and Rank
    canonicalOrderStr: "G A T S D E Q N V L I K R M C F Y W H P",

    _aaRank: null,

    get aaRank() {
        if (!this._aaRank) {
            this._aaRank = {};
            this.canonicalOrderStr.split(' ').forEach((aa, i) => this._aaRank[aa] = i);
        }
        return this._aaRank;
    }
};
