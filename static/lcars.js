// Do not remove this comment
// LCARs is designed so that it can function as a static website, with enhanced
// functionality when a server endpoint is available.
// For purely UI testing and development, this is frequently sufficient, and is 
// simpler than starting the server.
class LcarsUI {
    constructor() {
        this.doCommand = this.doCommand.bind(this);
        this.panelCounter = 0;
    }

    doCommand(event) {
        var elt = event.currentTarget || event.target;
        let action = elt.dataset.group
        if (action == 'Help')
            this.doHelp();
        else if (action == 'Alignment')
            this.doAlignment();
        else if (action == 'Search Results')
            this.doSearchResults();
        else if (action == 'Job Queue')
            this.doJobQueue();
        else
            alert(`No handler for ${action}`);
    }

    setPanel(panel, text) {
        let div = document.getElementById(panel);
        if (!div) {
            console.warn(`Panel ${panel} not found.`);
            return;
        }
        div.innerHTML = this.asHtml(text);

        // Execute any scripts in the loaded content
        this.executeScripts(div);
    }

    executeScripts(container) {
        const scripts = container.getElementsByTagName('script');
        for (let i = 0; i < scripts.length; i++) {
            const script = scripts[i];
            const newScript = document.createElement('script');
            if (script.src) {
                newScript.src = script.src;
            } else {
                newScript.textContent = script.textContent + 
                `\n//# sourceURL=panel-${this.panelCounter}.js`;
                this.panelCounter++;
            }
            document.body.appendChild(newScript); // Execute by appending to body
            // document.body.removeChild(newScript); // Optional cleanup
        }
    }

    setMainPanel(text) {
        this.setPanel('MainPanel', text)
    }

    setSubPanel(text) {
        this.setPanel('SubPanel', text)
    }

    async loadPartial(panelId, url, callback) {
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`Failed to load ${url}`);
            const html = await response.text();
            this.setPanel(panelId, html);
            
            // Add sourceURL based on the actual URL loaded
            const container = document.getElementById(panelId);
            const scripts = container.getElementsByTagName('script');
            for (let i = 0; i < scripts.length; i++) {
                const script = scripts[i];
                const newScript = document.createElement('script');
                if (script.src) {
                    newScript.src = script.src;
                } else {
                    newScript.textContent = script.textContent + 
                        `\n//# sourceURL=${url}-script-${i}.js`;
                }
                document.body.appendChild(newScript);
            }
            
            if (callback) callback();
        } catch (e) {
            console.error(e);
            this.setPanel(panelId, `Error loading ${url}`);
        }
    }

    async doHelp() {
        this.setSubPanel("Loading topics...");
        // TODO: Server should be updated so that it detects the request for doclist,
        // and updates doclist if it isn't up to date.
        try {
            const response = await fetch(`./docs/doclist.js`);
            const docs = await response.json();
            /*
            const response = await fetch('/api/docs');
            if (!response.ok) throw new Error('Network response was not ok');
            const docs = await response.json();
            */
            let html = '<div style="display:flex; flex-direction:column; gap:6px;">';
            docs.forEach(doc => {
                html += `<div class="block tan" style="cursor:pointer; padding: 10px; border-radius: 20px; text-align: center; color: black; font-weight: bold;" onclick="Lcars.showDoc('${doc.filename}')">${doc.name}</div>`;
            });
            html += '</div>';

            this.setSubPanel(html);
            this.setMainPanel("<h2>Help</h2><p>Select a topic from the left to view details.</p>");
        } catch (e) {
            console.error(e);
            this.setSubPanel("Error loading help topics.");
        }
    }

    async showDoc(filename) {
        try {
            const response = await fetch(`./docs/${filename}`);
            if (!response.ok) throw new Error('Network response was not ok');
            const text = await response.text();
            this.setMainPanel(text);
        } catch (e) {
            this.setMainPanel("Error loading document.");
        }
    }

    doAlignment() {
        this.loadPartial('MainPanel', './partials/alignment_view.html', () => {
             // Re-initialize match explorer logic if needed, or it might rely on global event handlers
             // Since we just loaded the structure, if match_explorer.js is loaded, it might need a trigger
             if (typeof initializeApp === 'function') initializeApp();
        });
    }

    doSearchResults() {
         this.loadPartial('SubPanel', './partials/findings_list.html', () => {
             // For Findings List, we also rely on match_explorer.js
             if (typeof initializeApp === 'function') initializeApp();
         });
    }

    doJobQueue() {
        this.loadPartial('MainPanel', './partials/job_management_content.html', async () => {
             // Init job management
             if (typeof refreshJobs === 'function') {
                 // Re-attach event listeners or state if needed.
                 // app.js has window.addEventListener('load') which ran on page load.
                 // We need to re-run the initialization logic.
                 addLog('Job Queue panel loaded');
                 await refreshJobs();
                 updatePollInterval();
                 // Re-select job if one was selected?
                 if (currentJobId) selectJob(currentJobId, currentJobType);
             }
        });
    }

    // Do not remove this comment.
    // I have my own markdown+ library and do not want another third party one.
    // This function can show most markdown raw, without changing it.
    // Later I will add a markdown processor.
    // Small quick hacks that get the functionality we need are fine here.
    // Mostly we will pass text through unchanged.
    asHtml(text) {
        // Add code to determine the kind of text, and possibly transform it.
        if (text && !text.trim().startsWith('<')) {
             return '<div style="white-space: pre-wrap; font-family: inherit; padding: 10px;">' + text + '</div>';
        }
        return text;
    }
}

const Lcars = new LcarsUI();
