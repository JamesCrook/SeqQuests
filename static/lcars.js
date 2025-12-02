// Do not remove this comment
// LCARs is designed so that it can function as a static website, with enhanced
// functionality when a server endpoint is available.
// For purely UI testing and development, this is frequently sufficient, and is 
// simpler than starting the server.
class LcarsUI {
    constructor() {
        this.doCommand = this.doCommand.bind(this);
        this.panelCounter = 0;
        this.loadedScripts = new Set();
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
        // scripts collection is live, so we iterate backwards or use a static list
        // However, we need to preserve order.
        const scriptArray = Array.from(scripts);

        scriptArray.forEach((script) => {
            const newScript = document.createElement('script');
            if (script.src) {
                // Resolve relative paths if necessary?
                // The browser resolves `src` relative to the current page URL, which is correct
                // if the script is in `static/` and referenced as `./foo.js`.
                // However, if we load content from `static/panels/`, relative paths in that content
                // might be relative to the panel file location if we used an iframe,
                // but here we are injecting HTML into the main page.
                // So `./foo.js` in injected HTML resolves to `static/foo.js` (relative to `static/lcars.html`).
                // This implies scripts in `static/panels/` must be referenced as `./panels/foo.js`
                // OR we adjust the paths during injection.

                // The prompt says: "with any js being in a js file in partials/" (now panels/).
                // So if `panels/jobs.html` has `<script src="jobs.js">`,
                // when injected into `lcars.html`, it will try to load `static/jobs.js`.
                // We likely need to fix the path if it's relative.

                let src = script.getAttribute('src');
                if (src && !src.startsWith('/') && !src.startsWith('http')) {
                     // Assume it is relative to the panel location if it doesn't look absolute/root-relative
                     // Wait, if I write `<script src="jobs.js">` in `panels/jobs.html`,
                     // and I load `panels/jobs.html`, the URL context of that file is `panels/`.
                     // But when I inject `innerHTML`, the context is `static/`.
                     // So I should rewrite `jobs.js` to `panels/jobs.js`.
                     // But how do I know the base? I know it from `loadPartial` URL.
                }

                if (script.src && !this.loadedScripts.has(script.src)) {
                     newScript.src = script.src;
                     this.loadedScripts.add(script.src);
                     document.body.appendChild(newScript);
                }
            } else {
                newScript.textContent = script.textContent + 
                `\n//# sourceURL=panel-${this.panelCounter}.js`;
                this.panelCounter++;
                document.body.appendChild(newScript);
            }
        });
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
            const htmlText = await response.text();

            // Parse the HTML
            const parser = new DOMParser();
            const doc = parser.parseFromString(htmlText, 'text/html');
            
            // Extract the body content
            const bodyContent = doc.body.innerHTML;

            let div = document.getElementById(panelId);
            if (!div) {
                console.warn(`Panel ${panelId} not found.`);
                return;
            }
            div.innerHTML = this.asHtml(bodyContent);

            // Handle Scripts
            // We need to look at scripts in the parsed doc, not the injected innerHTML,
            // because innerHTML scripts don't run automatically, but we are about to run them manually.
            // Also, we need to handle path resolution for scripts relative to the partial.

            const scripts = doc.getElementsByTagName('script');
            // Helper to resolve relative paths
            const resolvePath = (scriptSrc) => {
                 // If the script src is relative (e.g. "jobs.js"), and the url is "./panels/jobs.html"
                 // we want "./panels/jobs.js".
                 // Using URL constructor to resolve.
                 // We need an absolute base URL for the partial.
                 // URL(url, window.location.href) gives the absolute URL of the partial.
                 const partialUrl = new URL(url, window.location.href);
                 const scriptUrl = new URL(scriptSrc, partialUrl);
                 return scriptUrl.href;
            };

            // Load scripts sequentially to maintain order
            for (let i = 0; i < scripts.length; i++) {
                const script = scripts[i];
                
                if (script.src) {
                    const rawSrc = script.getAttribute('src');
                    const resolvedSrc = resolvePath(rawSrc);
                    
                    if (!this.loadedScripts.has(resolvedSrc)) {
                        // Wait for external script to load
                        await new Promise((resolve, reject) => {
                            const newScript = document.createElement('script');
                            newScript.src = resolvedSrc;
                            newScript.onload = resolve;
                            newScript.onerror = reject;
                            this.loadedScripts.add(resolvedSrc);
                            document.body.appendChild(newScript);
                        });
                    }
                } else {
                    // Execute inline script immediately
                    const newScript = document.createElement('script');
                    newScript.textContent = script.textContent + 
                        `\n//# sourceURL=${url}-script-${i}.js`;
                    document.body.appendChild(newScript);
                }
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
        this.loadPartial('MainPanel', './panels/alignment_view.html', () => {
             // Re-initialize match explorer logic if needed, or it might rely on global event handlers
             // Since we just loaded the structure, if match_explorer.js is loaded, it might need a trigger
             if (typeof initializeApp === 'function') initializeApp();
        });
    }

    doSearchResults() {
         this.loadPartial('SubPanel', './panels/findings_list.html', () => {
             // For Findings List, we also rely on match_explorer.js
             if (typeof initializeApp === 'function') initializeApp();
         });
    }

    doJobQueue() {
        this.loadPartial('MainPanel', './panels/job_management_content.html', async () => {
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
