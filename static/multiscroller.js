// Seeded pseudo-random number generator
class SeededRandom {
  constructor(seed) {
    this.seed = seed;
  }

  next() {
    this.seed = (this.seed * 9301 + 49297) % 233280;
    return this.seed / 233280;
  }

  nextInt(min, max) {
    return Math.floor(this.next() * (max - min + 1)) + min;
  }

  choice(array) {
    return array[Math.floor(this.next() * array.length)];
  }
}

// SwissProt Tree Implementation
class SwissProtTree {
  constructor() {
    this.levels = [{
      name: 'id-range',
      render: this.renderIdRange.bind(this)
    }, {
      name: 'id-and-name',
      render: this.renderIdAndName.bind(this)
    }, {
      name: 'full-record',
      render: this.renderFullRecord.bind(this)
    }];

    this.proteinNames = [
      'Hemoglobin', 'Insulin', 'Collagen', 'Keratin', 'Actin',
      'Myosin', 'Tubulin', 'Albumin', 'Immunoglobulin', 'Fibrinogen',
      'Cytochrome', 'Catalase', 'Lysozyme', 'Pepsin', 'Trypsin'
    ];

    this.aminoAcids = 'ACDEFGHIKLMNPQRSTVWY';
  }

  // Level 0: ID Range (P10000-P10099, P10100-P10199, etc.)
  next(cursor, level, sameParentOnly = true) {
    if(level === 0) {
      if(cursor === null) return {
        cursor: 0,
        data: {
          rangeStart: 10000
        }
      };
      if(cursor >= 999) return null;
      return {
        cursor: cursor + 1,
        data: {
          rangeStart: (cursor + 1) * 100 + 10000
        }
      };
    } else if(level === 1) {
      const {
        rangeStart,
        offset
      } = cursor;
      if(offset >= 99) {
        if (sameParentOnly) return null;
        // Go to next range
        const parentCursor = (rangeStart - 10000) / 100;
        if (parentCursor >= 999) return null;
        const nextRangeStart = rangeStart + 100;
        return {
          cursor: {
            rangeStart: nextRangeStart,
            offset: 0
          },
          data: {
            id: nextRangeStart
          }
        };
      }
      const newOffset = offset + 1;
      return {
        cursor: {
          rangeStart,
          offset: newOffset
        },
        data: {
          id: rangeStart + newOffset
        }
      };
    } else if(level === 2) {
      if (sameParentOnly) return null;
      // Go to next ID's record
      const currentId = cursor.rangeStart + cursor.offset;
      const nextOffset = cursor.offset + 1;
      if (nextOffset >= 100) {
        // Go to next range
        const nextRangeStart = cursor.rangeStart + 100;
        if ((nextRangeStart - 10000) / 100 >= 1000) return null;
        return {
          cursor: {
            rangeStart: nextRangeStart,
            offset: 0
          },
          data: {
            id: nextRangeStart
          }
        };
      }
      return {
        cursor: {
          rangeStart: cursor.rangeStart,
          offset: nextOffset
        },
        data: {
          id: cursor.rangeStart + nextOffset
        }
      };
    }
  }

  prev(cursor, level, sameParentOnly = true) {
    if(level === 0) {
      if(cursor === null || cursor === 0) return null;
      return {
        cursor: cursor - 1,
        data: {
          rangeStart: (cursor - 1) * 100 + 10000
        }
      };
    } else if(level === 1) {
      const {
        rangeStart,
        offset
      } = cursor;
      if(offset <= 0) {
        if (sameParentOnly) return null;
        // Go to previous range's last ID
        const parentCursor = (rangeStart - 10000) / 100;
        if (parentCursor <= 0) return null;
        const prevRangeStart = rangeStart - 100;
        return {
          cursor: {
            rangeStart: prevRangeStart,
            offset: 99
          },
          data: {
            id: prevRangeStart + 99
          }
        };
      }
      const newOffset = offset - 1;
      return {
        cursor: {
          rangeStart,
          offset: newOffset
        },
        data: {
          id: rangeStart + newOffset
        }
      };
    } else if(level === 2) {
      if (sameParentOnly) return null;
      // Go to previous ID's record
      const prevOffset = cursor.offset - 1;
      if (prevOffset < 0) {
        // Go to previous range's last ID
        const prevRangeStart = cursor.rangeStart - 100;
        if ((prevRangeStart - 10000) / 100 < 0) return null;
        return {
          cursor: {
            rangeStart: prevRangeStart,
            offset: 99
          },
          data: {
            id: prevRangeStart + 99
          }
        };
      }
      return {
        cursor: {
          rangeStart: cursor.rangeStart,
          offset: prevOffset
        },
        data: {
          id: cursor.rangeStart + prevOffset
        }
      };
    }
  }

  descend(cursor, level) {
    if(level === 0) {
      // From range to first ID in range
      return {
        cursor: {
          rangeStart: cursor * 100 + 10000,
          offset: 0
        },
        data: {
          id: cursor * 100 + 10000
        }
      };
    } else if(level === 1) {
      // From ID to full record
      return {
        cursor: cursor,
        data: {
          id: cursor.rangeStart + cursor.offset
        }
      };
    } else {
      return null;
    }
  }

  ascend(cursor, level) {
    if(level === 1) {
      // From ID to range
      const rangeStart = cursor.rangeStart;
      const rangeCursor = (rangeStart - 10000) / 100;
      return {
        cursor: rangeCursor,
        data: {
          rangeStart: rangeStart
        }
      };
    } else if(level === 2) {
      // From full record to ID
      return {
        cursor: cursor,
        data: {
          id: cursor.rangeStart + cursor.offset
        }
      };
    } else {
      return null;
    }
  }

  isChildOf(childCursor, childLevel, parentCursor, parentLevel) {
    // Check if childCursor at childLevel is a descendant of parentCursor at parentLevel
    if (childLevel !== parentLevel + 1) return false;
    
    if (parentLevel === 0) {
      // Parent is a range, child is an ID
      const rangeStart = parentCursor * 100 + 10000;
      const rangeEnd = rangeStart + 99;
      const childId = childCursor.rangeStart + childCursor.offset;
      return childId >= rangeStart && childId <= rangeEnd;
    } else if (parentLevel === 1) {
      // Parent is an ID cursor, child is a full record cursor
      const parentId = parentCursor.rangeStart + parentCursor.offset;
      const childId = childCursor.rangeStart + childCursor.offset;
      return childId === parentId;
    }
    
    return false;
  }

  renderIdRange(data) {
    const start = data.rangeStart;
    const end = start + 99;
    return `<div class="id-range">P${start.toString().padStart(5, '0')} - P${end.toString().padStart(5, '0')}</div>`;
  }

  renderIdAndName(data) {
    const id = data.id;
    const rng = new SeededRandom(id);
    const name = rng.choice(this.proteinNames);
    return `<div class="id-and-name"><span class="protein-id">P${id.toString().padStart(5, '0')}</span><span class="protein-name">${name}</span></div>`;
  }

  renderFullRecord(data) {
    const id = data.id;
    const rng = new SeededRandom(id);
    const name = rng.choice(this.proteinNames);
    const seqLength = rng.nextInt(100, 500);

    let sequence = '';
    for(let i = 0; i < seqLength; i++) {
      sequence += this.aminoAcids[Math.floor(rng.next() * this.aminoAcids
        .length)];
      if((i + 1) % 60 === 0) sequence += '\n';
    }

    return `<div class="full-record">
      <div class="record-header">P${id.toString().padStart(5, '0')} - ${name}</div>
      <div class="sequence">${sequence}</div>
  </div>`;
  }
}

// Column class
class Column {
  constructor(container, tree, level) {
    this.container = container;
    this.tree = tree;
    this.level = level;
    this.items = [];
    this.selectedIndices = []; // Changed to array for multiple selections

    this.element = document.createElement('div');
    this.element.className = 'column';
    this.container.appendChild(this.element);

    this.content = document.createElement('div');
    this.content.className = 'column-content';
    this.element.appendChild(this.content);

    this.scrollOffset = 0;
    this.isDragging = false;
    this.dragStartY = 0;
    this.dragStartOffset = 0;
    this.draggedIndex = -1;

    this.setupEventListeners();
  }

  setupEventListeners() {
    this.content.addEventListener('mousedown', (e) => this.onMouseDown(e));
    document.addEventListener('mousemove', (e) => this.onMouseMove(e));
    document.addEventListener('mouseup', (e) => this.onMouseUp(e));
  }

  onMouseDown(e) {
    const itemElement = e.target.closest('.item');
    if(!itemElement) return;

    const index = parseInt(itemElement.dataset.index);
    this.selectItem(index);

    this.isDragging = true;
    this.draggedIndex = index;
    this.dragStartY = e.clientY;
    this.dragStartOffset = this.scrollOffset;
    this.content.classList.add('dragging');
    e.preventDefault();
  }

  onMouseMove(e) {
    if(!this.isDragging) return;

    const delta = e.clientY - this.dragStartY;
    this.scrollOffset = this.dragStartOffset + delta;

    this.render();

    // Notify multiscroller of drag
    if(this.onDrag) {
      this.onDrag(this.selectedIndices, delta);
    }
  }

  onMouseUp(e) {
    if(!this.isDragging) return;
    this.isDragging = false;
    this.content.classList.remove('dragging');
  }

  selectItem(index) {
    this.selectedIndices = [index];
    if(this.onSelect) {
      this.onSelect(index);
    }
    this.render();
  }

  setSelectedIndices(indices) {
    this.selectedIndices = indices;
    this.render();
  }

  async populate(startCursor, direction = 'both') {
    this.items = [];

    // Determine batch size based on level
    let batchSize = 200; // Default for middle column
    if(this.level === 0) {
      batchSize = 100; // Left column - ranges
    } else if(this.level === 2) {
      batchSize = 300; // Right column - full records
    }

    // Populate backwards
    let cursor = startCursor;
    let backItems = [];
    for(let i = 0; i < batchSize / 2; i++) {
      const result = this.tree.prev(cursor, this.level);
      if(!result) break;
      backItems.unshift({
        cursor: result.cursor,
        data: result.data
      });
      cursor = result.cursor;
    }

    // Add start item
    const startResult = startCursor !== null ? {
      cursor: startCursor,
      data: this.getCursorData(startCursor)
    } : this.tree.next(null, this.level);
    if(startResult) {
      this.items = [...backItems, {
        cursor: startResult.cursor,
        data: startResult.data
      }];
      cursor = startResult.cursor;

      // Populate forwards
      for(let i = 0; i < batchSize / 2; i++) {
        const result = this.tree.next(cursor, this.level);
        if(!result) break;
        this.items.push({
          cursor: result.cursor,
          data: result.data
        });
        cursor = result.cursor;
      }
    }

    // 1. Render the DOM
    this.render(); // This will call rebuildDOM()

    // 2. Wait for the browser to finish layout
    await new Promise(resolve => requestAnimationFrame(resolve));
    
    // 3. NOW measure the items that are actually on screen
    this.measureItems();
  }

  getCursorData(cursor) {
    if(this.level === 0) {
      return {
        rangeStart: cursor * 100 + 10000
      };
    } else if(this.level === 1) {
      return {
        id: cursor.rangeStart + cursor.offset
      };
    } else {
      return {
        id: cursor.rangeStart + cursor.offset
      };
    }
  }

  measureItems() {
    console.log(`[measureItems] Measuring ${this.items.length} items for column ${this.level}`);
    const itemElements = this.content.children;
    const heights = [];

    this.items.forEach((item, index) => {
      const element = itemElements[index];
      if (element) {
        const height = element.offsetHeight;
        item.height = height;
        heights.push(height); // Store for logging
      } else {
        console.warn(`measureItems: Mismatch at index ${index}`);
      }
    });
    
    // Log all heights at once
    console.log(`[measureItems] Column ${this.level} heights:`, heights);
  }

  render() {
    // Check if we need to rebuild DOM
    const existingItems = this.content.querySelectorAll('.item');

    if(existingItems.length !== this.items.length) {
      // Item count changed, rebuild
      this.rebuildDOM();
    } else {
      // Just update selections and transform
      existingItems.forEach((itemDiv, index) => {
        if(this.selectedIndices.includes(index)) {
          itemDiv.classList.add('selected');
        } else {
          itemDiv.classList.remove('selected');
        }
      });
    }

    this.content.style.transform = `translateY(${this.scrollOffset}px)`;
  }

  rebuildDOM() {
    this.content.innerHTML = '';

    this.items.forEach((item, index) => {
      const itemDiv = document.createElement('div');
      itemDiv.className = 'item';
      if(this.selectedIndices.includes(index)) {
        itemDiv.classList.add('selected');
      }
      itemDiv.dataset.index = index;
      itemDiv.innerHTML = this.tree.levels[this.level].render(item.data);
      this.content.appendChild(itemDiv);
    });
  }

  getSelectedBounds() {
    if(this.selectedIndices.length === 0) return null;

    // Calculate bounds for all selected items
    let minIndex = Math.min(...this.selectedIndices);
    let maxIndex = Math.max(...this.selectedIndices);

    let top = 0;
    for(let i = 0; i < minIndex; i++) {
      top += this.items[i].height;
    }

    let bottom = top;
    for(let i = minIndex; i <= maxIndex; i++) {
      bottom += this.items[i].height;
    }

    return {
      top: top + this.scrollOffset,
      bottom: bottom + this.scrollOffset,
      height: bottom - top
    };
  }

  getDraggedItemBounds() {
    if(this.draggedIndex < 0) return null;

    let top = 0;
    for(let i = 0; i < this.draggedIndex; i++) {
      top += this.items[i].height;
    }

    return {
      top: top + this.scrollOffset,
      bottom: top + this.items[this.draggedIndex].height + this.scrollOffset,
      height: this.items[this.draggedIndex].height
    };
  }

  scrollToProportional(draggedBounds, viewportHeight) {
    const myBounds = this.getSelectedBounds();
    if(!myBounds || !draggedBounds) return;

    // Calculate what proportion of the dragged item is visible
    const draggedTop = draggedBounds.top;
    const draggedBottom = draggedBounds.bottom;
    const draggedHeight = draggedBounds.height;

    let proportion = draggedTop / (viewportHeight - draggedHeight);
    proportion = Math.max(0, Math.min(proportion, 1))

    // Apply same proportion to this column's selection
    const myHeight = myBounds.height;
    const availableSpace = viewportHeight - myHeight;
    const targetTop = proportion * availableSpace;

    let currentTop = 0;
    const minIndex = Math.min(...this.selectedIndices);
    for(let i = 0; i < minIndex; i++) {
      currentTop += this.items[i].height;
    }

    this.scrollOffset = targetTop - currentTop;
    this.render();
  }
}

// Multiscroller class
class Multiscroller {
  constructor(container, tree) {
    this.container = container;
    this.tree = tree;
    this.columns = [];

    // Create columns for each level
    tree.levels.forEach((level, index) => {
      const column = new Column(container, tree, index);
      column.onSelect = (itemIndex) => this.onColumnSelect(index,
        itemIndex);
      column.onDrag = (itemIndex, delta) => this.onColumnDrag(index);
      this.columns.push(column);
    });
  }

  async init() {
    await this.columns[0].populate(null);
  }

  async populateAncestorColumn(ancestorLevel, selectedCursor, selectedLevel) {
    const ancestorColumn = this.columns[ancestorLevel];
    
    // Ascend from the current selection to get the ancestor
    let currentCursor = selectedCursor;
    let currentLevel = selectedLevel;
    
    // Ascend to the target level
    while (currentLevel > ancestorLevel) {
      const ascendResult = this.tree.ascend(currentCursor, currentLevel);
      if (!ascendResult) return;
      currentCursor = ascendResult.cursor;
      currentLevel--;
    }
    
    if (currentLevel === ancestorLevel) {
      // Clear and repopulate the ancestor column around this cursor
      await ancestorColumn.populate(currentCursor);
      
      // Find and select the item with this cursor
      const ancestorIndex = ancestorColumn.items.findIndex(item => 
        JSON.stringify(item.cursor) === JSON.stringify(currentCursor)
      );
      if (ancestorIndex >= 0) {
        ancestorColumn.setSelectedIndices([ancestorIndex]);
      }
    }
  }

  collectChildrenOfParents(parentCursors, parentLevel, childLevel) {
    let childItems = [];
    let allSelectedIndices = [];
    
    for (let parentCursor of parentCursors) {
      // Get the first child of this parent
      const firstDescendResult = this.tree.descend(parentCursor, parentLevel);
      if (!firstDescendResult) continue;
      
      // Add first child
      let startIndex = childItems.length;
      childItems.push({
        cursor: firstDescendResult.cursor,
        data: firstDescendResult.data
      });
      
      // Iterate forward with next(), checking if each item is still a child of this parent
      let currentCursor = firstDescendResult.cursor;
      while (true) {
        const nextResult = this.tree.next(currentCursor, childLevel);
        if (!nextResult) break;
        
        // Check if this item is a child of the current parent
        if (!this.tree.isChildOf(nextResult.cursor, childLevel, parentCursor, parentLevel)) {
          break; // We've passed this parent's children
        }
        
        childItems.push({
          cursor: nextResult.cursor,
          data: nextResult.data
        });
        currentCursor = nextResult.cursor;
      }
      
      // Mark all children of this parent as selected
      for (let i = startIndex; i < childItems.length; i++) {
        allSelectedIndices.push(i);
      }
    }
    
    return { childItems, allSelectedIndices };
  }

  fillViewportWithNeighbors(childItems, descendantLevel, descendantColumn) {
    const viewportHeight = descendantColumn.element.offsetHeight;
    let fillBatchSize = 50;
    
    // Add items before
    let beforeCursor = childItems[0].cursor;
    let beforeItems = [];
    let beforeHeight = 0;
    
    for (let i = 0; i < fillBatchSize && beforeHeight < viewportHeight; i++) {
      const prevResult = this.tree.prev(beforeCursor, descendantLevel, false);
      if (!prevResult) break;
      
      beforeItems.unshift({
        cursor: prevResult.cursor,
        data: prevResult.data
      });
      beforeCursor = prevResult.cursor;
      beforeHeight += 50; // Rough estimate
    }
    
    // Add items after
    let afterCursor = childItems[childItems.length - 1].cursor;
    let afterItems = [];
    let afterHeight = 0;
    
    for (let i = 0; i < fillBatchSize && afterHeight < viewportHeight; i++) {
      const nextResult = this.tree.next(afterCursor, descendantLevel, false);
      if (!nextResult) break;
      
      afterItems.push({
        cursor: nextResult.cursor,
        data: nextResult.data
      });
      afterCursor = nextResult.cursor;
      afterHeight += 50; // Rough estimate
    }
    
    return { beforeItems, afterItems };
  }
  
  async populateAndPositionDescendantColumn(descendantColumn, childItems, allSelectedIndices, descendantLevel) { // <-- Make async

    if (childItems.length === 0) {
      descendantColumn.items = [];
      descendantColumn.selectedIndices = [];
      descendantColumn.scrollOffset = 0;
      descendantColumn.rebuildDOM();
      return;
    }
    
    // Fill viewport with neighbors
    const { beforeItems, afterItems } = this.fillViewportWithNeighbors(
      childItems, descendantLevel, descendantColumn
    );
    
    // Combine: before + children + after
    const allItems = [...beforeItems, ...childItems, ...afterItems];
    
    // Adjust selected indices to account for items added before
    const offsetAdjustment = beforeItems.length;
    const adjustedSelectedIndices = allSelectedIndices.map(idx => idx + offsetAdjustment);
    
    // Set the items synchronously
    descendantColumn.items = allItems;
    descendantColumn.scrollOffset = 0;
    
    // 1. Rebuild the DOM
    descendantColumn.rebuildDOM();
    
    // 2. Wait for the browser to finish layout
    await new Promise(resolve => requestAnimationFrame(resolve));

    // 3. NOW measure the items
    descendantColumn.measureItems();
    
    // 4. Calculate scroll offset with correct heights
    let selectedTop = 0;
    for (let i = 0; i < adjustedSelectedIndices[0]; i++) {
      if (descendantColumn.items[i]) { // Add a safety check
        selectedTop += descendantColumn.items[i].height;
      }
    }
    
    descendantColumn.scrollOffset = -selectedTop;
    
    // 5. Select the children and apply the final transform
    descendantColumn.setSelectedIndices(adjustedSelectedIndices);
  }


  async onColumnSelect(columnIndex, itemIndex) {
    const column = this.columns[columnIndex];
    const selectedItem = column.items[itemIndex];
    const selectedCursor = selectedItem.cursor;

    // Handle ancestor columns (to the left)
    for (let ancestorLevel = columnIndex - 1; ancestorLevel >= 0; ancestorLevel--) {
      await this.populateAncestorColumn(ancestorLevel, selectedCursor, columnIndex);
    }

    // Handle descendant columns (to the right)
    for (let descendantLevel = columnIndex + 1; descendantLevel < this.columns.length; descendantLevel++) {
      const descendantColumn = this.columns[descendantLevel];
      
      // Get all selected cursors from the previous level
      const prevColumn = this.columns[descendantLevel - 1];
      const parentCursors = prevColumn.selectedIndices.map(idx => prevColumn.items[idx].cursor);
      
      if (parentCursors.length === 0) {
        // No parents selected, clear this column
        descendantColumn.items = [];
        descendantColumn.selectedIndices = [];
        descendantColumn.rebuildDOM();
        continue;
      }
      
      // Collect all children of all parents
      const { childItems, allSelectedIndices } = this.collectChildrenOfParents(
        parentCursors, descendantLevel - 1, descendantLevel
      );
      
      // Populate column with children and viewport fill
      await this.populateAndPositionDescendantColumn( // <-- Add await
        descendantColumn, childItems, allSelectedIndices, descendantLevel
      );
    }
    // Now that all columns are populated and selected, sync
    // their scroll positions based on the item just clicked.
    // This is "drag by zero" logic.
    const clickedBounds = column.getSelectedBounds();
    const viewportHeight = column.element.offsetHeight;

    if (clickedBounds) {
      this.columns.forEach((col, idx) => {
        // Sync all *other* columns that have selections
        if (idx !== columnIndex && col.selectedIndices.length > 0) {
          col.scrollToProportional(clickedBounds, viewportHeight);
        }
      });
    }
  }

  onColumnDrag(draggedColumnIndex) {
    const draggedColumn = this.columns[draggedColumnIndex];
    const bounds = draggedColumn.getDraggedItemBounds();
    const viewportHeight = draggedColumn.element.offsetHeight;

    // Sync all other columns with selections
    this.columns.forEach((column, index) => {
      if(index !== draggedColumnIndex && column.selectedIndices.length >
        0) {
        column.scrollToProportional(bounds, viewportHeight);
      }
    });
  }
}