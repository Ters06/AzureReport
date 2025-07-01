let categoryChartInstance, impactChartInstance, subscriptionChartInstance;
let selectedCategory = null;
let originalSubscriptionData = {};
let currentSubGroupBy = 'impact';

const impactColors = { 'High': 'rgba(239, 68, 68, 0.8)', 'Medium': 'rgba(249, 115, 22, 0.8)', 'Low': 'rgba(34, 197, 94, 0.8)' };
const categoryColors = {
    'Reliability': '#ef4444', 'Security': '#3b82f6', 'Cost': '#22c55e',
    'Operational excellence': '#8b5cf6', 'Performance': '#f97316'
};
const textColor = document.body.classList.contains('dark') ? '#e5e7eb' : '#374151';

function initializeDashboardCharts() {
    fetch('/api/data/recommendations-summary')
        .then(response => response.json())
        .then(data => {
            renderCategoryChart(data.categories);
            renderImpactChart(data.impacts, 'Recommendations by Impact');
        });

    fetchSubscriptionData('impact');

    document.getElementById('group-by-impact-btn')?.addEventListener('click', () => switchSubscriptionGroup('impact'));
    document.getElementById('group-by-category-btn')?.addEventListener('click', () => switchSubscriptionGroup('category'));
    document.getElementById('hide-sub-id-toggle')?.addEventListener('change', () => renderSubscriptionChart());
    document.getElementById('show-with-recs-toggle')?.addEventListener('change', () => renderSubscriptionChart());
}

function switchSubscriptionGroup(groupBy) {
    if (currentSubGroupBy === groupBy) return;
    currentSubGroupBy = groupBy;
    document.getElementById('group-by-impact-btn').classList.toggle('active', groupBy === 'impact');
    document.getElementById('group-by-category-btn').classList.toggle('active', groupBy === 'category');
    fetchSubscriptionData(groupBy);
}

function fetchSubscriptionData(groupBy) {
    if (originalSubscriptionData[groupBy]) {
        renderSubscriptionChart();
        return;
    }
    fetch(`/api/data/recommendations-by-subscription/${groupBy}`)
        .then(response => response.json())
        .then(data => {
            originalSubscriptionData[groupBy] = data;
            renderSubscriptionChart();
        });
}

function renderCategoryChart(data) {
    const ctx = document.getElementById('categoryChart').getContext('2d');
    if (categoryChartInstance) categoryChartInstance.destroy();

    categoryChartInstance = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.labels.map(label => label || "Uncategorized"),
            datasets: [{ data: data.data, backgroundColor: data.labels.map(l => categoryColors[l] || '#9ca3af'), borderColor: document.body.classList.contains('dark') ? '#1f2937' : '#fff', borderWidth: 2, offset: Array(data.labels.length).fill(0) }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { position: 'right', labels: { color: textColor } } },
            onClick: (evt, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const label = evt.chart.data.labels[index];
                    const currentOffset = evt.chart.data.datasets[0].offset[index];

                    evt.chart.data.datasets[0].offset.fill(0);

                    if (currentOffset > 0) {
                        selectedCategory = null;
                        fetch('/api/data/recommendations-summary').then(res => res.json()).then(d => renderImpactChart(d.impacts, 'Recommendations by Impact'));
                    } else {
                        selectedCategory = label;
                        evt.chart.data.datasets[0].offset[index] = 20;
                        updateImpactChartForCategory(label, `Impact for ${label}`);
                    }
                    evt.chart.update();
                }
            }
        }
    });
}

function renderImpactChart(data, title) {
    const ctx = document.getElementById('impactChart').getContext('2d');
    document.getElementById('impact-chart-title').textContent = title;
    if (impactChartInstance) impactChartInstance.destroy();

    impactChartInstance = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.labels,
            datasets: [{ data: data.data, backgroundColor: data.labels.map(l => impactColors[l] || '#cccccc'), borderColor: document.body.classList.contains('dark') ? '#1f2937' : '#fff', borderWidth: 2 }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { position: 'right', labels: { color: textColor } } },
            onClick: (evt, elements) => {
                if (elements.length > 0) {
                    const impactLabel = evt.chart.data.labels[elements[0].index];
                    let url = new URL(window.location.origin + "/recommendations");
                    url.searchParams.append('impact', impactLabel);
                    if (selectedCategory) {
                        url.searchParams.append('category', selectedCategory.replace(/ /g, '-').toLowerCase());
                    }
                    window.location.href = url.toString();
                }
            }
        }
    });
}

function updateImpactChartForCategory(category, title) {
    fetch(`/api/data/impact-by-category/${category.replace(/ /g, '-').toLowerCase()}`)
        .then(response => response.json())
        .then(data => renderImpactChart(data, title));
}

function renderSubscriptionChart() {
    const data = originalSubscriptionData[currentSubGroupBy];
    if (!data) return;

    const ctx = document.getElementById('subscriptionChart').getContext('2d');
    if (subscriptionChartInstance) subscriptionChartInstance.destroy();

    let filteredData = JSON.parse(JSON.stringify(data));

    if (document.getElementById('show-with-recs-toggle')?.checked) {
        const indicesToKeep = [];
        for (let i = 0; i < filteredData.labels.length; i++) {
            const totalRecs = filteredData.datasets.reduce((sum, ds) => sum + ds.data[i], 0);
            if (totalRecs > 0) indicesToKeep.push(i);
        }
        filteredData.labels = filteredData.labels.filter((_, i) => indicesToKeep.includes(i));
        filteredData.datasets.forEach(ds => {
            ds.data = ds.data.filter((_, i) => indicesToKeep.includes(i));
        });
    }

    if (document.getElementById('hide-sub-id-toggle')?.checked) {
        filteredData.labels = filteredData.labels.map(label => label.split(' (')[0]);
    }

    const colors = currentSubGroupBy === 'impact' ? impactColors : categoryColors;

    subscriptionChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: filteredData.labels,
            datasets: filteredData.datasets.map(ds => ({ ...ds, backgroundColor: colors[ds.label] || '#9ca3af' }))
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', labels: { color: textColor } },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            let label = context.dataset.label || '';
                            if (label) { label += ': '; }
                            if (context.parsed.y !== null) { label += context.parsed.y; }
                            return label;
                        }
                    }
                }
            },
            scales: { x: { stacked: true, ticks: { color: textColor } }, y: { stacked: true, ticks: { color: textColor } } },
            onClick: (evt, elements) => {
                if (elements.length > 0) {
                    const subIndex = elements[0].index;
                    const groupIndex = elements[0].datasetIndex;
                    const subscriptionLabel = data.labels[subIndex].split(' (')[0];
                    const groupLabel = data.datasets[groupIndex].label;

                    let url = new URL(window.location.origin + "/recommendations");
                    url.searchParams.append('subscription', subscriptionLabel);
                    url.searchParams.append(currentSubGroupBy, groupLabel.replace(/ /g, '-').toLowerCase());
                    window.location.href = url.toString();
                }
            }
        }
    });
}
