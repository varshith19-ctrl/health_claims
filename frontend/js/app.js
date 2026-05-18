/* ================================================================
   ClaimShield AI — Main Application Logic
   ================================================================ */

const API_BASE = window.location.origin + '/api';
let currentUser = null;
let testimonialInterval = null;
let threeScene = null;

/* ================================================================
   AUTH
   ================================================================ */
function showRegister() {
    document.getElementById('login-card').style.display = 'none';
    const rc = document.getElementById('register-card');
    rc.style.display = 'block';
    rc.style.animation = 'cardSlideUp 0.4s ease';
    clearErrors();
}

function showLogin() {
    document.getElementById('register-card').style.display = 'none';
    const lc = document.getElementById('login-card');
    lc.style.display = 'block';
    lc.style.animation = 'cardSlideUp 0.4s ease';
    clearErrors();
}

function clearErrors() {
    ['login-error', 'register-error', 'register-success', 'claim-error'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    });
}

function showError(id, msg) {
    const el = document.getElementById(id);
    el.textContent = msg;
    el.style.display = 'block';
}

function setLoading(btnId, loading) {
    const btn = document.getElementById(btnId);
    const text = btn.querySelector('.btn-text');
    const loader = btn.querySelector('.btn-loader');
    if (loading) {
        text.style.display = 'none';
        loader.style.display = 'inline-block';
        btn.disabled = true;
    } else {
        text.style.display = 'inline';
        loader.style.display = 'none';
        btn.disabled = false;
    }
}

async function handleLogin(e) {
    e.preventDefault();
    clearErrors();
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    if (!username || !password) { showError('login-error', 'Please fill in all fields'); return false; }

    setLoading('btn-login', true);
    try {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (res.ok) {
            currentUser = data.username;
            localStorage.setItem('cs_user', currentUser);
            localStorage.setItem('cs_token', data.token);
            showHomePage();
        } else {
            showError('login-error', data.detail || 'Invalid credentials');
        }
    } catch (err) {
        showError('login-error', 'Cannot connect to server');
    }
    setLoading('btn-login', false);
    return false;
}

async function handleRegister(e) {
    e.preventDefault();
    clearErrors();
    const username = document.getElementById('reg-username').value.trim();
    const password = document.getElementById('reg-password').value;
    const confirm = document.getElementById('reg-password-confirm').value;
    if (!username || !password) { showError('register-error', 'Please fill in all fields'); return false; }
    if (password !== confirm) { showError('register-error', 'Passwords do not match'); return false; }
    if (password.length < 4) { showError('register-error', 'Password must be at least 4 characters'); return false; }

    setLoading('btn-register', true);
    try {
        const res = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (res.ok) {
            const s = document.getElementById('register-success');
            s.textContent = 'Account created! Redirecting to login...';
            s.style.display = 'block';
            setTimeout(() => showLogin(), 1500);
        } else {
            showError('register-error', data.detail || 'Registration failed');
        }
    } catch (err) {
        showError('register-error', 'Cannot connect to server');
    }
    setLoading('btn-register', false);
    return false;
}

function handleLogout() {
    currentUser = null;
    localStorage.removeItem('cs_user');
    localStorage.removeItem('cs_token');
    switchPage('page-auth');
    if (testimonialInterval) clearInterval(testimonialInterval);
}

/* ================================================================
   PAGE NAVIGATION
   ================================================================ */
function switchPage(pageId) {
    document.querySelectorAll('.page').forEach(p => {
        p.classList.remove('active');
        p.style.display = 'none';
    });
    const page = document.getElementById(pageId);
    page.style.display = 'block';
    requestAnimationFrame(() => page.classList.add('active'));
}

function showHomePage() {
    switchPage('page-home');
    document.getElementById('nav-username').textContent = currentUser || '';
    startTestimonialCarousel();
    animateStats();
}

function showClaimPage() {
    switchPage('page-claim');
    document.getElementById('nav-username-claim').textContent = currentUser || '';
    resetClaimForm();
    initThreeJS();
}

/* ================================================================
   TESTIMONIAL CAROUSEL
   ================================================================ */
let currentSlide = 0;
const totalSlides = 4;

function startTestimonialCarousel() {
    const dotsContainer = document.getElementById('carousel-dots');
    dotsContainer.innerHTML = '';
    for (let i = 0; i < totalSlides; i++) {
        const dot = document.createElement('button');
        dot.className = 'carousel-dot' + (i === 0 ? ' active' : '');
        dot.onclick = () => goToSlide(i);
        dotsContainer.appendChild(dot);
    }
    currentSlide = 0;
    updateCarousel();
    if (testimonialInterval) clearInterval(testimonialInterval);
    testimonialInterval = setInterval(() => {
        currentSlide = (currentSlide + 1) % totalSlides;
        updateCarousel();
    }, 3000);
}

function goToSlide(i) {
    currentSlide = i;
    updateCarousel();
    if (testimonialInterval) clearInterval(testimonialInterval);
    testimonialInterval = setInterval(() => {
        currentSlide = (currentSlide + 1) % totalSlides;
        updateCarousel();
    }, 3000);
}

function updateCarousel() {
    const track = document.getElementById('testimonial-track');
    if (track) track.style.transform = `translateX(-${currentSlide * 100}%)`;
    document.querySelectorAll('.carousel-dot').forEach((dot, i) => {
        dot.classList.toggle('active', i === currentSlide);
    });
}

/* ================================================================
   STAT COUNTER ANIMATION
   ================================================================ */
function animateStats() {
    document.querySelectorAll('.stat-number').forEach(el => {
        const target = parseFloat(el.dataset.target);
        const isDecimal = target % 1 !== 0;
        let current = 0;
        const step = target / 60;
        const timer = setInterval(() => {
            current += step;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            el.textContent = isDecimal ? current.toFixed(1) : Math.round(current);
        }, 25);
    });
}

/* ================================================================
   THREE.JS 3D HEALTHCARE ANIMATION
   ================================================================ */
function initThreeJS() {
    const canvas = document.getElementById('three-canvas');
    if (!canvas || typeof THREE === 'undefined') return;

    const parent = canvas.parentElement;
    const w = parent.clientWidth;
    const h = parent.clientHeight;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf8f9fc);

    const camera = new THREE.PerspectiveCamera(50, w / h, 0.1, 1000);
    camera.position.set(0, 2, 8);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // Lighting
    const ambient = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambient);
    const directional = new THREE.DirectionalLight(0xffffff, 0.8);
    directional.position.set(5, 10, 5);
    scene.add(directional);

    const objects = [];

    // Healthcare cross
    const crossMat = new THREE.MeshPhongMaterial({ color: 0x4A90D9, shininess: 100 });
    const crossH = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.6, 0.6), crossMat);
    const crossV = new THREE.Mesh(new THREE.BoxGeometry(0.6, 2.4, 0.6), crossMat);
    const crossGroup = new THREE.Group();
    crossGroup.add(crossH);
    crossGroup.add(crossV);
    crossGroup.position.set(0, 0.5, 0);
    scene.add(crossGroup);
    objects.push({ mesh: crossGroup, type: 'cross' });

    // Floating spheres (pills/molecules)
    const colors = [0x5ABE8A, 0xF2A7B3, 0xFF9F43, 0x87CEEB];
    for (let i = 0; i < 8; i++) {
        const radius = 0.15 + Math.random() * 0.25;
        const sphere = new THREE.Mesh(
            new THREE.SphereGeometry(radius, 24, 24),
            new THREE.MeshPhongMaterial({ color: colors[i % colors.length], shininess: 80, transparent: true, opacity: 0.8 })
        );
        sphere.position.set(
            (Math.random() - 0.5) * 6,
            (Math.random() - 0.5) * 4,
            (Math.random() - 0.5) * 4
        );
        scene.add(sphere);
        objects.push({ mesh: sphere, type: 'sphere', speed: 0.3 + Math.random() * 0.5, phase: Math.random() * Math.PI * 2 });
    }

    // Heart shape
    const heartShape = new THREE.Shape();
    const x = 0, y = 0;
    heartShape.moveTo(x, y + 0.5);
    heartShape.bezierCurveTo(x, y + 0.5, x - 0.5, y, x - 0.5, y);
    heartShape.bezierCurveTo(x - 0.5, y - 0.35, x, y - 0.6, x, y - 0.8);
    heartShape.bezierCurveTo(x, y - 0.6, x + 0.5, y - 0.35, x + 0.5, y);
    heartShape.bezierCurveTo(x + 0.5, y, x, y + 0.5, x, y + 0.5);
    const heartGeo = new THREE.ExtrudeGeometry(heartShape, { depth: 0.2, bevelEnabled: true, bevelThickness: 0.05, bevelSize: 0.05, bevelSegments: 3 });
    const heartMesh = new THREE.Mesh(heartGeo, new THREE.MeshPhongMaterial({ color: 0xFF6B6B, shininess: 100 }));
    heartMesh.scale.set(1.2, 1.2, 1.2);
    heartMesh.position.set(-2.5, 1.5, -1);
    scene.add(heartMesh);
    objects.push({ mesh: heartMesh, type: 'heart' });

    // DNA helix
    const helixGroup = new THREE.Group();
    const helixMat1 = new THREE.MeshPhongMaterial({ color: 0x5ABE8A });
    const helixMat2 = new THREE.MeshPhongMaterial({ color: 0x4A90D9 });
    for (let i = 0; i < 30; i++) {
        const t = i * 0.3;
        const s1 = new THREE.Mesh(new THREE.SphereGeometry(0.08, 12, 12), helixMat1);
        s1.position.set(Math.cos(t) * 0.5, t * 0.15 - 2, Math.sin(t) * 0.5);
        helixGroup.add(s1);
        const s2 = new THREE.Mesh(new THREE.SphereGeometry(0.08, 12, 12), helixMat2);
        s2.position.set(Math.cos(t + Math.PI) * 0.5, t * 0.15 - 2, Math.sin(t + Math.PI) * 0.5);
        helixGroup.add(s2);
    }
    helixGroup.position.set(3, 0.5, -1);
    scene.add(helixGroup);
    objects.push({ mesh: helixGroup, type: 'helix' });

    threeScene = { renderer, scene, camera, objects };

    function animate() {
        if (!threeScene) return;
        const t = Date.now() * 0.001;

        objects.forEach(obj => {
            if (obj.type === 'cross') {
                obj.mesh.rotation.y = Math.sin(t * 0.5) * 0.3;
                obj.mesh.position.y = 0.5 + Math.sin(t * 0.8) * 0.2;
            } else if (obj.type === 'sphere') {
                obj.mesh.position.y += Math.sin(t * obj.speed + obj.phase) * 0.003;
                obj.mesh.position.x += Math.cos(t * obj.speed * 0.7 + obj.phase) * 0.002;
            } else if (obj.type === 'heart') {
                obj.mesh.rotation.y = t * 0.4;
                const scale = 1.2 + Math.sin(t * 2) * 0.08;
                obj.mesh.scale.set(scale, scale, scale);
            } else if (obj.type === 'helix') {
                obj.mesh.rotation.y = t * 0.3;
            }
        });

        renderer.render(scene, camera);
        requestAnimationFrame(animate);
    }
    animate();

    // Handle resize
    const ro = new ResizeObserver(() => {
        const nw = parent.clientWidth;
        const nh = parent.clientHeight;
        camera.aspect = nw / nh;
        camera.updateProjectionMatrix();
        renderer.setSize(nw, nh);
    });
    ro.observe(parent);
}

/* ================================================================
   CLAIM SUBMISSION
   ================================================================ */
async function handleClaimSubmit(e) {
    e.preventDefault();
    clearErrors();

    const payload = {
        claim_id: document.getElementById('claim-id').value.trim(),
        patient_id: document.getElementById('patient-id').value.trim(),
        provider_id: document.getElementById('provider-id').value.trim(),
        procedure_code: document.getElementById('procedure-code').value.trim(),
        diagnosis_code: document.getElementById('diagnosis-code').value.trim(),
        billed_amount: parseFloat(document.getElementById('billed-amount').value)
    };

    // Validate
    for (const [key, val] of Object.entries(payload)) {
        if (!val && val !== 0) {
            showError('claim-error', `Please fill in ${key.replace(/_/g, ' ')}`);
            return false;
        }
    }
    if (isNaN(payload.billed_amount) || payload.billed_amount <= 0) {
        showError('claim-error', 'Billed amount must be a positive number');
        return false;
    }

    setLoading('btn-analyze', true);
    try {
        const res = await fetch(`${API_BASE}/predict-claim`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            const data = await res.json();
            renderResults(data);
        } else {
            const err = await res.json();
            showError('claim-error', err.detail || `Error: ${res.status}`);
        }
    } catch (err) {
        showError('claim-error', 'Cannot connect to API server. Is the backend running?');
    }
    setLoading('btn-analyze', false);
    return false;
}

function renderResults(data) {
    // Hide 3D, show results
    document.getElementById('animation-panel').style.display = 'none';
    document.getElementById('results-panel').style.display = 'block';
    threeScene = null; // Stop animation

    const prediction = data.prediction;
    const risk = data.risk;
    const score = data.score;
    const riskScore = data.risk_score;

    // Header
    const headerClass = prediction === 'ACCEPTED' ? 'accepted' : prediction === 'DENIED' ? 'denied' : 'medium';
    const predColor = prediction === 'ACCEPTED' ? '#2e7d32' : prediction === 'DENIED' ? '#d32f2f' : '#e65100';
    const badgeBg = prediction === 'ACCEPTED' ? '#5ABE8A' : prediction === 'DENIED' ? '#FF6B6B' : '#FF9F43';

    document.getElementById('result-header').className = `result-header ${headerClass}`;
    document.getElementById('result-header').innerHTML = `
        <div class="result-prediction" style="color:${predColor}">${prediction === 'ACCEPTED' ? '✅ Claim Accepted' : prediction === 'DENIED' ? '⚠️ Claim Denied' : '⏳ Medium Risk'}</div>
        <div class="result-score" style="color:${predColor}">Denial Probability: ${(score * 100).toFixed(1)}% | Risk Score: ${riskScore}</div>
        <span class="result-risk-badge" style="background:${badgeBg}">${risk} RISK</span>
    `;

    // Top factors
    const factors = data.top_2_features || [];
    let factorsHtml = '<div class="result-section-title">🎯 Top Denial Factors</div>';
    factors.forEach(f => {
        factorsHtml += `<div class="factor-row"><span class="factor-name">⚠️ ${f.feature}</span><span class="factor-pct">${f.percentage}%</span></div>`;
    });
    document.getElementById('result-factors').innerHTML = factorsHtml;

    // All contributions
    const contribs = data.feature_contributions || {};
    const sorted = Object.entries(contribs).sort((a, b) => b[1] - a[1]);
    const maxPct = sorted.length > 0 ? sorted[0][1] : 1;
    let contribHtml = '<div class="result-section-title">📊 Feature Contributions</div>';
    sorted.forEach(([name, pct]) => {
        const barW = Math.max(5, (pct / maxPct) * 100);
        contribHtml += `
            <div class="contrib-row">
                <span>${name}</span>
                <div class="contrib-bar-bg"><div class="contrib-bar" style="width:${barW}%"></div></div>
                <span style="font-weight:600;min-width:40px;text-align:right">${pct}%</span>
            </div>`;
    });
    document.getElementById('result-contributions').innerHTML = contribHtml;

    // Policy explanation
    document.getElementById('result-policy').innerHTML = `
        <div class="result-section-title">📜 Policy Explanation</div>
        <div class="policy-box">${data.policy_explanation || 'No policy explanation available.'}</div>
    `;

    // Recommendations
    const recs = data.recommendations || [];
    let recHtml = '<div class="result-section-title">💡 Recommendations</div>';
    recs.forEach(r => { recHtml += `<div class="rec-item">→ ${r}</div>`; });
    document.getElementById('result-recommendations').innerHTML = recHtml;

    // Execution trace
    const flow = data.execution_flow || [];
    let traceHtml = '<div class="result-section-title">⚙️ System Execution Trace</div>';
    flow.forEach(step => {
        traceHtml += `<div class="trace-step"><div><div class="trace-node">${step.node} — ${step.label}</div><div class="trace-detail">${step.detail}</div></div></div>`;
    });
    document.getElementById('result-trace').innerHTML = traceHtml;
}

function resetClaimForm() {
    document.getElementById('claim-form').reset();
    document.getElementById('results-panel').style.display = 'none';
    document.getElementById('animation-panel').style.display = 'block';
    clearErrors();
    initThreeJS();
}

/* ================================================================
   INIT
   ================================================================ */
document.addEventListener('DOMContentLoaded', () => {
    // Check if already logged in
    const savedUser = localStorage.getItem('cs_user');
    if (savedUser) {
        currentUser = savedUser;
        showHomePage();
    }
});
