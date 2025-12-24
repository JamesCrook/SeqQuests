class HelpOverlay {
    constructor() {
        this.canvas = document.createElement('canvas');
        this.canvas.style.position = 'fixed';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.pointerEvents = 'none';
        this.canvas.style.zIndex = '9999';
        this.ctx = this.canvas.getContext('2d');
        this.connections = [];
        this.animating = false;

        this.resizeCanvas = this.resizeCanvas.bind(this);
        this.draw = this.draw.bind(this);
    }

    init() {
        if (!this.canvas.parentNode) {
            document.body.appendChild(this.canvas);
        }
        this.resizeCanvas();
        window.addEventListener('resize', this.resizeCanvas);
    }

    addConnection(fromEl, toEl, color = '#64748b') {
        this.connections.push({ from: fromEl, to: toEl, color });
    }

    clearConnections() {
        this.connections = [];
    }

    start() {
        this.init();
        if (!this.animating) {
            this.animating = true;
            this.draw();
        }
    }

    stop() {
        this.animating = false;
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        if (this.canvas.parentNode) {
            this.canvas.parentNode.removeChild(this.canvas);
        }
        window.removeEventListener('resize', this.resizeCanvas);
    }

    resizeCanvas() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    getElementBox(el) {
        if (!el) return null;
        if (el.offsetParent === null) return null;

        const rect = el.getBoundingClientRect();
        return {
            left: rect.left,
            top: rect.top,
            right: rect.right,
            bottom: rect.bottom,
            width: rect.width,
            height: rect.height,
            centerX: rect.left + rect.width / 2,
            centerY: rect.top + rect.height / 2
        };
    }

    getTextBoundingBox(container, searchTerm) {
        if (!searchTerm || searchTerm.length < 2) return null;

        const text = container.textContent;
        const index = text.toLowerCase().indexOf(searchTerm.toLowerCase());

        if (index === -1) return null;

        let charCount = 0;
        let startNode = null;
        let startOffset = 0;
        let endNode = null;
        let endOffset = 0;

        const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, null, false);
        let node;

        while (node = walker.nextNode()) {
            const nodeLength = node.textContent.length;

            if (!startNode && charCount + nodeLength > index) {
                startNode = node;
                startOffset = index - charCount;
            }

            if (startNode && charCount + nodeLength >= index + searchTerm.length) {
                endNode = node;
                endOffset = (index + searchTerm.length) - charCount;
                break;
            }

            charCount += nodeLength;
        }

        if (startNode && endNode) {
            try {
                const range = document.createRange();
                range.setStart(startNode, startOffset);
                range.setEnd(endNode, endOffset);
                const rects = range.getClientRects();

                if (rects.length === 0) return null;

                const rect = rects[0];

                return {
                    left: rect.left,
                    top: rect.top,
                    right: rect.right,
                    bottom: rect.bottom,
                    width: rect.width,
                    height: rect.height,
                    centerX: rect.left + rect.width / 2,
                    centerY: rect.top + rect.height / 2
                };
            } catch (e) {
                return null;
            }
        }
        return null;
    }

    getNearestPoints(box1, box2) {
        const p1 = {
            x: Math.max(box1.left, Math.min(box2.centerX, box1.right)),
            y: Math.max(box1.top, Math.min(box2.centerY, box1.bottom))
        };

        const p2 = {
            x: Math.max(box2.left, Math.min(p1.x, box2.right)),
            y: Math.max(box2.top, Math.min(p1.y, box2.bottom))
        };

        p1.x = Math.max(box1.left, Math.min(p2.x, box1.right));
        p1.y = Math.max(box1.top, Math.min(p2.y, box1.bottom));

        return { p1, p2 };
    }

    drawArrow(ctx, fromX, fromY, toX, toY, color = '#64748b') {
        const headlen = 12;
        const dx = toX - fromX;
        const dy = toY - fromY;
        const dist = Math.sqrt(dx*dx + dy*dy);
        const angle = Math.atan2(dy, dx);

        if (dist < 1) return;

        ctx.beginPath();
        ctx.moveTo(fromX, fromY);
        ctx.lineTo(toX, toY);
        ctx.strokeStyle = color;
        ctx.lineWidth = 2.5;
        ctx.lineCap = 'round';
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(toX, toY);
        ctx.lineTo(toX - headlen * Math.cos(angle - Math.PI / 7), toY - headlen * Math.sin(angle - Math.PI / 7));
        ctx.lineTo(toX - headlen * Math.cos(angle + Math.PI / 7), toY - headlen * Math.sin(angle + Math.PI / 7));
        ctx.closePath();
        ctx.fillStyle = color;
        ctx.fill();
    }

    drawHighlightBox(ctx, box) {
        if (!box) return;
        ctx.strokeStyle = '#ef4444';
        ctx.lineWidth = 2;
        ctx.setLineDash([4, 2]);
        ctx.strokeRect(box.left - 2, box.top - 2, box.width + 4, box.height + 4);
        ctx.setLineDash([]);
        ctx.fillStyle = 'rgba(239, 68, 68, 0.1)';
        ctx.fillRect(box.left - 2, box.top - 2, box.width + 4, box.height + 4);
    }

    makeDraggable(el) {
        let isDragging = false;
        let startX, startY, initialLeft, initialTop;

        el.addEventListener('mousedown', (e) => {
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            const style = window.getComputedStyle(el);
            initialLeft = parseInt(style.left) || 0;
            initialTop = parseInt(style.top) || 0;
            el.style.cursor = 'grabbing';
        });

        window.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            el.style.left = `${initialLeft + (e.clientX - startX)}px`;
            el.style.top = `${initialTop + (e.clientY - startY)}px`;
        });

        window.addEventListener('mouseup', () => {
            isDragging = false;
            el.style.cursor = 'move';
        });
    }

    draw() {
        if (!this.animating) return;

        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        const isInViewport = (b) => b && (
            b.bottom > 0 && b.top < window.innerHeight &&
            b.right > 0 && b.left < window.innerWidth
        );

        for (const conn of this.connections) {
            let b1 = this.getElementBox(conn.from);

            if (!b1 && conn.fromText && conn.container) {
                b1 = this.getTextBoundingBox(conn.container, conn.fromText);
                if (b1) this.drawHighlightBox(this.ctx, b1);
            }

            const b2 = this.getElementBox(conn.to);

            if (isInViewport(b1) && isInViewport(b2)) {
                const { p1, p2 } = this.getNearestPoints(b1, b2);
                this.drawArrow(this.ctx, p1.x, p1.y, p2.x, p2.y, conn.color);
            }
        }

        requestAnimationFrame(this.draw);
    }
}

window.HelpOverlay = HelpOverlay;
