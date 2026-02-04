/* ============================================
   OmniBase - Generic Control Panel Framework
   ============================================
   
   Handles:
   - Layout management (portrait/landscape switching)
   - Building controls from config (sliders, presets, selects, buttons, dynamic containers)
   - Animating between presets
   - Tabbed scroll navigation (multiscroller)
   - Optional pan/zoom on container (for 2D SVG)
   - Legend toggle
   
   Usage:
   const base = new OmniBase({
     elements: { svg, container, controls, multiscroller, legendToggle, legend },
     sliderConfig: [...],
     presets: { 'Name': { param: value, ... }, ... },
     defaultPreset: 'Name',
     enablePanZoom: true,  // Set false for 3D apps with their own controls
     onRender: (params, panZoom, instance) => { ... },
     onParamChange: (id, value, isData, instance) => { ... },
     onLegendToggle: (showLegend, instance) => { ... },
     onResize: (instance) => { ... },
     hintHtml: 'Optional hint text'
   });
   
   base.setPreset('Name');
   base.updateSlider('id', value);
   base.setStatus('message', isError);
   base.render();
*/

class OmniBase {
  constructor(config) {
    this.elements = config.elements;
    this.sliderConfig = config.sliderConfig;
    this.presets = config.presets || {};
    this.defaultPreset = config.defaultPreset;
    this.onRender = config.onRender;
    this.onParamChange = config.onParamChange || (() => {});
    this.onLegendToggle = config.onLegendToggle || (() => {});
    this.onResize = config.onResize || (() => {});
    this.hintHtml = config.hintHtml || '';
    this.enablePanZoom = config.enablePanZoom !== false; // Default true
    
    // Layout constants
    this.ASPECT_RATIO = config.aspectRatio || (800 / 650);
    this.CONTROLS_WIDTH = 320;
    this.HEADER_HEIGHT = 30;
    this.MIN_CONTROLS_HEIGHT = 210;
    this.PADDING = 20;
    
    // State
    this.params = {};
    this.panZoom = { panX: 0, panY: 0 };
    this.showLegend = true;
    this.isDragging = false;
    this.dragStart = { x: 0, y: 0 };
    this.panStart = { panX: 0, panY: 0 };
    this.clickedSectionId = null;
    
    // Store references to dynamic elements
    this.dynamicContainers = {};
    this.statusEl = null;
    this.infoEl = null;
    
    // Initialize params from config defaults
    this._initParams();
    
    // Build UI
    this._buildMultiscroller();
    this._buildControls();
    this._setupScrollTracking();
    if (this.enablePanZoom) {
      this._setupPanZoom();
    }
    this._setupLegendToggle();
    this._setupLayout();
    
    // Apply default preset
    if (this.defaultPreset && this.presets[this.defaultPreset]) {
      this._applyPresetImmediate(this.defaultPreset);
      this._setActivePreset(this.defaultPreset);
    }
    
    this._updateActiveStripButton(this.sliderConfig[0]?.id);
    
    // Initial render
    this.render();
    
    // Update multiscroller names after layout settles
    requestAnimationFrame(() => this._updateMultiscrollerNames());
  }
  
  // ============================================================
  // Public API
  // ============================================================
  
  render() {
    if (this.onRender) {
      this.onRender(this.params, this.panZoom, this);
    }
  }
  
  setPreset(name, animate = true) {
    if (!this.presets[name]) return;
    
    if (animate) {
      this._animateToPreset(name);
    } else {
      this._applyPresetImmediate(name);
      this._setActivePreset(name);
      this.render();
    }
  }
  
  updateSlider(id, value, render = true) {
    this.params[id] = value;
    
    const input = document.getElementById(id);
    const valEl = document.getElementById(`${id}-val`);
    const slider = this._findSlider(id);
    
    if (input) input.value = value;
    if (valEl && slider) valEl.textContent = this._formatValue(value, slider.format);
    
    if (render) this.render();
  }
  
  // Update multiple sliders at once (more efficient)
  updateSliders(updates, render = true) {
    for (const [id, value] of Object.entries(updates)) {
      this.params[id] = value;
      
      const input = document.getElementById(id);
      const valEl = document.getElementById(`${id}-val`);
      const slider = this._findSlider(id);
      
      if (input) input.value = value;
      if (valEl && slider) valEl.textContent = this._formatValue(value, slider.format);
    }
    
    if (render) this.render();
  }
  
  getParams() {
    return { ...this.params };
  }
  
  setParam(id, value) {
    this.params[id] = value;
  }
  
  getPanZoom() {
    return { ...this.panZoom };
  }
  
  resetPanZoom() {
    this.panZoom = { panX: 0, panY: 0 };
    this.render();
  }
  
  // Status message helpers
  setStatus(message, isError = false) {
    if (this.statusEl) {
      this.statusEl.textContent = message;
      this.statusEl.classList.toggle('error', isError);
    }
  }
  
  clearStatus() {
    if (this.statusEl) {
      this.statusEl.textContent = '';
      this.statusEl.classList.remove('error');
    }
  }
  
  // Info panel helpers
  setInfo(html) {
    if (this.infoEl) {
      this.infoEl.innerHTML = html;
      this.infoEl.classList.add('visible');
    }
  }
  
  clearInfo() {
    if (this.infoEl) {
      this.infoEl.innerHTML = '';
      this.infoEl.classList.remove('visible');
    }
  }
  
  // Dynamic container helpers
  getDynamicContainer(id) {
    return this.dynamicContainers[id];
  }
  
  // Enable/disable a control
  setControlEnabled(id, enabled) {
    const el = document.getElementById(id);
    if (el) el.disabled = !enabled;
  }
  
  // Set select value
  setSelectValue(id, value) {
    const el = document.getElementById(id);
    if (el) el.value = value;
  }
  
  // ============================================================
  // Private: Initialization
  // ============================================================
  
  _initParams() {
    for (const group of this.sliderConfig) {
      if (group.sliders) {
        for (const s of group.sliders) {
          if (!s.isData) {
            this.params[s.id] = s.default;
          }
        }
      }
    }
  }
  
  _findSlider(id) {
    for (const group of this.sliderConfig) {
      if (group.sliders) {
        const slider = group.sliders.find(s => s.id === id);
        if (slider) return slider;
      }
    }
    return null;
  }
  
  // ============================================================
  // Private: Layout Management
  // ============================================================
  
  _setupLayout() {
    const updateLayout = () => {
      const W = window.innerWidth;
      const H = window.innerHeight;
      
      const H1 = this.HEADER_HEIGHT + this.MIN_CONTROLS_HEIGHT + this.PADDING;
      const W1 = this.CONTROLS_WIDTH + this.PADDING;
      
      const landscapeChartWidth = W - W1;
      const portraitChartWidth = this.ASPECT_RATIO * (H - H1);
      
      const useLandscape = landscapeChartWidth > portraitChartWidth;
      
      document.body.classList.toggle('layout-landscape', useLandscape);
      document.body.classList.toggle('layout-portrait', !useLandscape);
      
      this.onResize(this);
    };
    
    updateLayout();
    window.addEventListener('resize', () => {
      updateLayout();
      this._updateMultiscrollerNames();
    });
  }
  
  // ============================================================
  // Private: Multiscroller (Tab Strip)
  // ============================================================
  
  _buildMultiscroller() {
    const el = this.elements.multiscroller;
    if (!el) return;
    
    for (const group of this.sliderConfig) {
      const btn = document.createElement('button');
      btn.className = 'strip-btn';
      btn.dataset.section = group.id;
      btn.textContent = group.abbrev || group.group.substring(0, 3);
      
      btn.addEventListener('click', () => {
        if (btn.classList.contains('inactive')) return;
        const section = document.getElementById(`section-${group.id}`);
        if (section) {
          this.clickedSectionId = group.id;
          this._updateActiveStripButton(group.id);
          section.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      });
      
      el.appendChild(btn);
    }
  }
  
  _updateActiveStripButton(activeId) {
    const el = this.elements.multiscroller;
    if (!el) return;
    
    el.querySelectorAll('.strip-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.section === activeId);
    });
    
    this.elements.controls?.querySelectorAll('.control-group').forEach(group => {
      const sectionId = group.id.replace('section-', '');
      group.classList.toggle('active', sectionId === activeId);
    });
  }
  
  _updateMultiscrollerNames(retryCount = 0) {
    const el = this.elements.multiscroller;
    if (!el) return;
    
    const buttons = el.querySelectorAll('.strip-btn');
    const stripHeight = el.clientHeight;
    
    if (stripHeight < 100 && retryCount < 3) {
      requestAnimationFrame(() => this._updateMultiscrollerNames(retryCount + 1));
      return;
    }
    
    const useFullNames = stripHeight >= 400;
    
    buttons.forEach((btn, i) => {
      btn.textContent = useFullNames 
        ? this.sliderConfig[i].group 
        : (this.sliderConfig[i].abbrev || this.sliderConfig[i].group.substring(0, 3));
    });
    
    el.classList.toggle('full-names', useFullNames);
  }
  
  _setupScrollTracking() {
    const controlsEl = this.elements.controls;
    if (!controlsEl) return;
    
    const updateButtonStates = () => {
      const scrollTop = controlsEl.scrollTop;
      const panelHeight = controlsEl.clientHeight;
      const scrollBottom = scrollTop + panelHeight;
      const maxScroll = controlsEl.scrollHeight - panelHeight;
      const hasScroll = maxScroll > 5;
      const isAtBottom = hasScroll && scrollTop >= maxScroll - 1;
      
      const buttons = this.elements.multiscroller?.querySelectorAll('.strip-btn');
      if (!buttons) return;
      
      let computedActiveSection = this.sliderConfig[0]?.id;
      
      buttons.forEach((btn, i) => {
        const section = document.getElementById(`section-${this.sliderConfig[i].id}`);
        if (!section) return;
        
        const sectionTop = section.offsetTop;
        const sectionBottom = sectionTop + section.offsetHeight;
        
        if (sectionTop <= scrollTop + 20) {
          computedActiveSection = this.sliderConfig[i].id;
        }
        
        const fullyVisible = sectionTop >= scrollTop - 1 && sectionBottom <= scrollBottom + 1;
        const isInactive = isAtBottom && fullyVisible;
        
        btn.classList.toggle('inactive', isInactive);
      });
      
      if (!this.clickedSectionId) {
        this._updateActiveStripButton(computedActiveSection);
      }
    };
    
    controlsEl.addEventListener('wheel', () => { this.clickedSectionId = null; }, { passive: true });
    controlsEl.addEventListener('touchstart', () => { this.clickedSectionId = null; }, { passive: true });
    controlsEl.addEventListener('scroll', updateButtonStates);
    
    updateButtonStates();
    window.addEventListener('resize', updateButtonStates);
  }
  
  // ============================================================
  // Private: Control Building
  // ============================================================
  
  _buildControls() {
    const controlsEl = this.elements.controls;
    if (!controlsEl) return;
    
    for (const group of this.sliderConfig) {
      const groupEl = document.createElement('div');
      groupEl.className = 'control-group';
      groupEl.id = `section-${group.id}`;
      
      const h3 = document.createElement('h3');
      h3.textContent = group.group;
      groupEl.appendChild(h3);
      
      // Handle different control types
      if (group.type === 'presets') {
        this._buildPresets(groupEl);
      } else if (group.type === 'select') {
        this._buildSelect(groupEl, group);
      } else if (group.type === 'filedrop') {
        this._buildFileDrop(groupEl, group);
      } else if (group.type === 'button') {
        this._buildButton(groupEl, group);
      } else if (group.type === 'status') {
        this._buildStatus(groupEl, group);
      } else if (group.type === 'info') {
        this._buildInfo(groupEl, group);
      } else if (group.type === 'dynamic') {
        this._buildDynamic(groupEl, group);
      } else if (group.type === 'custom') {
        // Custom content built by the app
        if (group.build) group.build(groupEl, this);
      } else if (group.sliders) {
        this._buildSliders(groupEl, group.sliders);
      }
      
      controlsEl.appendChild(groupEl);
    }
    
    // Add hint if provided
    if (this.hintHtml) {
      const hint = document.createElement('p');
      hint.className = 'hint';
      hint.innerHTML = this.hintHtml;
      controlsEl.appendChild(hint);
    }
  }
  
  _buildPresets(groupEl) {
    const presetsEl = document.createElement('div');
    presetsEl.className = 'presets';
    presetsEl.id = 'presets';
    
    for (const name of Object.keys(this.presets)) {
      const btn = document.createElement('button');
      btn.className = 'preset-btn';
      btn.textContent = name;
      btn.onclick = () => this.setPreset(name);
      presetsEl.appendChild(btn);
    }
    
    groupEl.appendChild(presetsEl);
  }
  
  _buildSliders(groupEl, sliders) {
    for (const s of sliders) {
      const controlEl = document.createElement('div');
      controlEl.className = 'control';
      
      const label = document.createElement('label');
      const nameSpan = document.createElement('span');
      nameSpan.textContent = s.label;
      const valSpan = document.createElement('span');
      valSpan.id = `${s.id}-val`;
      
      const initVal = s.isData 
        ? (s.dataValue || s.default)
        : (this.params[s.id] ?? s.default);
      valSpan.textContent = this._formatValue(initVal, s.format);
      
      label.appendChild(nameSpan);
      label.appendChild(valSpan);
      
      const input = document.createElement('input');
      input.type = 'range';
      input.id = s.id;
      input.min = s.min;
      input.max = s.max;
      input.step = s.step;
      input.value = initVal;
      if (s.disabled) input.disabled = true;
      
      input.addEventListener('input', (e) => {
        const val = parseFloat(e.target.value);
        valSpan.textContent = this._formatValue(val, s.format);
        
        if (s.isData) {
          this.onParamChange(s.id, val, true, this);
        } else {
          this.params[s.id] = val;
          this.onParamChange(s.id, val, false, this);
        }
        
        this.render();
        this._clearActivePreset();
      });
      
      controlEl.appendChild(label);
      controlEl.appendChild(input);
      groupEl.appendChild(controlEl);
    }
  }
  
  _buildSelect(groupEl, group) {
    const controlEl = document.createElement('div');
    controlEl.className = 'control';
    
    if (group.label) {
      const label = document.createElement('label');
      label.innerHTML = `<span>${group.label}</span>`;
      controlEl.appendChild(label);
    }
    
    const select = document.createElement('select');
    select.id = group.selectId || group.id;
    
    for (const opt of (group.options || [])) {
      const option = document.createElement('option');
      option.value = opt.value;
      option.textContent = opt.label;
      select.appendChild(option);
    }
    
    select.addEventListener('change', (e) => {
      if (group.onChange) {
        group.onChange(e.target.value, this);
      } else {
        this.onParamChange(group.id, e.target.value, false, this);
        this.render();
      }
    });
    
    controlEl.appendChild(select);
    groupEl.appendChild(controlEl);
  }
  
  _buildButton(groupEl, group) {
    const btn = document.createElement('button');
    btn.className = 'btn' + (group.secondary ? ' secondary' : '');
    btn.id = group.buttonId || group.id;
    btn.textContent = group.label || 'Button';
    
    btn.addEventListener('click', () => {
      if (group.onClick) group.onClick(this);
    });
    
    groupEl.appendChild(btn);
  }
  
  _buildStatus(groupEl, group) {
    const statusEl = document.createElement('div');
    statusEl.className = 'status-message';
    statusEl.id = group.statusId || 'status';
    this.statusEl = statusEl;
    groupEl.appendChild(statusEl);
  }
  
  _buildInfo(groupEl, group) {
    const infoEl = document.createElement('div');
    infoEl.className = 'info-panel';
    infoEl.id = group.infoId || 'info';
    this.infoEl = infoEl;
    groupEl.appendChild(infoEl);
  }
  
  _buildDynamic(groupEl, group) {
    const containerEl = document.createElement('div');
    containerEl.className = 'dynamic-controls';
    containerEl.id = group.containerId || group.id;
    this.dynamicContainers[group.id] = containerEl;
    groupEl.appendChild(containerEl);
  }
  
  _buildFileDrop(groupEl, group) {
    const dropEl = document.createElement('div');
    dropEl.className = 'file-drop';
    dropEl.id = group.id;
    dropEl.innerHTML = `
      <div class="file-drop-icon">📁</div>
      <div>${group.label || 'Drop files here'}</div>
    `;
    
    dropEl.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropEl.classList.add('dragover');
    });
    
    dropEl.addEventListener('dragleave', () => {
      dropEl.classList.remove('dragover');
    });
    
    dropEl.addEventListener('drop', (e) => {
      e.preventDefault();
      dropEl.classList.remove('dragover');
      const files = e.dataTransfer.files;
      if (group.onDrop) group.onDrop(files, this);
    });
    
    dropEl.addEventListener('click', () => {
      const input = document.createElement('input');
      input.type = 'file';
      input.multiple = group.multiple || false;
      input.accept = group.accept || '*';
      input.onchange = () => {
        if (group.onDrop) group.onDrop(input.files, this);
      };
      input.click();
    });
    
    groupEl.appendChild(dropEl);
  }
  
  // ============================================================
  // Private: Preset Animation
  // ============================================================
  
  _animateToPreset(name) {
    const preset = this.presets[name];
    if (!preset) return;
    
    const startParams = { ...this.params };
    const duration = 600;
    const startTime = performance.now();
    
    const animate = (currentTime) => {
      const elapsed = currentTime - startTime;
      const t = Math.min(1, elapsed / duration);
      const eased = 1 - Math.pow(1 - t, 3); // ease-out cubic
      
      for (const group of this.sliderConfig) {
        if (!group.sliders) continue;
        for (const s of group.sliders) {
          if (s.isData) continue;
          if (preset[s.id] === undefined) continue;
          
          this.params[s.id] = startParams[s.id] + (preset[s.id] - startParams[s.id]) * eased;
          
          const input = document.getElementById(s.id);
          const valEl = document.getElementById(`${s.id}-val`);
          if (input) input.value = this.params[s.id];
          if (valEl) valEl.textContent = this._formatValue(this.params[s.id], s.format);
        }
      }
      
      this.render();
      
      if (t < 1) {
        requestAnimationFrame(animate);
      } else {
        this._setActivePreset(name);
      }
    };
    
    requestAnimationFrame(animate);
  }
  
  _applyPresetImmediate(name) {
    const preset = this.presets[name];
    if (!preset) return;
    
    for (const group of this.sliderConfig) {
      if (!group.sliders) continue;
      for (const s of group.sliders) {
        if (s.isData) continue;
        if (preset[s.id] === undefined) continue;
        
        this.params[s.id] = preset[s.id];
        
        const input = document.getElementById(s.id);
        const valEl = document.getElementById(`${s.id}-val`);
        if (input) input.value = this.params[s.id];
        if (valEl) valEl.textContent = this._formatValue(this.params[s.id], s.format);
      }
    }
  }
  
  _setActivePreset(name) {
    document.querySelectorAll('.preset-btn').forEach(btn => {
      btn.classList.toggle('active', btn.textContent === name);
    });
  }
  
  _clearActivePreset() {
    document.querySelectorAll('.preset-btn').forEach(btn => btn.classList.remove('active'));
  }
  
  // ============================================================
  // Private: Pan/Zoom (for 2D SVG apps)
  // ============================================================
  
  _setupPanZoom() {
    const container = this.elements.container;
    const svg = this.elements.svg;
    if (!container || !svg) return;
    
    // Mouse pan
    container.addEventListener('mousedown', (e) => {
      this.isDragging = true;
      this.dragStart = { x: e.clientX, y: e.clientY };
      this.panStart = { ...this.panZoom };
    });
    
    window.addEventListener('mousemove', (e) => {
      if (!this.isDragging) return;
      const rect = svg.getBoundingClientRect();
      const viewBox = svg.getAttribute('viewBox')?.split(' ').map(Number) || [0, 0, 800, 650];
      const scaleX = viewBox[2] / rect.width;
      const scaleY = viewBox[3] / rect.height;
      this.panZoom.panX = this.panStart.panX + (e.clientX - this.dragStart.x) * scaleX;
      this.panZoom.panY = this.panStart.panY + (e.clientY - this.dragStart.y) * scaleY;
      this.render();
    });
    
    window.addEventListener('mouseup', () => this.isDragging = false);
    
    // Touch pan
    container.addEventListener('touchstart', (e) => {
      if (e.touches.length === 1) {
        this.isDragging = true;
        this.dragStart = { x: e.touches[0].clientX, y: e.touches[0].clientY };
        this.panStart = { ...this.panZoom };
      }
    }, { passive: true });
    
    container.addEventListener('touchmove', (e) => {
      if (!this.isDragging || e.touches.length !== 1) return;
      const rect = svg.getBoundingClientRect();
      const viewBox = svg.getAttribute('viewBox')?.split(' ').map(Number) || [0, 0, 800, 650];
      const scaleX = viewBox[2] / rect.width;
      const scaleY = viewBox[3] / rect.height;
      this.panZoom.panX = this.panStart.panX + (e.touches[0].clientX - this.dragStart.x) * scaleX;
      this.panZoom.panY = this.panStart.panY + (e.touches[0].clientY - this.dragStart.y) * scaleY;
      this.render();
    }, { passive: true });
    
    container.addEventListener('touchend', () => this.isDragging = false);
    
    // Wheel zoom (disabled on touch devices)
    const isTouchDevice = () => 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    
    container.addEventListener('wheel', (e) => {
      if (isTouchDevice()) return;
      e.preventDefault();
      
      this.params.zoom = Math.max(0.25, Math.min(2, (this.params.zoom || 1) - e.deltaY * 0.001));
      
      const input = document.getElementById('zoom');
      const valEl = document.getElementById('zoom-val');
      if (input) input.value = this.params.zoom;
      if (valEl) valEl.textContent = this._formatValue(this.params.zoom);
      
      this.render();
    }, { passive: false });
  }
  
  // ============================================================
  // Private: Legend Toggle
  // ============================================================
  
  _setupLegendToggle() {
    const toggle = this.elements.legendToggle;
    if (!toggle) return;
    
    toggle.addEventListener('click', () => {
      this.showLegend = !this.showLegend;
      toggle.classList.toggle('active', this.showLegend);
      this.elements.multiscroller?.classList.toggle('multiscroller-unlocked', !this.showLegend);
      this.onLegendToggle(this.showLegend, this);
    });
  }
  
  // ============================================================
  // Private: Utilities
  // ============================================================
  
  _formatValue(val, format) {
    if (format === 'deg') return `${Math.round(val * 180 / Math.PI)}°`;
    if (format === 'int') return Math.round(val);
    if (format === 'degInt') return `${Math.round(val)}°`;
    return val.toFixed(2);
  }
}

// Export for use in modules or global scope
if (typeof module !== 'undefined' && module.exports) {
  module.exports = OmniBase;
} else if (typeof window !== 'undefined') {
  window.OmniBase = OmniBase;
}