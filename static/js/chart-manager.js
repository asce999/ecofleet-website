/**
 * EcoFleet Dashboard Chart Manager
 * Premium SaaS Aesthetic
 */

class ChartManager {
    constructor() {
        this.charts = new Map();
        this.updateColors();
    }

    updateColors() {
        if (typeof Chart === 'undefined') return;
        const style = getComputedStyle(document.body);
        this.colors = {
            textPrimary: style.getPropertyValue('--color-text-primary').trim() || style.getPropertyValue('--text').trim() || '#0f172a',
            textMuted: style.getPropertyValue('--color-text-muted').trim() || style.getPropertyValue('--muted').trim() || '#94a3b8',
            border: style.getPropertyValue('--color-border').trim() || style.getPropertyValue('--border').trim() || '#e2e8f0',
            primary: style.getPropertyValue('--color-primary').trim() || style.getPropertyValue('--cyan').trim() || '#2563eb',
            success: style.getPropertyValue('--color-success').trim() || style.getPropertyValue('--success').trim() || '#10b981',
            warning: style.getPropertyValue('--color-warning').trim() || style.getPropertyValue('--orange').trim() || '#f59e0b',
            danger: style.getPropertyValue('--color-danger').trim() || style.getPropertyValue('--danger').trim() || '#ef4444',
            info: style.getPropertyValue('--color-info').trim() || style.getPropertyValue('--purple').trim() || '#3b82f6',
        };

        Chart.defaults.font.family = style.getPropertyValue('--font-family-sans').trim() || "Inter, sans-serif";
        Chart.defaults.color = this.colors.textMuted;
        
        // Premium Custom HTML tooltips
        Chart.defaults.plugins.tooltip.enabled = false;
        Chart.defaults.plugins.tooltip.external = this.externalTooltipHandler.bind(this);

        Chart.defaults.maintainAspectRatio = false;
        Chart.defaults.elements.point.radius = 0;
        Chart.defaults.elements.point.hoverRadius = 4;
        Chart.defaults.elements.line.tension = 0.4; // smooth curves
        Chart.defaults.elements.line.borderWidth = 2;
    }

    externalTooltipHandler(context) {
        // Tooltip Element
        const {chart, tooltip} = context;
        let tooltipEl = chart.canvas.parentNode.querySelector('div.chartjs-custom-tooltip');

        if (!tooltipEl) {
            tooltipEl = document.createElement('div');
            tooltipEl.classList.add('chartjs-custom-tooltip');
            tooltipEl.style.background = 'rgba(15, 23, 42, 0.95)';
            tooltipEl.style.borderRadius = '8px';
            tooltipEl.style.color = 'white';
            tooltipEl.style.opacity = 1;
            tooltipEl.style.pointerEvents = 'none';
            tooltipEl.style.position = 'absolute';
            tooltipEl.style.transform = 'translate(-50%, 0)';
            tooltipEl.style.transition = 'all .1s ease';
            tooltipEl.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)';
            tooltipEl.style.zIndex = 10;
            tooltipEl.style.padding = '12px';
            tooltipEl.style.border = '1px solid rgba(255,255,255,0.1)';
            chart.canvas.parentNode.appendChild(tooltipEl);
        }

        // Hide if no tooltip
        if (tooltip.opacity === 0) {
            tooltipEl.style.opacity = 0;
            return;
        }

        // Set Text
        if (tooltip.body) {
            const titleLines = tooltip.title || [];
            const bodyLines = tooltip.body.map(b => b.lines);

            let innerHtml = '<div>';
            
            titleLines.forEach(title => {
                innerHtml += '<div style="font-size: 12px; font-weight: 600; color: #94a3b8; margin-bottom: 8px;">' + title + '</div>';
            });

            bodyLines.forEach((body, i) => {
                const colors = tooltip.labelColors[i];
                let style = 'background:' + colors.backgroundColor;
                style += '; border-color:' + colors.borderColor;
                style += '; border-width: 2px';
                style += '; width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 8px;';
                
                const span = '<span style="' + style + '"></span>';
                innerHtml += '<div style="display: flex; align-items: center; font-size: 13px; font-weight: 500; margin-bottom: 4px;">' + span + body + '</div>';
            });
            innerHtml += '</div>';

            tooltipEl.innerHTML = innerHtml;
        }

        const position = context.chart.canvas.getBoundingClientRect();
        tooltipEl.style.opacity = 1;
        tooltipEl.style.left = position.left + window.pageXOffset + tooltip.caretX + 'px';
        tooltipEl.style.top = position.top + window.pageYOffset + tooltip.caretY - 10 + 'px';
    }

    destroyChart(canvasId) {
        if (this.charts.has(canvasId)) {
            this.charts.get(canvasId).destroy();
            this.charts.delete(canvasId);
        }
    }

    _createGradient(ctx, colorHex) {
        // Convert hex or rgb to a vertical gradient fading out
        const gradient = ctx.createLinearGradient(0, 0, 0, 300);
        // Extremely crude parse just to ensure it looks good if it's a known theme color
        // For production, we assume colorHex is already somewhat processed or we just use a generic fade
        // The safest approach in Chart.js without full color parsing is setting the stops.
        
        // If it's an rgba string, we might struggle, but let's assume it's passed as the stroke color.
        // As a trick, we just use a subtle semi-transparent white/blue.
        // To be accurate, we'll try to just pass a soft blue gradient for the primary.
        gradient.addColorStop(0, colorHex === this.colors.primary ? 'rgba(37, 99, 235, 0.15)' : 'rgba(148, 163, 184, 0.15)');
        gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
        return gradient;
    }

    createLineChart(canvasId, labels, datasets, options = {}) {
        this.destroyChart(canvasId);
        this.updateColors();
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        const ctx = canvas.getContext('2d');

        // Enhance datasets with premium styling
        const premiumDatasets = datasets.map(ds => ({
            ...ds,
            borderWidth: 2,
            pointRadius: 0,
            pointHoverRadius: 4,
            pointBackgroundColor: '#fff',
            pointHoverBackgroundColor: ds.borderColor || this.colors.primary,
            pointBorderColor: ds.borderColor || this.colors.primary,
            pointBorderWidth: 2,
            tension: 0.4,
            fill: ds.fill !== false,
            backgroundColor: ds.fill !== false ? this._createGradient(ctx, ds.borderColor || this.colors.primary) : 'transparent',
        }));

        const defaultOptions = {
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                x: { 
                    grid: { display: false, drawBorder: false }, 
                    ticks: { color: this.colors.textMuted, font: { size: 11 } } 
                },
                y: { 
                    grid: { color: this.colors.border, borderDash: [4, 4], drawBorder: false }, 
                    ticks: { color: this.colors.textMuted, font: { size: 11 }, maxTicksLimit: 5 },
                    beginAtZero: true
                }
            }
        };

        const chart = new Chart(ctx, {
            type: 'line',
            data: { labels, datasets: premiumDatasets },
            options: { ...defaultOptions, ...options }
        });
        
        this.charts.set(canvasId, chart);
        return chart;
    }

    createBarChart(canvasId, labels, datasets, options = {}) {
        this.destroyChart(canvasId);
        this.updateColors();
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        const ctx = canvas.getContext('2d');

        const premiumDatasets = datasets.map(ds => ({
            ...ds,
            borderRadius: 4,
            borderWidth: 0,
            barThickness: 'flex',
            maxBarThickness: 32
        }));

        const defaultOptions = {
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                x: { 
                    grid: { display: false, drawBorder: false },
                    ticks: { font: { size: 11 } }
                },
                y: { 
                    grid: { color: this.colors.border, borderDash: [4, 4], drawBorder: false }, 
                    ticks: { font: { size: 11 }, maxTicksLimit: 5 },
                    beginAtZero: true 
                }
            }
        };

        const chart = new Chart(ctx, {
            type: 'bar',
            data: { labels, datasets: premiumDatasets },
            options: { ...defaultOptions, ...options }
        });
        
        this.charts.set(canvasId, chart);
        return chart;
    }

    createDoughnutChart(canvasId, labels, data, colors = [], options = {}) {
        this.destroyChart(canvasId);
        this.updateColors();
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const defaultOptions = {
            responsive: true,
            cutout: '75%',
            plugins: {
                legend: { 
                    position: 'right', 
                    labels: { 
                        usePointStyle: true, 
                        boxWidth: 8,
                        font: { size: 12 },
                        padding: 16
                    } 
                }
            },
            layout: {
                padding: { top: 10, bottom: 10 }
            }
        };

        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors.length ? colors : [this.colors.primary, this.colors.success, this.colors.warning, this.colors.danger, this.colors.info],
                    borderWidth: 0,
                    hoverOffset: 2
                }]
            },
            options: { ...defaultOptions, ...options }
        });
        
        this.charts.set(canvasId, chart);
        return chart;
    }
}

window.ChartManager = ChartManager;
