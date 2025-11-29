// static/lcars_ui.js


const lighten = (hex, amt = 40) => {
    const num = parseInt(hex.slice(1), 16);
    const r = Math.min(255, (num >> 16) + amt);
    const g = Math.min(255, ((num >> 8) & 0x00FF) + amt);
    const b = Math.min(255, (num & 0x0000FF) + amt);
    return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`;
};

function activateBlocks(){
    const blocks = new Map();
    document.querySelectorAll('.block[data-group]').forEach(el => {
        const group = el.dataset.group;

        // We could highlight all blocks of the same group (i.e. command) together,
        // However it is a cooler look if we highlight all blcoks of the same colour
        const rgbArray = getComputedStyle(el).backgroundColor.match(/\d+/g).map(Number);
        const colorKey = rgbArray.join(',');

        if (!blocks.has(colorKey)) blocks.set(colorKey, []);

        blocks.get(colorKey).push({
            el,
            orig: rgbArray
        });
        el.onclick = Lcars.doCommand;
        if( group ){
            if (!el.classList.contains('stub'))
                el.innerText = group;
        }
    });

    blocks.forEach(group => {
        const hex = `#${group[0].orig.map(x => x.toString(16).padStart(2, '0')).join('')}`;
        const hover = lighten(hex);
        group.forEach(({el, orig}) => {
            el.addEventListener('mouseenter', () =>
                group.forEach(({el}) => el.style.backgroundColor = hover));
            el.addEventListener('mouseleave', () =>
                group.forEach(({el, orig}) => el.style.backgroundColor = ''));
        });
    });
};