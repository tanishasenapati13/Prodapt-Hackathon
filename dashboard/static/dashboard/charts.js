/**
 * Chart.js configurations for the AI Resume Screening Dashboard.
 *
 * Two pages use charts:
 *   1. results.html   → Scores bar chart + Skills doughnut chart
 *   2. candidate_detail.html → Skill radar chart + Gap severity bar chart
 *
 * Data is injected from Django templates via window.dashboardData / window.candidateData.
 */

(function () {
    'use strict';

    // ── Color palette (matches dashboard.css vars) ──
    const COLORS = {
        primary: '#6366f1',
        primaryAlpha: 'rgba(99, 102, 241, 0.7)',
        secondary: '#8b5cf6',
        secondaryAlpha: 'rgba(139, 92, 246, 0.5)',
        success: '#10b981',
        successAlpha: 'rgba(16, 185, 129, 0.7)',
        warning: '#f59e0b',
        warningAlpha: 'rgba(245, 158, 11, 0.7)',
        danger: '#ef4444',
        dangerAlpha: 'rgba(239, 68, 68, 0.7)',
        info: '#06b6d4',
        infoAlpha: 'rgba(6, 182, 212, 0.7)',
        grid: 'rgba(75, 85, 99, 0.2)',
        text: '#94a3b8',
        textMuted: '#64748b',
    };

    // Gradient palette for bars / doughnut slices
    const GRADIENT_COLORS = [
        '#6366f1', '#8b5cf6', '#a855f7', '#06b6d4',
        '#10b981', '#f59e0b', '#ef4444', '#ec4899',
        '#14b8a6', '#f97316', '#84cc16', '#3b82f6',
    ];

    const GRADIENT_ALPHAS = GRADIENT_COLORS.map(c => c + 'b3'); // ~70% opacity

    // ── Shared defaults ──
    Chart.defaults.color = COLORS.text;
    Chart.defaults.borderColor = COLORS.grid;
    Chart.defaults.font.family = "'Inter', -apple-system, sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.pointStyleWidth = 10;
    Chart.defaults.plugins.legend.labels.padding = 16;

    /**
     * Get a color for a score value (green for high, yellow for mid, red for low).
     */
    function scoreColor(score) {
        if (score >= 85) return COLORS.success;
        if (score >= 70) return COLORS.warning;
        return COLORS.danger;
    }

    function scoreColorAlpha(score) {
        if (score >= 85) return COLORS.successAlpha;
        if (score >= 70) return COLORS.warningAlpha;
        return COLORS.dangerAlpha;
    }

    // ================================================================
    // RESULTS PAGE — Scores Bar Chart + Skills Doughnut Chart
    // ================================================================
    if (window.dashboardData) {
        const data = window.dashboardData;

        // ── Scores Bar Chart ──
        const scoresCtx = document.getElementById('scoresChart');
        if (scoresCtx && data.chartNames.length > 0) {
            new Chart(scoresCtx, {
                type: 'bar',
                data: {
                    labels: data.chartNames,
                    datasets: [{
                        label: 'Match Score (%)',
                        data: data.chartScores,
                        backgroundColor: data.chartScores.map(s => scoreColorAlpha(s)),
                        borderColor: data.chartScores.map(s => scoreColor(s)),
                        borderWidth: 2,
                        borderRadius: 8,
                        borderSkipped: false,
                        maxBarThickness: 52,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: '#1e293b',
                            titleColor: '#f1f5f9',
                            bodyColor: '#94a3b8',
                            borderColor: COLORS.grid,
                            borderWidth: 1,
                            cornerRadius: 8,
                            padding: 12,
                            callbacks: {
                                label: (ctx) => `Score: ${ctx.parsed.y}%`,
                            },
                        },
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            grid: { color: COLORS.grid },
                            ticks: {
                                callback: (v) => v + '%',
                                stepSize: 25,
                            },
                        },
                        x: {
                            grid: { display: false },
                            ticks: {
                                maxRotation: 45,
                                minRotation: 0,
                            },
                        },
                    },
                    animation: {
                        duration: 800,
                        easing: 'easeOutQuart',
                    },
                },
            });
        }

        // ── Skills Doughnut Chart ──
        const skillsCtx = document.getElementById('skillsChart');
        if (skillsCtx && data.skillLabels.length > 0) {
            new Chart(skillsCtx, {
                type: 'doughnut',
                data: {
                    labels: data.skillLabels,
                    datasets: [{
                        data: data.skillCounts,
                        backgroundColor: GRADIENT_COLORS.slice(0, data.skillLabels.length),
                        borderColor: '#0a0e1a',
                        borderWidth: 3,
                        hoverBorderColor: '#1e293b',
                        hoverOffset: 6,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '62%',
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                font: { size: 11 },
                                padding: 10,
                            },
                        },
                        tooltip: {
                            backgroundColor: '#1e293b',
                            titleColor: '#f1f5f9',
                            bodyColor: '#94a3b8',
                            borderColor: COLORS.grid,
                            borderWidth: 1,
                            cornerRadius: 8,
                            padding: 12,
                            callbacks: {
                                label: (ctx) => {
                                    const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                                    const pct = ((ctx.parsed / total) * 100).toFixed(1);
                                    return `${ctx.label}: ${ctx.parsed} candidates (${pct}%)`;
                                },
                            },
                        },
                    },
                    animation: {
                        animateRotate: true,
                        duration: 1000,
                        easing: 'easeOutQuart',
                    },
                },
            });
        }
    }

    // ================================================================
    // CANDIDATE DETAIL PAGE — Radar Chart + Gap Bar Chart
    // ================================================================
    if (window.candidateData) {
        const cdata = window.candidateData;

        // ── Skill Proficiency Radar Chart ──
        const radarCtx = document.getElementById('radarChart');
        if (radarCtx && cdata.skillNames.length > 0) {
            new Chart(radarCtx, {
                type: 'radar',
                data: {
                    labels: cdata.skillNames,
                    datasets: [{
                        label: 'Proficiency Level',
                        data: cdata.skillLevels,
                        backgroundColor: 'rgba(99, 102, 241, 0.15)',
                        borderColor: COLORS.primary,
                        borderWidth: 2,
                        pointBackgroundColor: COLORS.primary,
                        pointBorderColor: '#0a0e1a',
                        pointBorderWidth: 2,
                        pointRadius: 5,
                        pointHoverRadius: 7,
                        fill: true,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: '#1e293b',
                            titleColor: '#f1f5f9',
                            bodyColor: '#94a3b8',
                            borderColor: COLORS.grid,
                            borderWidth: 1,
                            cornerRadius: 8,
                            padding: 12,
                            callbacks: {
                                label: (ctx) => {
                                    const levels = ['', 'Beginner', 'Beginner', 'Intermediate', 'Advanced', 'Expert'];
                                    return `${levels[ctx.parsed.r] || 'Unknown'} (${ctx.parsed.r}/5)`;
                                },
                            },
                        },
                    },
                    scales: {
                        r: {
                            beginAtZero: true,
                            max: 5,
                            min: 0,
                            ticks: {
                                stepSize: 1,
                                display: false,
                            },
                            grid: {
                                color: COLORS.grid,
                            },
                            angleLines: {
                                color: COLORS.grid,
                            },
                            pointLabels: {
                                color: COLORS.text,
                                font: {
                                    size: 12,
                                    weight: '500',
                                },
                            },
                        },
                    },
                    animation: {
                        duration: 800,
                        easing: 'easeOutQuart',
                    },
                },
            });
        }

        // ── Gap Severity Horizontal Bar Chart ──
        const gapCtx = document.getElementById('gapChart');
        if (gapCtx && cdata.gapNames.length > 0) {
            const gapColors = cdata.gapImportances.map(imp => {
                if (imp >= 4) return COLORS.danger;
                if (imp >= 3) return COLORS.warning;
                if (imp >= 2) return COLORS.info;
                return COLORS.textMuted;
            });

            const gapAlphas = cdata.gapImportances.map(imp => {
                if (imp >= 4) return COLORS.dangerAlpha;
                if (imp >= 3) return COLORS.warningAlpha;
                if (imp >= 2) return COLORS.infoAlpha;
                return 'rgba(100, 116, 139, 0.5)';
            });

            new Chart(gapCtx, {
                type: 'bar',
                data: {
                    labels: cdata.gapNames,
                    datasets: [{
                        label: 'Gap Severity',
                        data: cdata.gapImportances,
                        backgroundColor: gapAlphas,
                        borderColor: gapColors,
                        borderWidth: 2,
                        borderRadius: 8,
                        borderSkipped: false,
                        maxBarThickness: 40,
                    }],
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: '#1e293b',
                            titleColor: '#f1f5f9',
                            bodyColor: '#94a3b8',
                            borderColor: COLORS.grid,
                            borderWidth: 1,
                            cornerRadius: 8,
                            padding: 12,
                            callbacks: {
                                label: (ctx) => {
                                    const levels = ['', 'Low', 'Medium', 'High', 'Critical'];
                                    return `Severity: ${levels[ctx.parsed.x] || 'Unknown'}`;
                                },
                            },
                        },
                    },
                    scales: {
                        x: {
                            beginAtZero: true,
                            max: 4,
                            grid: { color: COLORS.grid },
                            ticks: {
                                stepSize: 1,
                                callback: (v) => {
                                    const levels = ['', 'Low', 'Medium', 'High', 'Critical'];
                                    return levels[v] || '';
                                },
                            },
                        },
                        y: {
                            grid: { display: false },
                        },
                    },
                    animation: {
                        duration: 800,
                        easing: 'easeOutQuart',
                    },
                },
            });
        } else if (gapCtx) {
            // No gaps — show success message
            gapCtx.parentElement.innerHTML = `
                <div class="d-flex flex-column align-items-center justify-content-center h-100 text-success">
                    <i class="bi bi-check-circle-fill fs-1 mb-2"></i>
                    <p class="fw-600">No skill gaps identified!</p>
                </div>
            `;
        }
    }

})();
