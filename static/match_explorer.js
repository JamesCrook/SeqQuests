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
async function fetchFindingsList() {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);
        
        const response = await fetch(`${API_BASE_URL}/api/findings`, {
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
async function fetchSequenceDetails(id1, id2) {
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
        // Silently fail and fall back to mock data
        return null;
    }
}

// Mock data based on the provided document
const findingsData = `249655-33536 s(299) Q1Q8Y4-Q8LEM4 Length: 95/122 [...skipped 1 similar names]
249655: Cell division topological specificity factor {ECO:0000255|HAMAP-Rule:MF_00262}; Psychrobacter cryohalolentis (strain ATCC BAA-1226 / DSM 17306 / VKM B-2378 / K5).
33536: Autophagy-related protein 8a; Arabidopsis thaliana (Mouse-ear cress).
80774-148481 s(299) Q9KM66-P48027 Length: 686/907
80774: CAI-1 autoinducer sensor kinase/phosphatase CqsS; Vibrio cholerae serotype O1 (strain ATCC 39315 / El Tor Inaba N16961).
148481: Sensor protein GacS; Pseudomonas syringae pv. syringae.
249652-243170 s(299) Q3ICG2-Q5PN73 Length: 88/320
249652: Cell division topological specificity factor {ECO:0000255|HAMAP-Rule:MF_00262}; Pseudoalteromonas translucida (strain TAC 125).
243170: o-succinylbenzoate synthase {ECO:0000255|HAMAP-Rule:MF_00470}; Salmonella paratyphi A (strain ATCC 9150 / SARB42).
135066-235941 s(299) P13386-Q96JQ5 Length: 243/239
135066: High affinity immunoglobulin epsilon receptor subunit beta; Rattus norvegicus (Rat).
235941: Membrane-spanning 4-domains subfamily A member 4A; Homo sapiens (Human).
14243-62325 s(299) O60022-P81702 Length: 152/134 [...skipped 4 similar names]
14243: Allergen Asp f 15; Aspergillus fumigatus (strain ATCC MYA-4609 / CBS 101355 / FGSC A1100 / Af293) (Neosartorya fumigata).
62325: Cerato-platanin {ECO:0000303|PubMed:10455173, ECO:0000303|PubMed:15063505, ECO:0000303|PubMed:33736287, ECO:0000312|EMBL:CAC84090.2}; Ceratocystis fimbriata f. sp. platani.
229673-224520 s(299) Q5PH64-Q2GA52 Length: 78/263 [...skipped 12 similar names]
229673: Major outer membrane lipoprotein Lpp 1 {ECO:0000255|HAMAP-Rule:MF_00843}; Salmonella paratyphi A (strain ATCC 9150 / SARB42).
224520: Leucyl/phenylalanyl-tRNA--protein transferase {ECO:0000255|HAMAP-Rule:MF_00688}; Novosphingobium aromaticivorans (strain ATCC 700278 / DSM 12444 / CCUG 56034 / CIP 105152 / NBRC 16084 / F199).
191425-164415 s(299) Q9XER9-Q9FPQ6 Length: 1392/555
191425: ENHANCER OF AG-4 protein 2; Arabidopsis thaliana (Mouse-ear cress).
164415: Vegetative cell wall protein gp1; Chlamydomonas reinhardtii (Chlamydomonas smithii).
111107-104529 s(299) P0DXU8-P40764 Length: 253/332 [...skipped 1 toxins and 8 similar names]
111107: Daunorubicin resistance ABC transporter permease protein DrrB3 {ECO:0000305}; Streptomyces coeruleorubidus.
104529: Homeobox protein DLX-2; Mus musculus (Mouse).
253920-122547 s(299) M0R6D8-P18488 Length: 403/497 [...skipped 6 similar names]
253920: Motor neuron and pancreas homeobox 1 {ECO:0000312|RGD:1588091}; Rattus norvegicus (Rat).
122547: Homeotic protein empty spiracles; Drosophila melanogaster (Fruit fly).
155588-48625 s(299) C3RT17-E7EKH2 Length: 70/71 [...skipped 1 similar names]
155588: Gaegurin-LK1 {ECO:0000303|PubMed:23054029}; Limnonectes kuhlii (Kuhl's Creek frog) (Rana kuhlii).
48625: Brevinin-1SN2 {ECO:0000303|PubMed:24055160}; Sylvirana spinulosa (Fine-spined frog) (Hylarana spinulosa).
155210-155218 s(299) Q6GKV1-A1Z3X3 Length: 324/323 [...skipped 1 uncharacterized]
155210: Protein GET4 {ECO:0000303|PubMed:28096354}; Arabidopsis thaliana (Mouse-ear cress).
155218: Golgi to ER traffic protein 4 homolog; Oryzias latipes (Japanese rice fish) (Japanese killifish).
194429-57527 s(299) Q9LSS5-Q8C9S4 Length: 564/917 [...skipped 1 similar names]
194429: Interactor of constitutive active ROPs 3; Arabidopsis thaliana (Mouse-ear cress).
57527: Coiled-coil domain-containing protein 186; Mus musculus (Mouse).
42840-32796 s(299) Q9JLV1-P37278 Length: 577/926 [...skipped 1 uncharacterized and 4 similar names]
42840: BAG family molecular chaperone regulator 3; Mus musculus (Mouse).
32796: Calcium-transporting ATPase; Synechococcus elongatus (strain ATCC 33912 / PCC 7942 / FACHB-805) (Anacystis nidulans R2).
278355-85204 s(298) Q8R4I7-Q9JLB4 Length: 533/3623 [...skipped 1 similar names]
278355: Neuropilin and tolloid-like protein 1; Mus musculus (Mouse).
85204: Cubilin; Mus musculus (Mouse).
55228-168022 s(298) B1NY81-P10496 Length: 312/465 [...skipped 1 similar names]
55228: Dehydrin CAS31 {ECO:0000305}; Medicago truncatula (Barrel medic) (Medicago tribuloides).
168022: Glycine-rich cell wall structural protein 1.8; Phaseolus vulgaris (Kidney bean) (French bean).`;

// Mock sequence data generator
function generateMockSequence(length) {
    const aminoAcids = 'ACDEFGHIKLMNPQRSTVWY';
    let sequence = '';
    for (let i = 0; i < length; i++) {
        sequence += aminoAcids[Math.floor(Math.random() * aminoAcids.length)];
    }
    return sequence;
}

function generateMockAlignment(seq1, seq2) {
    const maxLen = Math.max(seq1.length, seq2.length);
    let align1 = '';
    let align2 = '';
    let matches = '';
    
    for (let i = 0; i < maxLen; i++) {
        const aa1 = seq1[i] || '-';
        const aa2 = seq2[i] || '-';
        align1 += aa1;
        align2 += aa2;
        
        if (aa1 === aa2 && aa1 !== '-') {
            matches += '|';
        } else if (aa1 === '-' || aa2 === '-') {
            matches += ' ';
        } else {
            matches += ':';
        }
    }
    
    return { align1, align2, matches };
}

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
        if (line.match(/^\d+-\d+/)) {
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


        // Try to fetch findings from server (includes health check)
        const serverFindings = await fetchFindingsList();
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

        // Handle URL Params
        handleUrlParams();

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
    const headerMatch = finding.header.match(/(\d+)-(\d+).*Length: (\d+)\/(\d+)/);
    if (!headerMatch) {
        isLoadingSequence = false;
        return;
    }
    
    const [, id1, id2, len1, len2] = headerMatch;
    
    // Try to fetch from server first
    let serverData = await fetchSequenceDetails(id1, id2);
    
    let seq1, seq2, alignment, score;
    
    if (serverData) {
        // Use server data
        seq1 = serverData.sequence1;
        seq2 = serverData.sequence2;
        score = serverData.score;
        seq1Details = seq1;
        seq2Details = seq2;
        alignment = {
            align1: serverData.alignment1,
            align2: serverData.alignment2,
            matches: serverData.matches
        };
    } else {
        // Fall back to mock data
        seq1 = generateMockSequence(parseInt(len1));
        seq2 = generateMockSequence(parseInt(len2));
        score = -1;
        seq1Details = formatSequenceWithLineNumbers(seq1);
        seq2Details = formatSequenceWithLineNumbers(seq2);

        alignment = generateMockAlignment(seq1, seq2);
    }
    
    // Calculate stats
    const matches = (alignment.matches.match(/\|/g) || []).length;
    const similarity = score ;//((matches / Math.max(seq1.length, seq2.length)) * 100).toFixed(1);
    
    // Update badges
    if (detailBadge) detailBadge.textContent = `${similarity} score`;
    if (alignmentBadge) alignmentBadge.textContent = `${matches} matches`;
    
    // Build alignment view
    const alignLines = [];
    const lineLen = 70;

    // Get starting positions from server data (convert from 0-indexed to 1-indexed)
    let pos1 = (serverData && serverData.seq1_start || 0) + 1;
    let pos2 = (serverData && serverData.seq2_start || 0) + 1;

    for (let i = 0; i < alignment.align1.length; i += lineLen) {
        const chunk1 = alignment.align1.substr(i, lineLen);
        const chunkMatch = alignment.matches.substr(i, lineLen);
        const chunk2 = alignment.align2.substr(i, lineLen);
        
        // Format current positions
        const pos1Str = String(pos1).padStart(6, ' ');
        const pos2Str = String(pos2).padStart(6, ' ');
        
        alignLines.push(`${pos1Str}  ${chunk1}`);
        alignLines.push(`        ${chunkMatch}`);
        alignLines.push(`${pos2Str}  ${chunk2}\n`);
        
        // Update positions for next chunk by counting non-gap characters
        for (let j = 0; j < chunk1.length; j++) {
            if (chunk1[j] !== '-') pos1++;
        }
        for (let j = 0; j < chunk2.length; j++) {
            if (chunk2[j] !== '-') pos2++;
        }
    }

    if (alignmentViewer) {
        alignmentViewer.innerHTML = `<pre style="margin: 0; color: var(--text-primary);">${alignLines.join('\n')}</pre>`;
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
                    <div class="stat-value">${similarity}%</div>
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



// If loaded directly, init
if (document.querySelector('.explorer-layout')) {
    window.addEventListener('DOMContentLoaded', async () => {
        await window.initializeApp();
        if (typeof initMultiscroller === 'function') {
            initMultiscroller();
            // Sync UI state in case of re-render
            if (typeof updateMultiscrollUI === 'function') {
                updateMultiscrollUI();
            }
        }
    });
}

/* Multiscroll Support */
let isMultiscrollerEnabled = false;

function toggleMultiscroller() {
    isMultiscrollerEnabled = !isMultiscrollerEnabled;
    const btn = document.getElementById('multiscrollBtn');
    if (btn) {
        btn.textContent = `Multiscroll: ${isMultiscrollerEnabled ? 'ON' : 'OFF'}`;
        btn.classList.toggle('active', isMultiscrollerEnabled);
    }
}

// Drag State
let dragData = {
    isDragging: false,
    startY: 0,
    startScrollLeft: 0,
    startScrollRight: 0,
    draggedPanelId: null
};

// Initialize Drag Listeners
function initMultiscroller() {
    const leftPanel = document.getElementById('findingsList');
    const rightPanel = document.getElementById('pairViewer');

    if (!leftPanel || !rightPanel) return;

    // Helper to setup listeners
    const setupDrag = (panel) => {
        panel.addEventListener('mousedown', (e) => startDrag(e, panel.id));
        panel.classList.add('draggable'); // Ensure cursor style is ready
    };

    setupDrag(leftPanel);
    setupDrag(rightPanel);

    // Global listeners for drag operation
    window.addEventListener('mousemove', handleDrag);
    window.addEventListener('mouseup', endDrag);
}

function startDrag(e, panelId) {
    if (!isMultiscrollerEnabled) return;

    //const leftPanel = document.getElementById('LeftPanel');
    const leftPanel = document.getElementById('findingsList');
    const rightPanel = document.getElementById('pairViewer');

    dragData.isDragging = true;
    dragData.startY = e.clientY;
    dragData.startScrollLeft = leftPanel.scrollTop;
    dragData.startScrollRight = rightPanel.scrollTop;
    dragData.draggedPanelId = panelId;

    document.body.classList.add('dragging'); // Global cursor style
    leftPanel.classList.add('active-drag');
    rightPanel.classList.add('active-drag');
}

function endDrag() {
    if (!dragData.isDragging) return;

    dragData.isDragging = false;
    document.body.classList.remove('dragging');
    const leftPanel = document.getElementById('findingsList');
    const rightPanel = document.getElementById('pairViewer');
    if (leftPanel) leftPanel.classList.remove('active-drag');
    if (rightPanel) rightPanel.classList.remove('active-drag');
}

function handleDrag(e) {
    if (!dragData.isDragging || !isMultiscrollerEnabled) return;

    e.preventDefault();

    const deltaY = e.clientY - dragData.startY;
    const leftPanel = document.getElementById('findingsList');
    const rightPanel = document.getElementById('pairViewer');

    // 1. Update the dragged panel normally (drag down -> scroll up = content moves down)
    // Actually, "drag to scroll" usually means:
    // Drag Mouse Down -> Content Moves Down -> Scroll Top Decreases.
    // So scrollTop = startScroll - deltaY.

    if (dragData.draggedPanelId === 'findingsList') {
        leftPanel.scrollTop = dragData.startScrollLeft - deltaY;
        syncRightPanel(leftPanel, rightPanel);
    } else {
        rightPanel.scrollTop = dragData.startScrollRight - deltaY;
        syncLeftPanel(leftPanel, rightPanel);
    }
}

function syncRightPanel(leftPanel, rightPanel) {
    // Top of selected item @ Top of Left View -> Right Panel @ Top (0)
    // Bottom of selected item @ Bottom of Left View -> Right Panel @ Bottom (Max)

    // Check if we have a selection
    if (selectedEntryIndex === null) return;
    const entry = document.querySelector(`.finding-entry[data-index="${selectedEntryIndex}"]`);
    if (!entry) return;

    const itemTop = entry.offsetTop - leftPanel.offsetTop; // Relative to leftPanel

    const H_left = leftPanel.clientHeight;
    const h_item = entry.offsetHeight;

    // y is the position of the top of the item relative to the top of the viewport
    const y = itemTop - leftPanel.scrollTop;

    // T_right = y * (MaxScroll / (H_left - h_item))

    const S_right = rightPanel.scrollHeight;
    const H_right = rightPanel.clientHeight;
    const maxScrollRight = S_right - H_right;

    const denominator = H_left - h_item;
    if (denominator === 0) return; // Divide by zero protection

    const targetScroll = y * (maxScrollRight / denominator);

    // Just set it and let the browser clamp scrollTop.
    // "ganged scrolling can stop once beyond these limits".

    rightPanel.scrollTop = targetScroll;
}

function syncLeftPanel(leftPanel, rightPanel) {
    // Bidirectional Sync
    // We reverse the formula:
    // T_right = y * factor
    // y = T_right / factor
    // itemTop - T_left = T_right / factor
    // T_left = itemTop - (T_right / factor)

    if (selectedEntryIndex === null) return;
    const entry = document.querySelector(`.finding-entry[data-index="${selectedEntryIndex}"]`);
    if (!entry) return;

    const H_left = leftPanel.clientHeight;
    const h_item = entry.offsetHeight;
    const S_right = rightPanel.scrollHeight;
    const H_right = rightPanel.clientHeight;
    const maxScrollRight = S_right - H_right;

    const denominator = H_left - h_item;
    if (denominator === 0 || maxScrollRight === 0) return;

    const factor = maxScrollRight / denominator;

    // Current Right Scroll
    const T_right = rightPanel.scrollTop ;

    // Calculated y
    const y = T_right / factor;

    // Calculated T_left
    const itemTop = entry.offsetTop - leftPanel.offsetTop;
    const targetScrollLeft = itemTop - y;

    leftPanel.scrollTop = targetScrollLeft;
}
