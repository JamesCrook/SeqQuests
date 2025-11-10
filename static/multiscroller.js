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
  next(cursor, level) {
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
      if(offset >= 99) return null;
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
      return null; // Full records don't have next
    }
  }

  prev(cursor, level) {
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
      if(offset <= 0) return null;
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
      return null;
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

    // Check if we need to load more items
    //this.ensureItemsCoverViewport();

    this.render();

    // Notify multiscroller of drag
    if(this.onDrag) {
      this.onDrag(this.selectedIndices, delta);
    }
  }

  ensureItemsCoverViewport() {
    if(this.items.length === 0) return;

    const viewportHeight = this.element.offsetHeight;
    const BUFFER = 100; // Pixels of buffer
    const MAX_ITEMS_TO_ADD = 50; // Don't add too many at once

    // Calculate total height of all items
    let totalHeight = 0;
    this.items.forEach(item => totalHeight += item.height);

    // Check if we need items at the top (scrolled down, positive offset means content moved down)
    if(this.scrollOffset > BUFFER) {
      // Need more items at the beginning
      let firstCursor = this.items[0].cursor;
      let newItems = [];
      let addedHeight = 0;

      // Keep adding items until we have enough buffer
      for(let count = 0; count < MAX_ITEMS_TO_ADD; count++) {
        const result = this.tree.prev(firstCursor, this.level);
        if(!result) break;

        // Measure this item
        const tempDiv = document.createElement('div');
        tempDiv.style.position = 'absolute';
        tempDiv.style.visibility = 'hidden';
        tempDiv.style.width = this.element.offsetWidth + 'px';
        this.element.appendChild(tempDiv);
        tempDiv.innerHTML = '<div class="item">' + this.tree.levels[this
          .level].render(result.data) + '</div>';
        const height = tempDiv.firstChild.offsetHeight;
        this.element.removeChild(tempDiv);

        newItems.unshift({
          cursor: result.cursor,
          data: result.data,
          height: height
        });
        addedHeight += height;
        firstCursor = result.cursor;

        // Stop if we've added enough buffer
        if(addedHeight > this.scrollOffset + viewportHeight) break;
      }

      if(newItems.length > 0) {
        // Adjust scroll offset to account for new items
        this.scrollOffset -= addedHeight;

        // Adjust selected indices and dragged index
        this.selectedIndices = this.selectedIndices.map(idx => idx + newItems
          .length);
        if(this.draggedIndex >= 0) {
          this.draggedIndex += newItems.length;
        }

        this.items = [...newItems, ...this.items];
        this.rebuildDOM(); // Rebuild since we added items
      }
    }

    // Recalculate total height after potentially adding items at top
    totalHeight = 0;
    this.items.forEach(item => totalHeight += item.height);

    // Check if we need items at the bottom
    const bottomOfContent = this.scrollOffset + totalHeight;
    if(bottomOfContent < viewportHeight - BUFFER) {
      // Need more items at the end
      let lastCursor = this.items[this.items.length - 1].cursor;
      let itemsAdded = 0;

      // Keep adding until we fill the viewport with buffer
      for(let count = 0; count < MAX_ITEMS_TO_ADD; count++) {
        const result = this.tree.next(lastCursor, this.level);
        if(!result) break;

        // Measure this item
        const tempDiv = document.createElement('div');
        tempDiv.style.position = 'absolute';
        tempDiv.style.visibility = 'hidden';
        tempDiv.style.width = this.element.offsetWidth + 'px';
        this.element.appendChild(tempDiv);
        tempDiv.innerHTML = '<div class="item">' + this.tree.levels[this
          .level].render(result.data) + '</div>';
        const height = tempDiv.firstChild.offsetHeight;
        this.element.removeChild(tempDiv);

        this.items.push({
          cursor: result.cursor,
          data: result.data,
          height: height
        });
        totalHeight += height;
        lastCursor = result.cursor;
        itemsAdded++;

        // Stop if we've filled enough
        const newBottom = this.scrollOffset + totalHeight;
        if(newBottom > viewportHeight + viewportHeight) break; // Extra buffer
      }

      if(itemsAdded > 0) {
        this.rebuildDOM(); // Rebuild since we added items
      }
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

  populate(startCursor, direction = 'both') {
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

    this.measureItems();
    this.render();
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
    const tempDiv = document.createElement('div');
    tempDiv.style.position = 'absolute';
    tempDiv.style.visibility = 'hidden';
    tempDiv.style.width = this.element.offsetWidth + 'px';
    this.element.appendChild(tempDiv);

    this.items.forEach((item, index) => {
      tempDiv.innerHTML = '<div class="item">' + this.tree.levels[this
        .level].render(item.data) + '</div>';
      item.height = tempDiv.firstChild.offsetHeight;
    });

    this.element.removeChild(tempDiv);
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

    // Initialize first column
    this.columns[0].populate(null);
  }

  onColumnSelect(columnIndex, itemIndex) {
    const column = this.columns[columnIndex];
    const selectedItem = column.items[itemIndex];
    const selectedCursor = selectedItem.cursor;

    // Handle ancestor columns (to the left)
    for (let ancestorLevel = columnIndex - 1; ancestorLevel >= 0; ancestorLevel--) {
      const ancestorColumn = this.columns[ancestorLevel];
      
      // Ascend from the current selection to get the ancestor
      let currentCursor = selectedCursor;
      let currentLevel = columnIndex;
      
      // Ascend to the target level
      while (currentLevel > ancestorLevel) {
        const ascendResult = this.tree.ascend(currentCursor, currentLevel);
        if (!ascendResult) break;
        currentCursor = ascendResult.cursor;
        currentLevel--;
      }
      
      if (currentLevel === ancestorLevel) {
        // Clear and repopulate the ancestor column around this cursor
        ancestorColumn.populate(currentCursor);
        
        // Find and select the item with this cursor
        const ancestorIndex = ancestorColumn.items.findIndex(item => 
          JSON.stringify(item.cursor) === JSON.stringify(currentCursor)
        );
        if (ancestorIndex >= 0) {
          ancestorColumn.setSelectedIndices([ancestorIndex]);
        }
      }
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
      
      // Collect all children by iterating through all parent cursors
      let childItems = [];
      let allSelectedIndices = [];
      
      for (let parentCursor of parentCursors) {
        // Get the first child of this parent
        const firstDescendResult = this.tree.descend(parentCursor, descendantLevel - 1);
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
          const nextResult = this.tree.next(currentCursor, descendantLevel);
          if (!nextResult) break;
          
          // Check if this item is a child of the current parent
          if (!this.tree.isChildOf(nextResult.cursor, descendantLevel, parentCursor, descendantLevel - 1)) {
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
      
      if (childItems.length > 0) {
        // Now fill viewport with items before and after the children
        const viewportHeight = descendantColumn.element.offsetHeight;
        let fillBatchSize = 50; // Items to add at a time
        
        // Add items before
        let beforeCursor = childItems[0].cursor;
        let beforeItems = [];
        let beforeHeight = 0;
        
        for (let i = 0; i < fillBatchSize && beforeHeight < viewportHeight; i++) {
          const prevResult = this.tree.prev(beforeCursor, descendantLevel);
          if (!prevResult) {
            // Hit a boundary - need to go to previous parent
            if (descendantLevel === 2) {
              // Can't go further back at level 2, we're at a record boundary
              // Need to go back to previous ID and get its record
              const parentResult = this.tree.ascend(beforeCursor, descendantLevel);
              if (!parentResult) break;
              const prevParentResult = this.tree.prev(parentResult.cursor, descendantLevel - 1);
              if (!prevParentResult) break;
              const prevChildResult = this.tree.descend(prevParentResult.cursor, descendantLevel - 1);
              if (!prevChildResult) break;
              beforeItems.unshift({
                cursor: prevChildResult.cursor,
                data: prevChildResult.data
              });
              beforeCursor = prevChildResult.cursor;
            } else {
              // At level 1, need to go to previous range
              const parentResult = this.tree.ascend(beforeCursor, descendantLevel);
              if (!parentResult) break;
              const prevParentResult = this.tree.prev(parentResult.cursor, descendantLevel - 1);
              if (!prevParentResult) break;
              const prevChildResult = this.tree.descend(prevParentResult.cursor, descendantLevel - 1);
              if (!prevChildResult) break;
              // Now get the last child of this previous parent
              let lastChild = prevChildResult;
              while (true) {
                const nextInParent = this.tree.next(lastChild.cursor, descendantLevel);
                if (!nextInParent) break;
                lastChild = nextInParent;
              }
              beforeItems.unshift({
                cursor: lastChild.cursor,
                data: lastChild.data
              });
              beforeCursor = lastChild.cursor;
            }
          } else {
            beforeItems.unshift({
              cursor: prevResult.cursor,
              data: prevResult.data
            });
            beforeCursor = prevResult.cursor;
          }
          
          // Rough height estimate (will measure properly later)
          beforeHeight += 50;
        }
        
        // Add items after
        let afterCursor = childItems[childItems.length - 1].cursor;
        let afterItems = [];
        let afterHeight = 0;
        
        for (let i = 0; i < fillBatchSize && afterHeight < viewportHeight; i++) {
          const nextResult = this.tree.next(afterCursor, descendantLevel);
          if (!nextResult) {
            // Hit a boundary - need to go to next parent
            if (descendantLevel === 2) {
              // Can't go further at level 2, we're at a record boundary
              // Need to go to next ID and get its record
              const parentResult = this.tree.ascend(afterCursor, descendantLevel);
              if (!parentResult) break;
              const nextParentResult = this.tree.next(parentResult.cursor, descendantLevel - 1);
              if (!nextParentResult) break;
              const nextChildResult = this.tree.descend(nextParentResult.cursor, descendantLevel - 1);
              if (!nextChildResult) break;
              afterItems.push({
                cursor: nextChildResult.cursor,
                data: nextChildResult.data
              });
              afterCursor = nextChildResult.cursor;
            } else {
              // At level 1, need to go to next range
              const parentResult = this.tree.ascend(afterCursor, descendantLevel);
              if (!parentResult) break;
              const nextParentResult = this.tree.next(parentResult.cursor, descendantLevel - 1);
              if (!nextParentResult) break;
              const nextChildResult = this.tree.descend(nextParentResult.cursor, descendantLevel - 1);
              if (!nextChildResult) break;
              afterItems.push({
                cursor: nextChildResult.cursor,
                data: nextChildResult.data
              });
              afterCursor = nextChildResult.cursor;
            }
          } else {
            afterItems.push({
              cursor: nextResult.cursor,
              data: nextResult.data
            });
            afterCursor = nextResult.cursor;
          }
          
          // Rough height estimate
          afterHeight += 50;
        }
        
        // Combine: before + children + after
        const allItems = [...beforeItems, ...childItems, ...afterItems];
        
        // Adjust selected indices to account for items added before
        const offsetAdjustment = beforeItems.length;
        const adjustedSelectedIndices = allSelectedIndices.map(idx => idx + offsetAdjustment);
        
        // Set the items
        descendantColumn.items = allItems;
        descendantColumn.measureItems();
        
        // Calculate scroll offset to center the selected items
        let selectedTop = 0;
        for (let i = 0; i < adjustedSelectedIndices[0]; i++) {
          selectedTop += descendantColumn.items[i].height;
        }
        
        descendantColumn.scrollOffset = -selectedTop;
        descendantColumn.rebuildDOM();
        
        // Select the children (now at adjusted indices)
        descendantColumn.setSelectedIndices(adjustedSelectedIndices);
      } else {
        // No children found
        descendantColumn.items = [];
        descendantColumn.selectedIndices = [];
        descendantColumn.scrollOffset = 0;
        descendantColumn.rebuildDOM();
      }
    }
  }

  onColumnDrag(draggedColumnIndex) {
    const draggedColumn = this.columns[draggedColumnIndex];
    const bounds = draggedColumn.getDraggedItemBounds();
    const viewportHeight = draggedColumn.element.offsetHeight;

    // Ensure all columns have enough items to cover their viewports
    this.columns.forEach((column) => {
      if(column.items.length > 0) {
        column.ensureItemsCoverViewport();
      }
    });

    // Sync all other columns with selections
    this.columns.forEach((column, index) => {
      if(index !== draggedColumnIndex && column.selectedIndices.length >
        0) {
        column.scrollToProportional(bounds, viewportHeight);
      }
    });
  }
}