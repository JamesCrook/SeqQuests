# Multiscroller Documentation

## Overview

The Multiscroller is a hierarchical data browser that displays tree-structured data across multiple synchronized columns. It provides an interface for navigating parent-child relationships in large datasets without needing to know the total size of the tree in advance.

## Core Concept

The multiscroller operates on a **cursor-based tree interface** that supports three fundamental operations:

- **`next(cursor, level)`** - Move to the next sibling at the current level
- **`prev(cursor, level)`** - Move to the previous sibling at the current level  
- **`descend(cursor, level)`** - Move down one level to the first child

This design allows the multiscroller to work with datasets of unknown or very large size, loading data on-demand as the user explores the tree.

## Visual Layout

The interface consists of multiple columns displayed side-by-side, where:

- Each column represents one level of the tree hierarchy
- Items within a column can be scrolled by clicking and dragging vertically
- There are **no scrollbars** - all scrolling is done via click-and-drag
- Selected items are highlighted with a subtle background color change

## Interaction Model

### Selection Behavior

When you **click** an item in any column:

1. The clicked item is selected in its column
2. All columns to the left are populated with just the parents (ancestors) of the selected item and these are selected.
3. The next column to the right is populated with just the children of the selected item, and these are selected. 
4. This cascades through all subsequent columns - grandchildren are loaded and selected, etc.

**Example**: Clicking a range in column 1 selects all IDs in that range (column 2), which in turn selects all corresponding full records (column 3).

### Scrolling Behavior

When you **drag** a selected item vertically:

1. The dragged item scrolls within its column
2. All other columns with selections scroll **proportionally**
3. The proportional relationship is maintained such that:
   - When the top of the dragged item reaches the top of its viewport, the tops of all other selections align with their viewport tops
   - When the bottom of the dragged item reaches the bottom of its viewport, the bottoms of all other selections align with their viewport bottoms
   - Positions in between are linearly interpolated

This creates a synchronized scrolling experience across the hierarchy, making it easy to see related items at all levels simultaneously.

### Dynamic Loading

As you scroll, the multiscroller automatically:

- Detects when blank space is becoming visible at the top or bottom of any column
- Loads additional items using `prev()` or `next()` operations
- Maintains a buffer of items above and below the visible area
- Adjusts internal indices and scroll positions to ensure smooth scrolling

This happens for **all columns simultaneously** during a drag operation, ensuring all viewports remain filled with content (unless the end of the data is reached).

## Architecture

### Column Class

Each column manages:
- A list of items with their cursors, data, and measured heights
- Selected indices (supports multiple selections)
- Scroll offset (vertical position of content)
- Dynamic loading of items as needed
- DOM rendering and updates

### Multiscroller Class

The multiscroller coordinates:
- Creation and management of all columns
- Propagation of selection events across columns
- Synchronized scrolling during drag operations
- Triggering of dynamic loading across all columns

### Tree Interface

The tree implementation provides:
- Cursor-based navigation (opaque cursor objects)
- Data rendering for each level
- Parent-child relationship traversal

## Performance Optimizations

1. **Lazy DOM updates**: The render method only updates CSS classes when item count hasn't changed, avoiding expensive DOM rebuilds during scrolling
2. **Measured heights**: Item heights are measured once and cached, avoiding repeated layout calculations
3. **Bounded loading**: Dynamic loading adds a maximum number of items per scroll to prevent UI freezing
4. **Buffer zones**: Items are loaded with buffers above and below the visible area to reduce loading frequency

---

## Mock Data: SwissProt Tree

The current implementation uses mock protein sequence data structured as a three-level hierarchy:

### Level 0: ID Ranges

**Format**: `P10000 - P10099`, `P10100 - P10199`, etc.

- Each range contains 100 sequential protein IDs
- Ranges start at P10000 and increment by 100
- Displayed in the leftmost column
- Styled with bold, light blue text

### Level 1: ID and Name

**Format**: `P12345 - Hemoglobin`

- Individual protein identifiers with associated names
- IDs follow the format P##### (5-digit zero-padded number)
- Protein names are randomly selected from a predefined list:
  - Hemoglobin, Insulin, Collagen, Keratin, Actin
  - Myosin, Tubulin, Albumin, Immunoglobulin, Fibrinogen
  - Cytochrome, Catalase, Lysozyme, Pepsin, Trypsin
- Each ID consistently maps to the same name (via seeded random generation)
- IDs displayed in orange/peach, names in light green

### Level 2: Full Record

**Format**: Complete sequence data for a protein

Contains:
- Header with protein ID and name
- Amino acid sequence (100-500 amino acids in length)
- Sequence uses standard single-letter amino acid codes: `ACDEFGHIKLMNPQRSTVWY`
- Sequences are displayed in monospace font with letter spacing, wrapped at 60 characters per line

### Seeded Random Generation

All random elements (protein names, sequence lengths, amino acid sequences) are generated using a **seeded pseudo-random number generator** based on the protein ID. This ensures:

- The same protein ID always produces the same name and sequence
- Data is consistent across sessions
- No backend storage is required
- The illusion of real data is maintained

### Cursor Structure

**Level 0 cursors**: Simple integers (0, 1, 2, ...) representing range indices

**Level 1 cursors**: Objects with structure `{ rangeStart: number, offset: number }`
- `rangeStart`: The starting ID of the range (e.g., 10000, 10100, 10200)
- `offset`: Position within the range (0-99)

**Level 2 cursors**: Same as level 1 (the cursor represents the protein ID, which is the same for both ID-and-name and full-record views)

### Data Boundaries

- Total ranges: 1000 (covering IDs from P10000 to P109999)
- IDs per range: 100
- Total possible proteins: 100,000
- Sequence length: Random between 100-500 amino acids per protein

This mock data provides enough volume to test scrolling performance and hierarchical navigation while remaining entirely client-side.