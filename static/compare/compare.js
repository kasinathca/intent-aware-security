// ── UTILITIES ──
let currentScenario = 'a';
let currentStep = 0;
let steps = [];
let isPlaying = false;
let playInterval = null;

// Live clock
function updateClocks() {
    const now = new Date();
    const t = now.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });

    // Update multiple clock elements if they exist
    const lockTime = document.getElementById('lock-time');
    const victimTime = document.getElementById('victim-time');

    // Also update date on lock screen
    const dateOptions = { weekday: 'long', month: 'long', day: 'numeric' };
    const d = now.toLocaleDateString('en-US', dateOptions);
    const lockDate = document.getElementById('lock-date');

    if (lockTime) lockTime.textContent = t.replace(' AM', '').replace(' PM', '');
    if (victimTime) victimTime.textContent = t.replace(' AM', '').replace(' PM', '');
    if (lockDate) lockDate.textContent = d;
}
updateClocks();
setInterval(updateClocks, 10000);

// ── DOM HELPERS ──
function showVictimState(id) {
    document.querySelectorAll('.screen-state').forEach(e => e.classList.remove('visible'));
    const el = document.getElementById(id);
    if (el) el.classList.add('visible');
}

function showRogueSMS(text) {
    const el = document.getElementById('att-sms');
    const txt = document.getElementById('att-sms-text');
    if (text) {
        txt.innerHTML = text;
        el.style.transform = 'translateY(0)';
    } else {
        el.style.transform = 'translateY(-150px)';
    }
}

function gwLog(html) {
    const log = document.getElementById('gw-log');
    const time = new Date().toLocaleTimeString('en-GB');
    log.innerHTML += `<span class="gl"><span style="opacity:0.5">[${time}]</span> ${html}</span>`;
    log.scrollTop = log.scrollHeight;
}

function gwStatus(text, cls) {
    const s = document.getElementById('gw-status');
    s.textContent = text;
    s.className = 'gw-status ' + cls;
}

function gwIcon(icon) {
    document.getElementById('gw-icon').textContent = icon;
}

function laptopLine(html) {
    const t = document.getElementById('laptop-term');
    t.innerHTML += `<span class="lt-line">${html}</span>`;
    t.scrollTop = t.scrollHeight;
}

function setStepHighlight(id, state) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.remove('active', 'done');
    if (state) el.classList.add(state);
}

function fillOtpDigits(count) {
    const otp = '847291';
    document.querySelectorAll('#otp-digits .otp-cell').forEach((d, i) => {
        d.classList.remove('filled');
        if (i < count) {
            d.textContent = otp[i];
            d.classList.add('filled');
        } else {
            d.textContent = '';
        }
    });
}

function rogueLog(text, cls = '') {
    const feed = document.getElementById('rogue-feed');
    const span = document.createElement('span');
    span.className = 'rogue-feed-line' + (cls ? ' ' + cls : '');
    span.textContent = text;
    feed.appendChild(span);
    // Keep only last 8 lines
    while (feed.children.length > 8) feed.removeChild(feed.firstChild);
    feed.scrollTop = feed.scrollHeight;
}

// ── AUTO PLAY ──
function togglePlay() {
    if (isPlaying) {
        stopPlay();
    } else {
        startPlay();
    }
}

function startPlay() {
    if (currentStep >= steps.length) {
        resetSim();
    }
    isPlaying = true;
    document.getElementById('play-btn').innerHTML = '<span class="material-symbols-outlined">pause</span> Pause';
    document.getElementById('play-btn').classList.add('active');

    if (currentStep === 0) goNext();

    // Variable timing could be implemented here, but fixed for now
    playInterval = setInterval(() => {
        if (currentStep < steps.length) {
            goNext();
        } else {
            stopPlay();
        }
    }, 3000);
}

function stopPlay() {
    isPlaying = false;
    clearInterval(playInterval);
    document.getElementById('play-btn').innerHTML = '<span class="material-symbols-outlined">play_arrow</span> Auto Play';
    document.getElementById('play-btn').classList.remove('active');
}

// ── FULL RESET ──
function resetSim() {
    stopPlay();
    currentStep = 0;

    showVictimState('v-lock');
    document.getElementById('uid-display').textContent = '_ _ _ _\u00a0\u00a0_ _ _ _\u00a0\u00a0_ _ _ _';

    // Hide all dynamic cards
    document.getElementById('otp-card').style.display = 'none';
    document.getElementById('zkp-card').style.display = 'none';
    document.getElementById('v-status-wrap').style.display = 'none';
    document.getElementById('v-action-btn').style.display = 'none';

    document.getElementById('sms-notif').style.transform = 'translateY(-150%)';

    // Reset ZKP visuals
    document.getElementById('zkp-ring').className = 'zkp-ring';
    document.getElementById('zkp-check').style.opacity = '0';
    document.getElementById('zkp-label').innerHTML = 'Signing with Secure Enclave...';

    fillOtpDigits(0);

    // Reset Gateway
    document.getElementById('gw-log').innerHTML = '<span class="gl gl-info"># Gateway Initialized v2.4.0</span>';
    gwStatus('IDLE', 'gw-neutral');
    gwIcon('🛡️');

    // Reset Laptop
    document.getElementById('laptop-term').innerHTML =
        '<span class="lt-line lt-dim"># SIM swap toolkit v3.1</span>' +
        '<span class="lt-line lt-prompt">root@kali:~# <span class="lt-cursor">_</span></span>';
    showRogueSMS(null);
    document.getElementById('rogue-feed').innerHTML =
        '<span class="rogue-feed-line dim">$ ss7_monitor --iface gsm0</span>' +
        '<span class="rogue-feed-line dim">Listening on GSM channels...</span>';

    // Reset Highlights
    ['bad-s1', 'bad-s2', 'bad-s3', 'bad-s4', 'good-s1', 'good-s2', 'good-s3', 'good-s4']
        .forEach(id => setStepHighlight(id, null));
    document.getElementById('result-bad').classList.remove('show');
    document.getElementById('result-good').classList.remove('show');

    updateNav();
}

// ── NAVIGATION ──
function updateNav() {
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const counter = document.getElementById('step-counter');
    const desc = document.getElementById('step-desc');
    const progressFill = document.getElementById('progress-fill');

    prevBtn.disabled = currentStep === 0;
    nextBtn.disabled = currentStep >= steps.length;

    const progress = (currentStep / steps.length) * 100;
    progressFill.style.width = `${progress}%`;

    if (currentStep === 0) {
        counter.textContent = `START`;
        desc.textContent = 'Scenario Ready: Click Next to Begin';
    } else {
        counter.textContent = `STEP ${currentStep} / ${steps.length}`;
        desc.textContent = steps[currentStep - 1].label;
    }
}

function goNext() {
    if (currentStep >= steps.length) return;
    steps[currentStep].apply();
    currentStep++;
    updateNav();
}

function goPrev() {
    if (currentStep <= 0) return;
    currentStep--;
    steps[currentStep].undo();
    updateNav();
}

function selectScenario(s) {
    currentScenario = s;
    document.getElementById('btn-a').classList.toggle('active', s === 'a');
    document.getElementById('btn-b').classList.toggle('active', s === 'b');

    const label = document.getElementById('scen-label');
    const badge = document.getElementById('sim-badge');

    if (s === 'a') {
        label.textContent = 'Current Aadhaar OTP authentication — attacker wins';
        badge.className = 'scenario-badge badge-a';
        badge.textContent = 'Scenario A — OTP System: Attacker Wins';
    } else {
        label.textContent = 'Proposed ZKP system — attacker blocked';
        badge.className = 'scenario-badge badge-b';
        badge.textContent = 'Scenario B — ZKP System: Attacker Blocked';
    }

    steps = s === 'a' ? buildStepsA() : buildStepsB();
    resetSim();
}

// ══ SCENARIO A: DETAILED STEPS ══
function buildStepsA() {
    return [
        {
            label: 'Attacker compromises the victim credentials',
            apply() {
                laptopLine('<span class="lt-info">[*] Leaked DB found: "Aadhaar_Dump_2024.sql"</span>');
                laptopLine('<span class="lt-ok">[+] Extracted UID: 7412 5896 3021</span>');
                laptopLine('<span class="lt-ok">[+] Extracted Phone: +91-9876543212</span>');
            },
            undo() { resetSim(); }
        },
        {
            label: 'Attacker initiates SS7/SIM Swap attack',
            apply() {
                laptopLine('<span class="lt-warn">[*] Initializing SS7 attack on carrier...</span>');
                laptopLine('<span class="lt-warn">[*] Sending MAP_UPDATE_LOCATION packet...</span>');
                document.getElementById('att-carrier').textContent = 'Searching...';
                rogueLog('Sending MAP_SEND_ROUTING_INFO...', 'warn');
                rogueLog('Target: +91-9876543212', 'dim');
            },
            undo() {
                const t = document.getElementById('laptop-term');
                t.removeChild(t.lastChild); t.removeChild(t.lastChild);
                document.getElementById('att-carrier').textContent = 'No Service';
            }
        },
        {
            label: 'Network fooled: Traffic redirected to rogue SIM',
            apply() {
                laptopLine('<span class="lt-ok">[+] HLR Update Successful!</span>');
                laptopLine('<span class="lt-ok">[+] Target number mapped to IMSI: 4042011... (Rogue SIM)</span>');
                document.getElementById('att-carrier').textContent = 'Jio 5G (Rogue)';
                rogueLog('HLR response: IMSI redirect OK', 'ok');
                rogueLog('Rogue SIM registered on network', 'ok');
                rogueLog('Monitoring +91-9876543212 traffic...', 'dim');
            },
            undo() {
                const t = document.getElementById('laptop-term');
                t.removeChild(t.lastChild); t.removeChild(t.lastChild);
                document.getElementById('att-carrier').textContent = 'Searching...';
            }
        },
        {
            label: 'Victim unlocks phone to access service',
            apply() {
                showVictimState('v-app');
                setStepHighlight('bad-s1', 'active');
            },
            undo() {
                showVictimState('v-lock');
                setStepHighlight('bad-s1', null);
            }
        },
        {
            label: 'Victim enters Aadhaar Number in App',
            apply() {
                document.getElementById('uid-display').textContent = '7412  5896  3021';
                gwStatus('Processing Request...', 'gw-wait');
                gwLog('Incoming Auth Request: UID 7412-xxx-3021');
            },
            undo() {
                document.getElementById('uid-display').textContent = '_ _ _ _  _ _ _ _  _ _ _ _';
                gwStatus('IDLE', 'gw-neutral');
            }
        },
        {
            label: 'Gateway sends OTP via SMS',
            apply() {
                setStepHighlight('bad-s1', 'done');
                setStepHighlight('bad-s2', 'active');
                gwLog('Authentication Policy: OTP (Legacy)');
                gwLog('Generating 6-digit OTP...');
                gwLog('<span class="lt-info">>> SMS Dispatched to +91-98xxxxxx12</span>');
                gwStatus('OTP SENT', 'gw-wait');
                gwIcon('📨');
                // Show SMS banner on victim phone first
                document.getElementById('sms-notif').style.transform = 'translateY(0)';
                // After victim reads SMS, OTP card slides in
                setTimeout(() => {
                    document.getElementById('otp-card').style.display = 'block';
                    // Auto-dismiss the notification banner
                    setTimeout(() => {
                        document.getElementById('sms-notif').style.transform = 'translateY(-150%)';
                    }, 2000);
                }, 1500);
            },
            undo() {
                setStepHighlight('bad-s1', 'active');
                setStepHighlight('bad-s2', null);
                document.getElementById('otp-card').style.display = 'none';
                document.getElementById('sms-notif').style.transform = 'translateY(-150%)';
                gwStatus('Processing Request...', 'gw-wait');
            }
        },
        {
            label: 'Network routes SMS to Attacker (SIM Swap)',
            apply() {
                setStepHighlight('bad-s2', 'done');
                setStepHighlight('bad-s3', 'active');
                laptopLine('<span class="lt-warn">[!] Incoming SMS on GSM Channel 3...</span>');
                laptopLine('<span class="lt-ok">[+] SMS DECODED: "Your Aadhaar OTP is 847291"</span>');
                rogueLog('── INCOMING SMS ──', 'warn');
                rogueLog('From: UIDAI-OTP', 'dim');
                rogueLog('Msg: OTP is 847291', 'ok');
                showRogueSMS('OTP: 847291');
            },
            undo() {
                setStepHighlight('bad-s2', 'active');
                setStepHighlight('bad-s3', null);
                showRogueSMS(null);
                const t = document.getElementById('laptop-term');
                t.removeChild(t.lastChild); t.removeChild(t.lastChild);
            }
        },
        {
            label: 'Attacker inputs stolen OTP',
            apply() {
                // Simulate typing
                fillOtpDigits(6);
                laptopLine('<span class="lt-info">[*] Auto-submitting OTP to Gateway...</span>');
                gwLog('Received OTP: 847291');
            },
            undo() {
                fillOtpDigits(0);
                const t = document.getElementById('laptop-term');
                t.removeChild(t.lastChild);
            }
        },
        {
            label: 'Gateway validates OTP (Cannot detect swap)',
            apply() {
                setStepHighlight('bad-s3', 'done');
                setStepHighlight('bad-s4', 'active');
                gwLog('<span class="lt-ok">OTP MATCH CONFIRMED</span>');
                gwStatus('ACCESS GRANTED', 'gw-ok');
                gwIcon('✅');
            },
            undo() {
                setStepHighlight('bad-s3', 'active');
                setStepHighlight('bad-s4', null);
                gwStatus('OTP SENT', 'gw-wait');
                gwIcon('📨');
            }
        },
        {
            label: '🔓 BREACH SUCCESSFUL: Attacker logged in',
            apply() {
                setStepHighlight('bad-s4', 'done');
                document.getElementById('v-status-wrap').style.display = 'block';
                document.getElementById('v-action-btn').style.display = 'block';
                document.getElementById('result-bad').classList.add('show');
                laptopLine('<span class="lt-ok">[SUCCESS] Auth Token Received! Dumping user data...</span>');
            },
            undo() {
                setStepHighlight('bad-s4', 'active');
                document.getElementById('v-status-wrap').style.display = 'none';
                document.getElementById('v-action-btn').style.display = 'none';
                document.getElementById('result-bad').classList.remove('show');
                const t = document.getElementById('laptop-term');
                t.removeChild(t.lastChild);
            }
        }
    ];
}

// ══ SCENARIO B: DETAILED STEPS ══
function buildStepsB() {
    return [
        {
            label: 'Attacker performs steps 1-3 (Leak, SS7 Attack)',
            apply() {
                laptopLine('<span class="lt-info">[*] Leaked DB found: "Aadhaar_Dump_2024.sql"</span>');
                laptopLine('<span class="lt-warn">[*] Initializing SS7 attack...</span>');
                laptopLine('<span class="lt-ok">[+] SIM swap confirmed — Rogue SIM active</span>');
                document.getElementById('att-carrier').textContent = 'Jio 5G (Rogue)';
            },
            undo() { resetSim(); }
        },
        {
            label: 'Victim unlocks phone & opens app',
            apply() {
                showVictimState('v-app');
                setStepHighlight('good-s1', 'active');
            },
            undo() {
                showVictimState('v-lock');
                setStepHighlight('good-s1', null);
            }
        },
        {
            label: 'Victim submits Aadhaar Number',
            apply() {
                document.getElementById('uid-display').textContent = '7412  5896  3021';
                gwStatus('Processing Request', 'gw-wait');
                gwLog('Incoming Auth Request: UID 7412-xxx-3021');
            },
            undo() {
                document.getElementById('uid-display').textContent = '_ _ _ _  _ _ _ _  _ _ _ _';
                gwStatus('IDLE', 'gw-neutral');
            }
        },
        {
            label: 'Gateway issues ZKP Challenge (NO SMS)',
            apply() {
                setStepHighlight('good-s1', 'done');
                setStepHighlight('good-s2', 'active');
                gwLog('Policy: ZKP-Enhaced (Draft 2026)');
                gwLog('<span class="lt-info">Generating Cryptographic Nonce (32-byte)</span>');
                gwLog('>> Sending Challenge to Device (HTTPS)');
                gwStatus('ZKP PENDING', 'gw-wait');
                gwIcon('🔐');
                document.getElementById('zkp-card').style.display = 'block';
            },
            undo() {
                setStepHighlight('good-s1', 'active');
                setStepHighlight('good-s2', null);
                document.getElementById('zkp-card').style.display = 'none';
                gwStatus('Processing Request', 'gw-wait');
            }
        },
        {
            label: 'Attacker waits for SMS... (Silence)',
            apply() {
                setStepHighlight('good-s2', 'done');
                laptopLine('<span class="lt-warn">[!] Monitoring GSM channels for SMS...</span>');
                laptopLine('...');
                laptopLine('<span class="lt-err">[-] 10s Timeout: No SMS detected</span>');
            },
            undo() {
                setStepHighlight('good-s2', 'active');
                const t = document.getElementById('laptop-term');
                t.removeChild(t.lastChild); t.removeChild(t.lastChild); t.removeChild(t.lastChild);
            }
        },
        {
            label: 'Victim Device Signs Challenge (Secure Enclave)',
            apply() {
                document.getElementById('zkp-label').innerHTML = 'Deriving private key from hardware...';
                setTimeout(() => {
                    if (currentStep > 5) document.getElementById('zkp-ring').classList.add('done'); // Hack to prevent async glitch
                }, 500);
            },
            undo() {
                document.getElementById('zkp-label').innerHTML = 'Signing with Secure Enclave...';
                document.getElementById('zkp-ring').classList.remove('done');
            }
        },
        {
            label: 'Signature Generation Complete',
            apply() {
                setStepHighlight('good-s3', 'active');
                document.getElementById('zkp-ring').classList.add('done');
                document.getElementById('zkp-check').style.opacity = '1';
                document.getElementById('zkp-label').innerHTML = 'Signed Successfully<br><span style="color:#27ae60;font-weight:700">ECDSA P-256 ✓</span>';
                gwLog('Receiving Signed Response...');
            },
            undo() {
                setStepHighlight('good-s3', null);
                document.getElementById('zkp-check').style.opacity = '0';
            }
        },
        {
            label: 'Attacker attempts brute-force (Impossible)',
            apply() {
                laptopLine('<span class="lt-info">[*] Attempting replay attack...</span>');
                laptopLine('<span class="lt-err">[-] FAILED: Challenge is unique per session</span>');
                laptopLine('<span class="lt-info">[*] Attempting key derivation...</span>');
                laptopLine('<span class="lt-err">[-] FAILED: Private key not in SIM</span>');
            },
            undo() {
                const t = document.getElementById('laptop-term');
                for (let i = 0; i < 4; i++) t.removeChild(t.lastChild);
            }
        },
        {
            label: 'Gateway Verifies Geometric Proof',
            apply() {
                gwLog('Verifying Signature against Public Key...');
                gwLog('<span class="lt-ok">MATH CHECK: VALID</span>');
                gwLog('Checking ML Risk Score...');
                gwLog('Risk Score: 0.05 (Low)');
            },
            undo() {
                const l = document.getElementById('gw-log');
                for (let i = 0; i < 4; i++) l.removeChild(l.lastChild);
            }
        },
        {
            label: '🔓 Victim Authenticated (Attacker Blocked)',
            apply() {
                setStepHighlight('good-s3', 'done');
                setStepHighlight('good-s4', 'active');

                gwStatus('VICTIM VERIFIED', 'gw-ok');
                gwIcon('✅');

                document.getElementById('v-status-wrap').style.display = 'block';
                document.getElementById('v-action-btn').style.display = 'block';
                document.getElementById('result-good').classList.add('show');

                laptopLine('<span class="lt-err">[FATAL] Auth Failed. Server rejected request.</span>');
            },
            undo() {
                setStepHighlight('good-s3', 'active');
                setStepHighlight('good-s4', null);
                gwStatus('ZKP PENDING', 'gw-wait');
                gwIcon('🔐');
                document.getElementById('v-status-wrap').style.display = 'none';
                document.getElementById('v-action-btn').style.display = 'none';
                document.getElementById('result-good').classList.remove('show');
                const t = document.getElementById('laptop-term');
                t.removeChild(t.lastChild);
            }
        }
    ];
}

// ── INIT ──
steps = buildStepsA();
updateNav();

// ── KEYBOARD SHORTCUTS ──
document.addEventListener('keydown', (e) => {
    // Ignore if typing in an input/textarea
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    switch (e.key.toLowerCase()) {
        case 'd':
        case 'arrowright':
            goNext(); break;
        case 'a':
        case 'arrowleft':
            goPrev(); break;
        case ' ':
            e.preventDefault();
            togglePlay(); break;
    }
});
