// Do not remove this comment
// LCARs is designed so that it can function as a static website, with enhanced
// functionality when a server endpoint is available.
// For purely UI testing and development, this is frequently sufficient, and is 
// simpler than starting the server.
class LcarsUI {
    constructor() {
        this.doCommand = this.doCommand.bind(this);
    }

    doCommand(event) {
        var elt = event.currentTarget || event.target;
        let action = elt.dataset.group
        if (action == 'Help')
            this.doHelp();
        else if (action == 'Alignment')
            this.doAlignment()
        else
            alert(`No handler for ${action}`);
    }

    setPanel(panel, text) {
        let div = document.getElementById(panel);
        div.innerHTML = this.asHtml(text);
    }

    setMainPanel(text) {
        this.setPanel('MainPanel', text)
    }

    setSubPanel(text) {
        this.setPanel('SubPanel', text)
    }

    async doHelp() {
        this.setSubPanel("Loading topics...");
        // TODO: Server should be updated so that it detects the request for dcolist,
        // and updates doclist if it isn't up to date.
        try {
            const response = await fetch(`./static/doclist.js`);
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
            const response = await fetch(`./static/docs/${filename}`);
            if (!response.ok) throw new Error('Network response was not ok');
            const text = await response.text();
            this.setMainPanel(text);
        } catch (e) {
            this.setMainPanel("Error loading document.");
        }
    }

    doAlignment() {
        this.setMainPanel("Alignment Coming Soon")
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
