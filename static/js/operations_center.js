/**
 * EcoFleet Express — Operations Center
 * Handles all chart rendering, empty-state management,
 * count-up animations, and UI interactions.
 */

document.addEventListener('DOMContentLoaded', () => {

    // ── Guard ──────────────────────────────────────────────────────────────
    if (typeof window.ChartManager === 'undefined') {
        console.error('[Ops Center] ChartManager not loaded — charts disabled.');
        return;
    }

    const manager = new window.ChartManager();

    // ── Helpers ────────────────────────────────────────────────────────────

    function loadChartData(id) {
        const el = document.getElementById(id);
        if (!el) return null;
        const raw = (el.textContent || '').trim();
        if (!raw || raw === 'null' || raw === '{}' || raw === '""' || raw === '[]') return null;
        try {
            const parsed = JSON.parse(raw);
            if (typeof parsed === 'object' && parsed !== null && Object.keys(parsed).length === 0) return null;
            return parsed;
        } catch (e) {
            console.warn(`[Ops Center] JSON parse failed for #${id}:`, e);
            return null;
        }
    }

    function hideChartCard(canvasId) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        const card = canvas.closest('.chart-card');
        if (!card) return;

        // Hide just the card
        card.style.display = 'none';

        // Collapse the grid only if ALL its chart-cards are now hidden
        const grid = card.closest('.chart-grid');
        if (grid) {
            const anyVisible = Array.from(grid.querySelectorAll('.chart-card'))
                .some(c => c.style.display !== 'none');
            if (!anyVisible) {
                grid.style.display = 'none';
            }
        }
    }

    function markRendered(canvasId) {
        const el = document.getElementById(canvasId);
        if (el) el.setAttribute('data-rendered', 'true');
    }

    // ── 1. Performance Chart ───────────────────────────────────────────────
    (function initPerformanceChart() {
        const data = loadChartData('chart-data-performance');
        if (!data || !data.labels || !data.data) {
            hideChartCard('performanceChart');
            return;
        }
        manager.createLineChart('performanceChart', data.labels, [
            {
                label: 'Response Time (ms)',
                data: data.data,
                borderColor: manager.colors.primary,
                fill: true,
            }
        ]);
        markRendered('performanceChart');
    })();

    // ── 2. Storage Chart ───────────────────────────────────────────────────
    (function initStorageChart() {
        const data = loadChartData('chart-data-storage');
        if (!data || !data.labels || !data.data) {
            hideChartCard('storageChart');
            return;
        }
        manager.createDoughnutChart(
            'storageChart',
            data.labels,
            data.data,
            [manager.colors.primary, manager.colors.warning, manager.colors.info, manager.colors.border]
        );
        markRendered('storageChart');
    })();

    // ── 3. System Events / Activity Chart ─────────────────────────────────
    (function initActivityChart() {
        const data = loadChartData('chart-data-activity');
        if (
            !data ||
            !Array.isArray(data.labels) ||
            !Array.isArray(data.datasets) ||
            data.labels.length === 0
        ) {
            hideChartCard('activityChart');
            return;
        }

        const colorMap = {
            'Info':     manager.colors.info,
            'Warnings': manager.colors.warning,
            'Errors':   manager.colors.danger,
        };

        const datasets = data.datasets.map(ds => ({
            label: ds.label,
            data: ds.data,
            borderColor: colorMap[ds.label] || manager.colors.primary,
            fill: false,
        }));

        manager.createLineChart('activityChart', data.labels, datasets, {
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: { usePointStyle: true, boxWidth: 8, font: { size: 11 }, padding: 16 },
                },
            },
        });
        markRendered('activityChart');
    })();

    // ── 4. Count-up animations ─────────────────────────────────────────────
    (function initCountUp() {
        document.querySelectorAll('.count-up').forEach(el => {
            const raw     = el.textContent.trim().replace(/,/g, '');
            const target  = parseFloat(raw);
            if (isNaN(target)) return;

            const isFloat  = raw.includes('.');
            const decimals = isFloat ? raw.split('.')[1].length : 0;
            const suffix   = el.dataset.suffix || '';
            const step     = Math.max(1, Math.floor(1400 / 60));
            const inc      = target / 60;
            let current    = 0;

            const timer = setInterval(() => {
                current = Math.min(current + inc, target);
                el.textContent = current.toFixed(decimals) + suffix;
                if (current >= target) clearInterval(timer);
            }, step);
        });
    })();

    // ── 5. Alert banner dismiss ────────────────────────────────────────────
    (function initAlertDismiss() {
        const btn = document.getElementById('alert-close');
        if (!btn) return;
        btn.addEventListener('click', () => {
            const banner = btn.closest('.alert-banner');
            if (!banner) return;
            Object.assign(banner.style, {
                transition: 'opacity 0.3s ease, max-height 0.4s ease, margin 0.3s ease',
                opacity:    '0',
                maxHeight:  '0',
                overflow:   'hidden',
                margin:     '0',
            });
            setTimeout(() => banner.remove(), 420);
        });
    })();

    // ── 6. Theme toggle — rebuild charts with updated CSS vars ─────────────
    (function initThemeToggle() {
        const toggle = document.getElementById('theme-toggle');
        if (!toggle) return;

        toggle.addEventListener('click', () => {
            setTimeout(() => {
                manager.updateColors();

                const perf = document.getElementById('performanceChart');
                if (perf && perf.getAttribute('data-rendered')) {
                    const d = loadChartData('chart-data-performance');
                    if (d && d.labels && d.data) {
                        manager.createLineChart('performanceChart', d.labels, [
                            { label: 'Response Time (ms)', data: d.data, borderColor: manager.colors.primary, fill: true }
                        ]);
                    }
                }

                const storage = document.getElementById('storageChart');
                if (storage && storage.getAttribute('data-rendered')) {
                    const d = loadChartData('chart-data-storage');
                    if (d && d.labels && d.data) {
                        manager.createDoughnutChart('storageChart', d.labels, d.data,
                            [manager.colors.primary, manager.colors.warning, manager.colors.info, manager.colors.border]
                        );
                    }
                }

                const activity = document.getElementById('activityChart');
                if (activity && activity.getAttribute('data-rendered')) {
                    const d = loadChartData('chart-data-activity');
                    if (d && d.labels && d.datasets) {
                        const colorMap = { 'Info': manager.colors.info, 'Warnings': manager.colors.warning, 'Errors': manager.colors.danger };
                        const datasets = d.datasets.map(ds => ({
                            label: ds.label, data: ds.data,
                            borderColor: colorMap[ds.label] || manager.colors.primary, fill: false,
                        }));
                        manager.createLineChart('activityChart', d.labels, datasets, {
                            plugins: { legend: { display: true, position: 'top', labels: { usePointStyle: true, boxWidth: 8, font: { size: 11 }, padding: 16 } } },
                        });
                    }
                }
            }, 80);
        });
    })();

});