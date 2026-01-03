//Multiscroller Refactor Blueprint1. The Proportional Gold StandardThis static method is the "Universal Translator" between different columns. It calculates a ratio (0 to 1) of where an item sits in its viewport "travel zone" and maps it to the target's scroll range.


// 1. Define the Navigator for Match Explorer
// Level 0: Findings List [index]
// Level 1: Details View [index, 0]
class FindingsNavigator {
    constructor(data) {
        this.data = data;
    }
    
    // Maps a finding selection to its detail view equivalent
    translateCursor(cursor, targetLevel) {
        if (targetLevel === 0) return [cursor[0]];
        if (targetLevel === 1) return [cursor[0], 0];
        return cursor;
    }
}

class ScrollMath {
    /* @param {number} itemTop Current visual Y of the source item
     * @param {number} itemHeight Height of the source item
     * @param {number} viewportHeight Height of the visible box
     * @param {number} targetItemHeight Height of the item in the destination panel
     */
    static calculateTargetVisualTop(itemTop, itemHeight, viewportHeight, targetItemHeight) {
        const sourceTravel = viewportHeight - itemHeight;
        const targetTravel = viewportHeight - targetItemHeight;

        //console.log( `${itemTop}/${itemHeight} ${viewportHeight}/${targetItemHeight}`)

        // Ratio: 0.0 (top of viewport) to 1.0 (bottom of viewport)
        const ratio = Math.max(0, Math.min(itemTop / sourceTravel, 1));
        //console.log( `ratio:${ratio} Maxscroll:${targetTravel}`)

        // Map that ratio to the target's travel zone
        return ratio * targetTravel;
    }    
}

class Multiscroller {
    constructor(navigator) {
        this.nav = navigator;
        this.targets = [];
        this.activeCursor = [0];
    }

    attach(element, level) {
        const target = new AttachedPanel(element, level, this);
        this.targets.push(target);
        return target;
    }

    // Single point of entry for state changes
    setActiveCursor(cursor, sourceIndex) {
        this.activeCursor = cursor;
        // Optionally update UI selection across all panels here
    }

    broadcastSync(sourceIndex) {
        const source = this.targets[sourceIndex];
        const bounds = source.getBounds(this.activeCursor);
        if (!bounds) return;

        this.targets.forEach((target, i) => {
            if (i !== sourceIndex) target.applySync(bounds);
        });
    }
}

class SyncTarget {
    constructor(el, level, orch) {
        this.el = el;
        this.level = level;
        this.orch = orch;
        this.isEnabled = false;
        this.isDragging = false;
        
        this._boundMouseMove = (e) => this.onMouseMove(e);
        this._boundMouseUp = (e) => this.onMouseUp(e);
        this.setupEventListeners();
    }

    setEnabled(val) { this.isEnabled = val; }

    setupEventListeners() {
        this.el.addEventListener('mousedown', (e) => this.onMouseDown(e));
        this.el.addEventListener('mouseleave', (e) => this.onMouseUp(e));
    }

    onMouseDown(e) {
        if (!this.isEnabled) return;
        
        const clickedItem = e.target.closest('[data-index]');
        if (clickedItem) {
            const index = parseInt(clickedItem.dataset.index);
            const newCursor = this.getCursorFromIndex(index);
            this.orch.setActiveCursor(newCursor, this.level);
        }

        this.isDragging = true;
        this.dragStartY = e.clientY;
        this.dragStartPos = this.getInternalScrollPos();
        
        window.addEventListener('mousemove', this._boundMouseMove);
        window.addEventListener('mouseup', this._boundMouseUp);
        e.preventDefault();
    }

    onMouseMove(e) {
        if (!this.isDragging) return;
        const delta = e.clientY - this.dragStartY;
        this.setInternalScrollPos(this.dragStartPos - delta);
        this.orch.broadcastSync(this.level);
    }

    onMouseUp() {
        if (!this.isDragging) return;
        this.isDragging = false;
        window.removeEventListener('mousemove', this._boundMouseMove);
        window.removeEventListener('mouseup', this._boundMouseUp);
    }

    applySync(refBounds) {
        // 1. Identify the 'Focal Item' for this panel
        const translated = this.orch.nav.translateCursor(this.orch.activeCursor, this.level);
        const localIndex = translated[translated.length - 1];
        const item = this.el.querySelector(`[data-index="${localIndex}"]`) || this.el.firstElementChild;

        if (!item) return;

        // 2. Calculate the "Target Visual Top"
        // This is the pixel position (0 to Travel) where the item should sit in the viewport
        const targetVisualTop = ScrollMath.calculateTargetVisualTop(
            refBounds.top, refBounds.height,
            this.el.clientHeight, item.offsetHeight
        );

        // 3. Perform the Scroll
        // To put the item at 'targetVisualTop', we scroll to: (Item's Absolute Position) - (Desired Visual Position)
        const absoluteItemTop = item.offsetTop; 
        this.setInternalScrollPos( absoluteItemTop - targetVisualTop - this.el.offsetTop);
    }

    // --- Implementation Details ---
    getInternalScrollPos() { throw "Not Implemented"; }
    setInternalScrollPos(val) { throw "Not Implemented"; }
    getBounds(cursor) { throw "Not Implemented"; }
    getCursorFromIndex(index) { throw "Not Implemented"; }
}

class AttachedPanel extends SyncTarget {
    getInternalScrollPos() { return this.el.scrollTop; }
    setInternalScrollPos(val) { this.el.scrollTop = val }

    getCursorFromIndex(index) {
        return [index];
    }

    getBounds(cursor) {
        const translated = this.orch.nav.translateCursor(cursor, this.level);
        const localIndex = translated[translated.length - 1];
        // the 'first child' alternative is for a style where we place a containing 'holder' inside
        // the scroller, rather than rely on data-index existing. 
        const item = this.el.querySelector(`[data-index="${localIndex}"]`) || this.el.firstElementChild;
        
        if (!item) {
            console.log("Item not found")
            return null;
        }
        const itemRect = item.getBoundingClientRect();
        const containerRect = this.el.getBoundingClientRect();
        return { top: itemRect.top - containerRect.top, height: itemRect.height };
    }
}

class ManagedColumn extends SyncTarget {
    getInternalScrollPos() { return -this.scrollOffset; }
    setInternalScrollPos(val) { this.scrollOffset = -val; this.render(); }

    getCursorFromIndex(index) { return this.items[index]?.cursor || [0]; }

    getBounds(cursor) {
        const translated = this.orch.nav.translateCursor(cursor, this.level);
        const item = this.items.find(it => JSON.stringify(it.cursor) === JSON.stringify(translated));
        if (!item) return null;

        const itemRect = item.element.getBoundingClientRect();
        const containerRect = this.el.getBoundingClientRect();
        return { top: itemRect.top - containerRect.top, height: itemRect.height };
    }
}


// API Configuration
// const API_BASE_URL = window.location.origin; // Defined in HTML
// const API_TIMEOUT = 5300; // Defined in HTML

function setConnectionStatus(connected) {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    if (!statusDot || !statusText) return;

    if (connected) {
        statusDot.classList.add('connected');
        statusDot.classList.remove('disconnected');
        statusText.textContent = 'Server Connected';
    } else {
        statusDot.classList.remove('connected');
        statusDot.classList.add('disconnected');
        statusText.textContent = 'Using Mock Data';
    }
}

// Fetch findings list from server with timeout
async function fetchFindingsList( list ='distilled') {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);
  
// The commented out version fetches the list via API.
//        const response = await fetch(`${API_BASE_URL}/api/findings`, {
//            signal: controller.signal
//        });
        
        const response = await fetch(`../findings/sw_finds_${list}.txt`, {
            signal: controller.signal
        });

        clearTimeout(timeoutId);
        
        if (response.ok) {
            return await response.text();
        }
        return null;
    } catch (error) {
        // Silently fail and fall back to mock data
        return null;
    }
}

// Fetch sequence details from server with timeout
async function fetchSequenceDetailsFromLabServer(id1, id2) {
    // Only fetch from server if we're using real findings data
    if (!usingRealFindings) {
        return null;
    }

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);
        
        const response = await fetch(`${API_BASE_URL}/api/comparison/${id1}/${id2}`, {
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
            return await response.json();
        }
        return null;
    } catch (error) {
        // Silently fail and fall back to mock/no data
        return null;
    }
}

// Fetch sequence details from uniprot
async function fetchSequenceDetailsFromUniprot(id1, id2) {
    // Only fetch from server if we're using real findings data
    if (!usingRealFindings) {
        return null;
    }

    let serverData = {};
    serverData.sequence1 ="ID This is Placeholder data";
    serverData.sequence2 ="ID This is also Placeholder data";
    serverData.score = 101;
    serverData.seq1_start = 12;
    serverData.seq2_start = 15;
    serverData.alignment1 = "AAAAAAAAAAAAAAA"
    serverData.alignment2 = "BBBBBBBBBBBBBBB"
    serverData.matches    = "....|||........"
    return serverData;


    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);
        
        const response = await fetch(`${API_BASE_URL}/api/comparison/${id1}/${id2}`, {
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
            return await response.json();
        }
        return null;
    } catch (error) {
        // Silently fail and fall back to mock/no data
        return null;
    }
}

const findingsData = '';

function formatSequenceWithLineNumbers(sequence, lineLength = 70) {
    let formatted = '';
    for (let i = 0; i < sequence.length; i += lineLength) {
        const lineNum = String(i + 1).padStart(6, ' ');
        const chunk = sequence.substr(i, lineLength);
        formatted += `${lineNum}  ${chunk}\n`;
    }
    return formatted;
}

// Parse findings data
function parseFindings(data) {
    const lines = data.trim().split('\n');
    const findings = [];
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        if (line.match(/^[A-Z0-9]+-[A-Z0-9]+/)) {
            const header = line;
            const details = [];
            
            // Collect detail lines
            while (i + 1 < lines.length && lines[i + 1].startsWith(' ')) {
                details.push(lines[i + 1]);
                i++;
            }
            
            findings.push({ header, details });
        }
    }
    
    return findings;
}


let statusDot = null;
let statusText = null;
let findings = null;
let isInitializing = false;
let parsedFindings = [];
let selectedEntryIndex = null;



// Initialize the application
// Made global so it can be called from lcars.js
window.initializeApp = async function() {
    // Check if required elements exist
    if (!document.getElementById('findingsList')) {
        // We might be loading just one part, or not loaded yet.
    }

    // Prevent multiple simultaneous initializations
    if (isInitializing) {
        return;
    }
    isInitializing = true;

    try{
        // Connection status management
        statusDot = document.getElementById('statusDot');
        statusText = document.getElementById('statusText');

        findings = parseFindings(findingsData);

        newSource();

        // Handle URL Params
        handleUrlParams();

        // Initialize the new orchestrator instead of the old manual listeners
        await initOrchestratedMultiscroller();
        
        // Sync UI state if needed
        if (typeof updateMultiscrollUI === 'function') {
            updateMultiscrollUI();
        }        

    } catch (error) {
        console.error('Error during app initialization:', error);
        // Optionally set connection status to disconnected on error
        if (typeof setConnectionStatus === 'function') {
            setConnectionStatus(false);
        }
    } finally {
        isInitializing = false;
    }    
};

function handleUrlParams() {
    const urlParams = new URLSearchParams(window.location.search);
    const hitId = urlParams.get('hit');

    if (hitId && parsedFindings.length > 0) {
        // Find index. header contains the ID like "249655-33536 s(299)..."
        const index = parsedFindings.findIndex(f => f.header.startsWith(hitId + ' '));
        if (index !== -1) {
            selectEntry(index);
            // Scroll findings list
            const entryDiv = document.querySelector(`.finding-entry[data-index="${index}"]`);
            if (entryDiv) {
                entryDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    }
}

function updateUrl(header) {
    const match = header.match(/^(\d+-\d+)/);
    if (match) {
        const id = match[1];
        const newUrl = `${window.location.pathname}?hit=${id}`;
        // Update URL without reloading
        window.history.pushState({ path: newUrl }, '', newUrl);
    }
}

// Populate findings list
function populateFindingsList(findingsArray) {
    const findingsList = document.getElementById('findingsList');
    if (!findingsList) return;

    findingsList.innerHTML = '';
    
    findingsArray.forEach((finding, index) => {
        const entryDiv = document.createElement('div');
        entryDiv.className = 'finding-entry';
        entryDiv.dataset.index = index;
        
        const headerDiv = document.createElement('div');
        headerDiv.className = 'finding-header';
        headerDiv.textContent = finding.header;
        
        entryDiv.appendChild(headerDiv);
        
        finding.details.forEach(detail => {
            const detailDiv = document.createElement('div');
            detailDiv.className = 'finding-detail';
            detailDiv.textContent = detail;
            entryDiv.appendChild(detailDiv);
        });
        
        // Click event
        entryDiv.addEventListener('click', () => {
             updateUrl(finding.header);
             selectEntry(index);
        });
        
        findingsList.appendChild(entryDiv);
    });
}

async function selectEntry(index) {
    // Ignore if loading or same entry
    if (isLoadingSequence || selectedEntryIndex === index) {
        return;
    }

    const finding = parsedFindings[index];
    if (!finding) return;

    // Update UI selection
    document.querySelectorAll('.finding-entry').forEach(e => e.classList.remove('active'));
    const entryDiv = document.querySelector(`.finding-entry[data-index="${index}"]`);
    if (entryDiv) {
        entryDiv.classList.add('active');
    }

    selectedEntryIndex = index;
    await loadSequenceDetails(finding, index);
    if (orchestrator) {
        orchestrator.activeCursor = [index];
        // Trigger an initial sync once the details are loaded
        orchestrator.broadcastSync(0, orchestrator.targets[0].getBounds([index]));
    }
 }

async function loadSequenceDetails(finding, index) {
    // Set loading flag
    isLoadingSequence = true;
    
    const detailViewer = document.getElementById('detailViewer');
    const alignmentViewer = document.getElementById('alignmentViewer');
    const detailBadge = document.getElementById('detailBadge');
    const alignmentBadge = document.getElementById('alignmentBadge');
    
    // Check if viewers exist
    if (detailViewer) {
         detailViewer.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; gap: 12px;"><div class="loading"></div><span>Loading sequence data...</span></div>';
    }
    if (alignmentViewer) {
         alignmentViewer.innerHTML = '<div style="display: flex; align-items: center; justify-content: center; height: 100%; gap: 12px;"><div class="loading"></div><span>Loading alignment...</span></div>';
    }
    
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 200));
    
    // Check if still selecting the same entry (handle race condition)
    if (selectedEntryIndex !== index) {
        isLoadingSequence = false;
        return;
    }
    
    // Extract IDs and lengths from header
    const headerMatch = finding.header.match(/([A-Z0-9]+)-([A-Z0-9]+).*Length: (\d+)\/(\d+)/);
    if (!headerMatch) {
        isLoadingSequence = false;
        return;
    }
    
    const [, id1, id2, len1, len2] = headerMatch;
    
    // Try to fetch from server
    let serverData = await fetchSequenceDetailsFromUniprot(id1, id2);
    
    if( !serverData){
        lastLoadedEntry = index;
        isLoadingSequence = false;
        Lcars.loadPartial('RightPanel', './panels/detail_view.html')
        return;
    }

    let seq1Details, seq2Details, alignment, score;
    
    // Use server data
    seq1Details = serverData.sequence1;
    seq2Details = serverData.sequence2;
    score = serverData.score;
    alignment = {
        seq1_start: serverData.seq1_start,             
        seq2_start: serverData.seq2_start,             
        align1: serverData.alignment1,
        align2: serverData.alignment2,
        matches: serverData.matches
    };
    // Calculate stats
    const matches = (alignment.matches.match(/\|/g) || []).length;
    const identity = ((matches / alignment.align1.length) * 100).toFixed(1);
    
    // Update badges
    if (detailBadge) detailBadge.textContent = `${score} score`;
    if (alignmentBadge) alignmentBadge.textContent = `${matches} matches`;
    const alignLines = formatAlignment( alignment);

    if (alignmentViewer) {
        alignmentViewer.innerHTML = `${alignLines.join('\n')}`;
    }
    
    // Build detail view
    if (detailViewer) {
        detailViewer.innerHTML = `
            <div class="stats-bar">
                <div class="stat-item">
                    <div class="stat-label">Match Score</div>
                    <div class="stat-value">${finding.header.match(/s\((\d+)\)/)[1]}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Identity</div>
                    <div class="stat-value">${identity}%</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Length 1</div>
                    <div class="stat-value">${len1}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Length 2</div>
                    <div class="stat-value">${len2}</div>
                </div>
            </div>

            <div class="sequence-section">
                <div class="sequence-label">Sequence 1 (ID: ${id1})</div>
                <div class="sequence-text" id="details1">${seq1Details}</div>
            </div>

            <div class="sequence-section">
                <div class="sequence-label">Sequence 2 (ID: ${id2})</div>
                <div class="sequence-text" id="details2">${seq2Details}</div>
            </div>
        `;
    }
    
    // Mark this entry as loaded and clear loading flag
    lastLoadedEntry = index;
    isLoadingSequence = false;

    // Scroll details panel to top
    const rightPanel = document.getElementById('RightPanel');
    if (rightPanel) {
        rightPanel.scrollTop = 0;
    }
}

function updateStatus( status, result ){
    if( statusDiv )
        statusDiv.textContent = status;
    if( reultArea )
        resultArea.value = result;
}

async function getAccessionAsText( accession ) {
    const useInternal = false;
    let url;

    if (useInternal) {
        url = `/api/uniprot/${accession}`;
    } else {
        url = `https://rest.uniprot.org/uniprotkb/${accession}.json`;
    }

    updateStatus( "Loading...",
        `Fetching from ${useInternal ? 'Lab Server' : 'Swiss-Prot'}...`);

    try {
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        updateStatus( "Success.", JSON.stringify(data, null, 2));
    } catch (error) {
        console.error('Fetch error:', error);
        updateStatus( "Error occurred.", `Error fetching data:\n${error.message}`);
    }
};

function getMatchText( index ){
    if (index === null || index < 0 || index >= parsedFindings.length) return '';
    item = parsedFindings[index];
    return `${item.header}\n${item.details[0]}\n${item.details[1]}\n\n`;
}

// Copy alignment to clipboard
function copyAlignment() {
    const alignmentViewer = document.getElementById('alignmentViewer');
    const copyBtn = document.getElementById('copyAlignmentBtn');
    if (!alignmentViewer || !copyBtn) return;
    
    // Get the text content from the pre element
    const preElement = alignmentViewer.querySelector('pre');
    
    if (!preElement || preElement.textContent.includes('No alignment selected') || preElement.textContent.includes('Loading')) {
        return;
    }
    
    let alignmentText = getMatchText(lastLoadedEntry) + preElement.textContent;
    
    // Copy to clipboard
    navigator.clipboard.writeText(alignmentText).then(() => {
        // Show success feedback
        const originalText = copyBtn.textContent;
        copyBtn.textContent = 'Copied!';
        copyBtn.classList.add('copied');
        
        // Reset button after 2 seconds
        setTimeout(() => {
            copyBtn.textContent = originalText;
            copyBtn.classList.remove('copied');
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy alignment:', err);
    });
}

// Copy details to clipboard
function copyDetail() {
    const detailViewer = document.getElementById('detailViewer');
    const copyBtn = document.getElementById('copyDetailBtn');
    if (!detailViewer || !copyBtn) return;
    
    // Get the text content from the pre element
    const detail1Element = document.getElementById('details1');
    const detail2Element = document.getElementById('details2');
    
    if (!detail1Element || !detail2Element) {
        return;
    }
    
    let detailText = `Is the similarity between the following two proteins already known and is it indicated in these two sequence files annotations?\n` + detail1Element.textContent + '\n'+ detail2Element.textContent;
    
    // Copy to clipboard
    navigator.clipboard.writeText(detailText).then(() => {
        // Show success feedback
        const originalText = copyBtn.textContent;
        copyBtn.textContent = 'Copied!';
        copyBtn.classList.add('copied');
        
        // Reset button after 2 seconds
        setTimeout(() => {
            copyBtn.textContent = originalText;
            copyBtn.classList.remove('copied');
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy detail text:', err);
    });
}

async function newSource( source ){
    //alert( elt.value )
    // Try to fetch findings from server (includes health check)
    const serverFindings = await fetchFindingsList( source );
    const bFound = serverFindings ? true:false;

    isServerConnected = bFound;
    usingRealFindings = bFound;
    setConnectionStatus(bFound);
    
    const dataToUse = serverFindings || findingsData;
    parsedFindings = parseFindings(dataToUse);

    // Update entry count
    const entriesCount = document.getElementById('entriesCount');
    if (entriesCount) {
        entriesCount.textContent = `${parsedFindings.length} entries`;
    }

    // Populate findings list
    populateFindingsList(parsedFindings);
}


let orchestrator = null;
let isMultiscrollerEnabled = false;

// 2. Updated toggle function
function toggleMultiscroller() {
    isMultiscrollerEnabled = !isMultiscrollerEnabled;
    const btn = document.getElementById('multiscrollBtn');
    if (btn) {
        btn.textContent = `Multiscroll: ${isMultiscrollerEnabled ? 'ON' : 'OFF'}`;
        btn.classList.toggle('active', isMultiscrollerEnabled);
    }
    // Update the targets to respect the global toggle
    if (orchestrator) {
        orchestrator.targets.forEach(t => t.setEnabled(isMultiscrollerEnabled));
    }
}

// 3. New Initialization Logic
async function initOrchestratedMultiscroller() {
    const findingsListEl = document.getElementById('findingsList');
    const pairViewerEl = document.getElementById('pairViewer');

    if (!findingsListEl || !pairViewerEl) return;

    // Create the orchestrator with our findings data
    orchestrator = new Multiscroller(new FindingsNavigator(parsedFindings));

    // Retrofit the existing DOM elements
    // Level 0: The Findings List
    const listPanel = orchestrator.attach(findingsListEl, 0);
    
    // Level 1: The Detail Viewer
    const detailPanel = orchestrator.attach(pairViewerEl, 1);

    // Initial state
    listPanel.setEnabled(isMultiscrollerEnabled);
    detailPanel.setEnabled(isMultiscrollerEnabled);
}

// 4. Entry Point Replacement
if (document.querySelector('.explorer-layout')) {
    window.addEventListener('DOMContentLoaded', async () => {
        await window.initializeApp(); // Load data first
    });
}