document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('wheel-canvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const wrapper = document.getElementById('wheel-wrapper');

    const sectors = [
        { name: '★ Karambit\nDoppler',        color: '#ffd700', glow: '#fff3b0', id: 100 },
        { name: '★ Butterfly\nSlaughter',     color: '#ff6600', glow: '#ffaa33', id: 101 },
        { name: 'M4A1-S\nKnight',             color: '#eb4b4b', glow: '#ff8080', id: 102 },
        { name: 'AWP\nMedusa',                color: '#8847ff', glow: '#b380ff', id: 103 },
        { name: 'AK-47\nFire Serpent',        color: '#d32ce6', glow: '#f062ff', id: 104 },
        { name: 'USP-S\nKill Confirmed',      color: '#00bcd4', glow: '#66ffff', id: 105 },
        { name: 'Glock\nDragon Tattoo',       color: '#4caf50', glow: '#8bff8b', id: 106 },
        { name: 'Deagle\nCobalt Disruption',  color: '#2196f3', glow: '#80cfff', id: 107 },
        { name: 'Nothing',                    color: '#666666', glow: '#999999', id: 200 }
    ];

    let selectedIndex = null;
    window._spinning = false;
    let currentRotation = 0;

    const spinButton = document.getElementById('spin-button');
    const selectedSkinText = document.getElementById('selected-skin-text');
    const resultModal = document.getElementById('result-modal');
    const modalSelected = document.getElementById('modal-selected');
    const modalOutcome = document.getElementById('modal-outcome');
    const modalWinMsg = document.getElementById('modal-win-message');
    const modalLossMsg = document.getElementById('modal-loss-message');
    const modalDoubleSection = document.getElementById('modal-double-section');
    const doubleBtn = document.getElementById('double-or-nothing-btn');
    const doubleResult = document.getElementById('double-result');
    const modalCloseBtn = document.getElementById('modal-close-btn');

    function resizeCanvas() {
        if (!wrapper) return;
        const size = Math.min(wrapper.clientWidth, 400);
        canvas.width = size;
        canvas.height = size;
        drawWheel(currentRotation);
    }

    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    function drawWheel(rotation = 0) {
        const cx = canvas.width / 2;
        const cy = canvas.height / 2;
        const radius = Math.min(cx, cy) - 8;
        const arcSize = (2 * Math.PI) / sectors.length;

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        ctx.beginPath();
        ctx.arc(cx, cy, radius + 3, 0, 2 * Math.PI);
        ctx.strokeStyle = 'rgba(241, 196, 15, 0.4)';
        ctx.lineWidth = 2;
        ctx.stroke();

        sectors.forEach((sector, i) => {
            const startAngle = i * arcSize + rotation;
            const endAngle = startAngle + arcSize;

            const gradient = ctx.createLinearGradient(cx - radius, cy - radius, cx + radius, cy + radius);
            gradient.addColorStop(0, sector.color);
            gradient.addColorStop(1, '#1a1a1a');

            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.arc(cx, cy, radius, startAngle, endAngle);
            ctx.closePath();
            ctx.fillStyle = gradient;
            ctx.fill();
            ctx.strokeStyle = '#f1c40f';
            ctx.lineWidth = 1;
            ctx.stroke();

            ctx.save();
            ctx.translate(cx, cy);
            ctx.rotate(startAngle + arcSize / 2);
            ctx.textAlign = "right";
            ctx.fillStyle = '#ffffff';
            ctx.font = `bold ${Math.max(10, radius/20)}px Roboto, sans-serif`;
            ctx.shadowColor = sector.glow;
            ctx.shadowBlur = 6;
            const lines = sector.name.split('\n');
            lines.forEach((line, idx) => {
                ctx.fillText(line, radius - 10, -4 + idx * (radius/16));
            });
            ctx.shadowBlur = 0;
            ctx.restore();
        });

        ctx.beginPath();
        ctx.arc(cx, cy, radius * 0.08, 0, 2 * Math.PI);
        const coinGrad = ctx.createRadialGradient(cx-2, cy-2, 1, cx, cy, radius*0.08);
        coinGrad.addColorStop(0, '#fff7cc');
        coinGrad.addColorStop(0.4, '#f1c40f');
        coinGrad.addColorStop(1, '#b8860b');
        ctx.fillStyle = coinGrad;
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 1;
        ctx.stroke();
        ctx.font = `bold ${Math.max(10, radius/12)}px Orbitron, sans-serif`;
        ctx.fillStyle = '#000';
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText('GO', cx, cy);
    }

    document.querySelectorAll('.inventory-slot').forEach(slot => {
        slot.addEventListener('click', () => {
            if (window._spinning) return;
            document.querySelectorAll('.inventory-slot').forEach(s => s.classList.remove('selected'));
            slot.classList.add('selected');
            selectedIndex = parseInt(slot.dataset.index);
            spinButton.disabled = false;
            spinButton.textContent = '🎰 КРУТИТЬ';
            const name = slot.querySelector('.inventory-slot-name').textContent;
            selectedSkinText.textContent = `Выбран: ${name}`;
            if (window.playClickSound) window.playClickSound();
            const oddsBtn = document.getElementById('odds-button');
            if (oddsBtn) oddsBtn.disabled = false;
        });
    });

    spinButton.addEventListener('click', () => {
        if (window._spinning || selectedIndex === null) return;
        window._spinning = true;
        spinButton.disabled = true;
        spinButton.textContent = 'Крутим...';
        selectedSkinText.textContent = 'Колесо вращается...';

        if (window.playSpinSound) window.playSpinSound();

        fetch('/spin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ skin_index: selectedIndex })
        })
        .then(res => res.json())
        .then(data => {
            const sectorIndex = data.sector_index;
            animateWheelToSector(sectorIndex, () => {
                if (data.outcome_name !== 'Nothing') {
                    if (window.playWinSound) window.playWinSound();
                } else {
                    if (window.playLoseSound) window.playLoseSound();
                }

                updateInventoryAfterSpin(selectedIndex, data.outcome_name !== 'Nothing');
                showResultModal(data);

                if (data.outcome_name !== 'Nothing' && ['classified', 'covert', 'rare_special'].includes(data.outcome_rarity)) {
                    launchConfetti();
                }

                window._spinning = false;
                spinButton.disabled = true;
                spinButton.textContent = 'ВЫБЕРИТЕ СКИН';
                selectedSkinText.textContent = 'Выберите скин для следующего апгрейда';
                selectedIndex = null;
            });
        })
        .catch(err => {
            console.error(err);
            alert('Ошибка сервера');
            window._spinning = false;
            spinButton.disabled = false;
            spinButton.textContent = '🎰 КРУТИТЬ';
            selectedSkinText.textContent = 'Ошибка. Попробуйте снова.';
        });
    });

    function animateWheelToSector(targetSectorIndex, callback) {
        const arcSize = (2 * Math.PI) / sectors.length;
        const pointerAngle = -Math.PI / 2;
        let targetRotation = pointerAngle - targetSectorIndex * arcSize - arcSize / 2;
        while (targetRotation < 0) targetRotation += 2 * Math.PI;
        const fullTurns = 4 + Math.floor(Math.random() * 3);
        const finalRotation = fullTurns * 2 * Math.PI + targetRotation;
        const startRotation = currentRotation;
        const duration = 4000;
        const startTime = performance.now();

        function step(now) {
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const c1 = 1.70158;
            const c3 = c1 + 1;
            const easeOutBack = 1 + c3 * Math.pow(progress - 1, 3) + c1 * Math.pow(progress - 1, 2);
            currentRotation = startRotation + (finalRotation - startRotation) * easeOutBack;
            drawWheel(currentRotation);

            if (progress < 1) {
                requestAnimationFrame(step);
            } else {
                currentRotation = finalRotation % (2 * Math.PI);
                drawWheel(currentRotation);
                if (callback) callback();
            }
        }
        requestAnimationFrame(step);
    }

    function updateInventoryAfterSpin(usedIndex, win) {
        const slots = document.querySelectorAll('.inventory-slot');
        if (slots.length > usedIndex) {
            slots[usedIndex].remove();
        }
        if (win) {
            window._shouldReload = true;
        }
    }

    function showResultModal(data) {
        modalSelected.textContent = data.selected_name;
        modalOutcome.textContent = data.outcome_name;
        modalWinMsg.style.display = 'none';
        modalLossMsg.style.display = 'none';
        modalDoubleSection.style.display = 'none';
        doubleResult.innerHTML = '';

        if (data.outcome_name !== 'Nothing') {
            modalWinMsg.style.display = 'block';
            modalWinMsg.textContent = `🎉 Вы выиграли предмет ценностью $${data.outcome_price}!`;
            if (data.outcome_id && data.outcome_id !== 200) {
                modalDoubleSection.style.display = 'block';
                doubleBtn.dataset.skinId = data.outcome_id;
                doubleBtn.style.display = 'inline-block';
                doubleBtn.disabled = false;
            }
        } else {
            modalLossMsg.style.display = 'block';
            modalLossMsg.textContent = '😞 К сожалению, ничего не выпало.';
        }

        resultModal.style.display = 'flex';
    }

    if (modalCloseBtn) {
        modalCloseBtn.addEventListener('click', () => {
            resultModal.style.display = 'none';
            if (window._shouldReload) {
                window._shouldReload = false;
                location.reload();
            }
        });
    }

    if (doubleBtn) {
        doubleBtn.addEventListener('click', () => {
            const skinId = parseInt(doubleBtn.dataset.skinId);
            if (!skinId) return;

            doubleBtn.disabled = true;
            doubleBtn.style.display = 'none';
            const animContainer = document.getElementById('double-anim');
            const coin = document.getElementById('double-coin');
            if (animContainer) {
                animContainer.classList.add('double-active');
            }
            if (window.playDoubleSound) window.playDoubleSound();

            setTimeout(() => {
                fetch('/double', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ skin_id: skinId })
                })
                .then(res => res.json())
                .then(data => {
                    if (animContainer) {
                        animContainer.classList.remove('double-active');
                        animContainer.classList.add(data.win ? 'double-win' : 'double-lose');
                    }
                    doubleResult.innerHTML = '';
                    if (data.win) {
                        if (window.playDoubleWin) window.playDoubleWin();
                        doubleResult.innerHTML = `<span class="win-text">🎉 ${data.message}</span>`;
                        launchConfetti();
                    } else {
                        if (window.playDoubleLose) window.playDoubleLose();
                        doubleResult.innerHTML = `<span class="loss-text">😞 ${data.message}</span>`;
                    }
                    document.querySelector('.balance-value').textContent = '$' + data.balance;
                    window._shouldReload = true;
                })
                .catch(err => {
                    console.error('Double error:', err);
                    alert('Ошибка Double or Nothing.');
                    doubleBtn.style.display = 'inline-block';
                    doubleBtn.disabled = false;
                    if (animContainer) animContainer.classList.remove('double-active');
                });
            }, 4000);
        });
    }

    function launchConfetti() {
        if (typeof confetti !== 'function') return;
        const duration = 2000;
        const end = Date.now() + duration;
        const colors = ['#f1c40f', '#e67e22', '#ffffff', '#e84393', '#4caf50'];

        (function frame() {
            confetti({
                particleCount: 3,
                angle: 60,
                spread: 55,
                origin: { x: 0, y: 0.6 },
                colors: colors
            });
            confetti({
                particleCount: 3,
                angle: 120,
                spread: 55,
                origin: { x: 1, y: 0.6 },
                colors: colors
            });

            if (Date.now() < end) {
                requestAnimationFrame(frame);
            }
        }());
    }
});