function addBackCircle() {
    // 1. Define the Styles
    const styles = `
        #nav-utility-btn {
            position: fixed;
            top: 20px;
            left: 20px;
            width: 40px;
            height: 40px;
            background-color: #0003;
            color: white;
            border-radius: 20px;
            border: 1px solid #fff3;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            z-index: 9999;
            transition: transform 0.2s ease;
        }
        #nav-utility-btn:hover { transform: scale(1.05); }
        .icon-bar {
            width: 20px;
            height: 2px;
            background-color: white;
            margin: 4px 0;
            border-radius: 2px;
        }
    `;

    const styleSheet = document.createElement("style");
    styleSheet.innerText = styles;
    document.head.appendChild(styleSheet);

    // 2. Determine presence of history
    // length > 1 usually indicates the user didn't land here directly
    const hasHistory = window.history.length > 1;

    // 3. Create the Button
    const btn = document.createElement('div');
    btn.id = 'nav-utility-btn';

    if (hasHistory ) {
        // Back Button Style (Arrow)
        btn.innerHTML = '<div>←</div>';
        btn.onclick = () => window.history.back();
    } else {
        // Hamburger Style (3 Lines)
        btn.innerHTML = `
            <div>
                <div class="icon-bar"></div>
                <div class="icon-bar"></div>
                <div class="icon-bar"></div>
            </div>
        `;
        btn.onclick = () => window.location.href = "https://catalase.com/";
    }

    // 4. Append to Body
    document.body.appendChild(btn);
};

document.addEventListener('DOMContentLoaded', addBackCircle);