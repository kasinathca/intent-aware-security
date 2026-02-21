// ── UTILITIES ──
let currentScenario = 'a';
let currentStep = 0;
let steps = [];

// Live clock
function updateClocks() {
    const now = new Date();
    const t = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false });
    const el1 = document.getElementById('victim-time');
    const el2 = document.getElementById('lock-time');
    if (el1) el1.textContent = t;
    if (el2) el2.textContent = t;
}
updateClocks();
setInterval(updateClocks, 30000);

// ── DOM HELPERS ──
function showVictimState(id) {
    document.querySelectorAll('.screen-state').forEach(e => e.classList.remove('visible'));
    const el = document.getElementById(id);
    if (el) el.classList.add('visible');
}

function showRogueState(id) {
    document.querySelectorAll('.rogue-state').forEach(e => e.classList.remove('visible'));
    const el = document.getElementById(id);
    if (el) el.classList.add('visible');
}

function gwLog(html) {
    const log = document.getElementById('gw-log');
    log.innerHTML += `<span class="gl">${html}</span>`;
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

function attScreen(html) {
    showRogueState('att-active');
    document.getElementById('att-screen-text').innerHTML = html.replace(/\n/g, '<br>');
}

function setStepHighlight(id, state) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.remove('active', 'done');
    if (state) el.classList.add(state);
}

function fillOtpDigits(count) {
    const otp = '847291';
    document.querySelectorAll('#otp-digits .otp-d').forEach((d, i) => {
        d.classList.remove('filled', 'active-cursor');
        if (i < count) {
            d.textContent = otp[i];
            d.classList.add('filled');
        } else {
            d.textContent = '';
        }
    });
}

// ── FULL RESET ──
function resetSim() {
    currentStep = 0;
    showVictimState('v-lock');
    document.getElementById('uid-display').textContent = '_ _ _ _\u00a0\u00a0_ _ _ _\u00a0\u00a0_ _ _ _';
    document.getElementById('otp-card').style.display = 'none';
    document.getElementById('zkp-card').style.display = 'none';
    document.getElementById('v-status-wrap').style.display = 'none';
    document.getElementById('v-action-btn').style.display = 'none';
    document.getElementById('sms-notif').classList.remove('slide-in');
    document.getElementById('zkp-ring').className = 'zkp-ring';
    document.getElementById('zkp-check').className = 'zkp-check';
    document.getElementById('zkp-label').innerHTML = 'Signing with device key\u2026<br><span style="font-size:.55rem;color:#aaa;">ECDSA P-256</span>';
    fillOtpDigits(0);
    document.getElementById('gw-log').innerHTML = '<span class="gl gl-info"># Gateway ready</span>';
    gwStatus('Waiting...', 'gw-neutral');
    gwIcon('\u23f3');
    document.getElementById('laptop-term').innerHTML =
        '<span class="lt-line lt-dim"># SIM swap toolkit v3.1</span>' +
        '<span class="lt-line lt-prompt">root@kali:~# <span style="color:#c9d1d9;">_</span></span>';
    document.getElementById('att-sms').classList.remove('slide-in');
    showRogueState('att-idle');
    document.getElementById('att-screen-text').textContent = '';
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

    prevBtn.disabled = currentStep === 0;
    nextBtn.disabled = currentStep >= steps.length;
    nextBtn.textContent = currentStep >= steps.length ? '\u2713 Done' : 'Next \u203a';

    if (currentStep === 0) {
        counter.textContent = `Step 0 / ${steps.length}`;
        desc.textContent = 'Press Next to begin the simulation';
    } else {
        counter.textContent = `Step ${currentStep} / ${steps.length}`;
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
    document.getElementById('scen-label').textContent = s === 'a'
        ? 'Current Aadhaar OTP authentication \u2014 attacker wins'
        : 'Proposed ZKP system \u2014 attacker blocked';
    const badge = document.getElementById('sim-badge');
    badge.className = 'scenario-badge ' + (s === 'a' ? 'badge-a' : 'badge-b');
    badge.textContent = s === 'a'
        ? 'Scenario A \u2014 OTP System: Attacker Wins'
        : 'Scenario B \u2014 ZKP System: Attacker Blocked';
    steps = s === 'a' ? buildStepsA() : buildStepsB();
    resetSim();
}

// ══ SCENARIO A STEPS ══
function buildStepsA() {
    return [
        {
            label: 'Attacker initiates SS7 redirect attack',
            apply() {
                laptopLine('<span class="lt-info">[*] Initiating SS7 redirect attack...</span>');
                laptopLine('<span class="lt-warn">[*] Target: +91-98XXXXXX12 (Jio)</span>');
            },
            undo() {
                document.getElementById('laptop-term').innerHTML =
                    '<span class="lt-line lt-dim"># SIM swap toolkit v3.1</span>' +
                    '<span class="lt-line lt-prompt">root@kali:~# <span style="color:#c9d1d9;">_</span></span>';
            }
        },
        {
            label: 'SIM swap confirmed — attacker\'s Airtel SIM now receives victim\'s calls & SMS',
            apply() {
                laptopLine('<span class="lt-ok">[+] SIM swap confirmed \u2014 Airtel rogue SIM active</span>');
                attScreen('SIM SWAP ACTIVE\n\nTarget routed to\nrogue Airtel SIM\n\nAwaiting OTP...');
            },
            undo() {
                showRogueState('att-idle');
                const t = document.getElementById('laptop-term');
                t.removeChild(t.lastChild);
            }
        },
        {
            label: 'Victim opens mAadhaar app and enters Aadhaar number',
            apply() {
                showVictimState('v-app');
                setStepHighlight('bad-s1', 'active');
                document.getElementById('uid-display').textContent = '7412  5896  3021';
            },
            undo() {
                showVictimState('v-lock');
                setStepHighlight('bad-s1', null);
                document.getElementById('uid-display').textContent = '_ _ _ _\u00a0\u00a0_ _ _ _\u00a0\u00a0_ _ _ _';
            }
        },
        {
            label: 'Server sends OTP via SMS to registered mobile number',
            apply() {
                setStepHighlight('bad-s1', 'done');
                setStepHighlight('bad-s2', 'active');
                gwLog('<span class="gl-info">[22:07:15] UID: 7412-5896-3021</span>');
                gwLog('<span class="gl-info">[22:07:15] OTP dispatched via SMS</span>');
                gwStatus('OTP Sent', 'gw-wait');
                gwIcon('\ud83d\udce8');
                document.getElementById('otp-card').style.display = 'block';
            },
            undo() {
                setStepHighlight('bad-s1', 'active');
                setStepHighlight('bad-s2', null);
                document.getElementById('otp-card').style.display = 'none';
                document.getElementById('gw-log').innerHTML = '<span class="gl gl-info"># Gateway ready</span>';
                gwStatus('Waiting...', 'gw-neutral');
                gwIcon('\u23f3');
            }
        },
        {
            label: 'Attacker\'s rogue SIM intercepts the OTP — victim never sees it',
            apply() {
                setStepHighlight('bad-s2', 'done');
                setStepHighlight('bad-s3', 'active');
                laptopLine('<span class="lt-ok">[+] SMS intercepted from UIDAI!</span>');
                laptopLine('<span class="lt-ok">[+] OTP extracted: 847291</span>');
                document.getElementById('att-sms').classList.add('slide-in');
                attScreen('OTP CAPTURED!\n\nFrom: UIDAI-OTP\nCode: 847291\nValid: 10 min\n\nAuto-submitting...');
            },
            undo() {
                setStepHighlight('bad-s2', 'active');
                setStepHighlight('bad-s3', null);
                document.getElementById('att-sms').classList.remove('slide-in');
                attScreen('SIM SWAP ACTIVE\n\nTarget routed to\nrogue Airtel SIM\n\nAwaiting OTP...');
                const t = document.getElementById('laptop-term');
                t.removeChild(t.lastChild);
                t.removeChild(t.lastChild);
            }
        },
        {
            label: 'OTP also arrives on victim\'s phone (but attacker already has it)',
            apply() {
                document.getElementById('sms-notif').classList.add('slide-in');
            },
            undo() {
                document.getElementById('sms-notif').classList.remove('slide-in');
            }
        },
        {
            label: 'Attacker submits OTP — server has no way to distinguish attacker from victim',
            apply() {
                setStepHighlight('bad-s3', 'done');
                setStepHighlight('bad-s4', 'active');
                fillOtpDigits(6);
                gwLog('<span class="gl-ok">[22:07:17] OTP VALID \u2713</span>');
                gwLog('<span class="gl-warn">[22:07:17] No anomaly detected</span>');
                gwStatus('OTP Valid \u2713', 'gw-ok');
                gwIcon('\u2705');
            },
            undo() {
                setStepHighlight('bad-s3', 'active');
                setStepHighlight('bad-s4', null);
                fillOtpDigits(0);
                const log = document.getElementById('gw-log');
                log.removeChild(log.lastChild);
                log.removeChild(log.lastChild);
                gwStatus('OTP Sent', 'gw-wait');
                gwIcon('\ud83d\udce8');
            }
        },
        {
            label: '🔓 ATTACKER AUTHENTICATED — Full access to victim\'s Aadhaar profile',
            apply() {
                setStepHighlight('bad-s4', 'done');
                const pill = document.getElementById('v-status-pill');
                pill.className = 'status-pill pill-ok';
                pill.textContent = '\u2713 Authenticated';
                document.getElementById('v-status-wrap').style.display = 'block';
                const btn = document.getElementById('v-action-btn');
                btn.className = 'app-action-btn btn-green';
                btn.textContent = 'Access Granted \u2014 View Aadhaar';
                btn.style.display = 'block';
                document.getElementById('result-bad').classList.add('show');
            },
            undo() {
                setStepHighlight('bad-s4', 'active');
                document.getElementById('v-status-wrap').style.display = 'none';
                document.getElementById('v-action-btn').style.display = 'none';
                document.getElementById('result-bad').classList.remove('show');
            }
        }
    ];
}

// ══ SCENARIO B STEPS ══
function buildStepsB() {
    return [
        {
            label: 'Attacker initiates SS7 redirect attack (same as before)',
            apply() {
                laptopLine('<span class="lt-info">[*] Initiating SS7 redirect attack...</span>');
                laptopLine('<span class="lt-warn">[*] Target: +91-98XXXXXX12 (Jio)</span>');
            },
            undo() {
                document.getElementById('laptop-term').innerHTML =
                    '<span class="lt-line lt-dim"># SIM swap toolkit v3.1</span>' +
                    '<span class="lt-line lt-prompt">root@kali:~# <span style="color:#c9d1d9;">_</span></span>';
            }
        },
        {
            label: 'SIM swap confirmed — attacker is ready to intercept SMS',
            apply() {
                laptopLine('<span class="lt-ok">[+] SIM swap confirmed \u2014 Airtel rogue SIM active</span>');
                attScreen('SIM SWAP ACTIVE\n\nTarget routed to\nrogue Airtel SIM\n\nAwaiting OTP...');
            },
            undo() {
                showRogueState('att-idle');
                const t = document.getElementById('laptop-term');
                t.removeChild(t.lastChild);
            }
        },
        {
            label: 'Victim opens mAadhaar app and enters Aadhaar number',
            apply() {
                showVictimState('v-app');
                setStepHighlight('good-s1', 'active');
                document.getElementById('uid-display').textContent = '7412  5896  3021';
            },
            undo() {
                showVictimState('v-lock');
                setStepHighlight('good-s1', null);
                document.getElementById('uid-display').textContent = '_ _ _ _\u00a0\u00a0_ _ _ _\u00a0\u00a0_ _ _ _';
            }
        },
        {
            label: 'Server issues a ZKP challenge nonce — NO SMS sent, no OTP channel',
            apply() {
                setStepHighlight('good-s1', 'done');
                setStepHighlight('good-s2', 'active');
                gwLog('<span class="gl-info">[22:07:15] UID: 7412-5896-3021</span>');
                gwLog('<span class="gl-info">[22:07:15] ZKP challenge: a3f9...e72b</span>');
                gwStatus('Challenge Issued', 'gw-wait');
                gwIcon('\ud83d\udd10');
                document.getElementById('zkp-card').style.display = 'block';
            },
            undo() {
                setStepHighlight('good-s1', 'active');
                setStepHighlight('good-s2', null);
                document.getElementById('zkp-card').style.display = 'none';
                document.getElementById('gw-log').innerHTML = '<span class="gl gl-info"># Gateway ready</span>';
                gwStatus('Waiting...', 'gw-neutral');
                gwIcon('\u23f3');
            }
        },
        {
            label: 'Attacker waits — no SMS arrives. The system uses cryptographic challenge-response, not OTP',
            apply() {
                setStepHighlight('good-s2', 'done');
                laptopLine('<span class="lt-warn">[!] Waiting for OTP intercept...</span>');
                laptopLine('<span class="lt-err">[-] No SMS received. System uses ZKP \u2014 no OTP sent!</span>');
                attScreen('ERROR: No OTP\n\nSystem uses crypto\nchallenge-response.\nNo SMS channel.\n\nAttempting signature\nforgery...');
            },
            undo() {
                setStepHighlight('good-s2', 'active');
                attScreen('SIM SWAP ACTIVE\n\nTarget routed to\nrogue Airtel SIM\n\nAwaiting OTP...');
                const t = document.getElementById('laptop-term');
                t.removeChild(t.lastChild);
                t.removeChild(t.lastChild);
            }
        },
        {
            label: 'Victim\'s browser signs the challenge with their private key (ECDSA P-256)',
            apply() {
                setStepHighlight('good-s3', 'active');
                gwLog('<span class="gl-info">[22:07:16] Signature received from client</span>');
                document.getElementById('zkp-ring').className = 'zkp-ring done';
                document.getElementById('zkp-check').className = 'zkp-check show';
                document.getElementById('zkp-label').innerHTML = 'Signed successfully<br><span style="font-size:.55rem;color:#27ae60;">ECDSA P-256 \u2713</span>';
            },
            undo() {
                setStepHighlight('good-s3', null);
                const log = document.getElementById('gw-log');
                log.removeChild(log.lastChild);
                document.getElementById('zkp-ring').className = 'zkp-ring';
                document.getElementById('zkp-check').className = 'zkp-check';
                document.getElementById('zkp-label').innerHTML = 'Signing with device key\u2026<br><span style="font-size:.55rem;color:#aaa;">ECDSA P-256</span>';
            }
        },
        {
            label: 'Attacker tries to forge the ECDSA signature — computationally infeasible (2²⁵⁶ key space)',
            apply() {
                laptopLine('<span class="lt-warn">[*] Brute-forcing ECDSA P-256...</span>');
                laptopLine('<span class="lt-err">[-] Infeasible \u2014 2\u00b2\u2075\u2076 key space</span>');
                laptopLine('<span class="lt-err">[-] Forged signature REJECTED by server</span>');
                attScreen('BLOCKED\n\nSignature forgery\nFAILED.\n\nECDSA P-256 is\ncomputationally\ninfeasible to break.\n\nSIM swap: irrelevant.\nNo private key.');
            },
            undo() {
                attScreen('ERROR: No OTP\n\nSystem uses crypto\nchallenge-response.\nNo SMS channel.\n\nAttempting signature\nforgery...');
                const t = document.getElementById('laptop-term');
                t.removeChild(t.lastChild);
                t.removeChild(t.lastChild);
                t.removeChild(t.lastChild);
            }
        },
        {
            label: '🔒 ATTACKER BLOCKED — Victim authenticated, attacker gets HTTP 403 Forbidden',
            apply() {
                setStepHighlight('good-s3', 'done');
                setStepHighlight('good-s4', 'active');
                gwLog('<span class="gl-ok">[22:07:17] Victim sig: VALID \u2713</span>');
                gwLog('<span class="gl-err">[22:07:17] Attacker sig: INVALID \u2717</span>');
                gwLog('<span class="gl-err">[22:07:17] HTTP 403 FORBIDDEN</span>');
                gwStatus('Attacker Blocked \u2717', 'gw-err');
                gwIcon('\ud83d\udeab');
                setStepHighlight('good-s4', 'done');
                const pill = document.getElementById('v-status-pill');
                pill.className = 'status-pill pill-ok';
                pill.textContent = '\u2713 Authenticated';
                document.getElementById('v-status-wrap').style.display = 'block';
                const btn = document.getElementById('v-action-btn');
                btn.className = 'app-action-btn btn-green';
                btn.textContent = 'Access Granted \u2014 View Aadhaar';
                btn.style.display = 'block';
                document.getElementById('result-good').classList.add('show');
            },
            undo() {
                setStepHighlight('good-s3', 'active');
                setStepHighlight('good-s4', null);
                const log = document.getElementById('gw-log');
                log.removeChild(log.lastChild);
                log.removeChild(log.lastChild);
                log.removeChild(log.lastChild);
                gwStatus('Challenge Issued', 'gw-wait');
                gwIcon('\ud83d\udd10');
                document.getElementById('v-status-wrap').style.display = 'none';
                document.getElementById('v-action-btn').style.display = 'none';
                document.getElementById('result-good').classList.remove('show');
            }
        }
    ];
}

// ── INIT ──
steps = buildStepsA();
updateNav();
