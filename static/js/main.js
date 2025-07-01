document.addEventListener('DOMContentLoaded', () => {
    // Initialize dashboard charts if on the index page
    const categoryChartCanvas = document.getElementById('categoryChart');
    if (categoryChartCanvas) {
        initializeDashboardCharts();
    }

    // Initialize interactive tables if on a list page
    const interactiveTable = document.querySelector('.table-sortable');
    if (interactiveTable) {
        initializeInteractiveTable(interactiveTable.id);
    }

    // Initialize all dropdowns
    initializeDropdowns();

    // Initialize items per page selector
    const limitSelector = document.getElementById('limit-selector');
    if (limitSelector) {
        limitSelector.addEventListener('change', (e) => {
            const newLimit = e.target.value;
            const url = new URL(window.location);
            url.searchParams.set('limit', newLimit);
            url.searchParams.set('page', '1'); // Reset to first page
            window.location = url.toString();
        });
    }
});

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


function initializeDropdowns() {
    const dropdownToggles = document.querySelectorAll('[data-dropdown-toggle]');

    dropdownToggles.forEach(toggle => {
        toggle.addEventListener('click', (event) => {
            event.stopPropagation();
            const dropdownId = toggle.getAttribute('data-dropdown-toggle');
            const dropdownMenu = document.getElementById(dropdownId);

            document.querySelectorAll('.relative > div').forEach(menu => {
                if (menu.id !== dropdownId) menu.classList.add('hidden');
            });
            dropdownMenu.classList.toggle('hidden');
        });
    });

    window.addEventListener('click', (event) => {
        if (!event.target.closest('[data-dropdown-toggle]')) {
            document.querySelectorAll('.relative > div').forEach(menu => {
                menu.classList.add('hidden');
            });
        }
    });
}

function initializeInteractiveTable(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;

    table.querySelectorAll('thead th.sortable').forEach(th => {
        th.addEventListener('click', (e) => {
            if (!e.target.closest('.filter-btn') && !e.target.closest('.filter-menu')) {
                sortTable(tableId, parseInt(th.dataset.columnIndex), th.dataset.sortType);
            }
        });

        const filterBtn = th.querySelector('.filter-btn');
        if (filterBtn) {
            filterBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                toggleFilterMenu(tableId, parseInt(th.dataset.columnIndex));
            });
        }
    });
}

function toggleFilterMenu(tableId, colIndex) {
    const table = document.getElementById(tableId);
    const header = table.querySelector(`th[data-column-index="${colIndex}"]`);

    document.querySelectorAll('.filter-menu').forEach(menu => {
        if (menu.parentElement.dataset.columnIndex !== colIndex.toString()) {
            menu.classList.add('hidden');
        }
    });

    let menu = header.querySelector('.filter-menu');
    if (!menu) {
        menu = document.createElement('div');
        menu.className = 'filter-menu hidden';
        header.classList.add('filter-menu-container');

        const values = [...new Set(Array.from(table.tBodies[0].rows).map(row => row.cells[colIndex].textContent.trim()))];
        values.sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));

        menu.innerHTML = `
            <div class="p-2 text-gray-800 dark:text-gray-200" onclick="event.stopPropagation()">
                <input type="text" placeholder="Search..." class="w-full p-1 mb-2 border rounded text-xs dark:bg-gray-700 dark:border-gray-600">
                <div class="max-h-48 overflow-y-auto border-t border-b dark:border-gray-600 py-1">
                    <label class="block px-2 py-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"><input type="checkbox" class="mr-2 select-all" checked>Select All</label>
                    ${values.map(val => `<label class="block px-2 py-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"><input type="checkbox" class="mr-2 filter-option" value="${val}" checked>${val || '(Blank)'}</label>`).join('')}
                </div>
                <div class="flex justify-end mt-2 space-x-2">
                    <button class="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 apply-filter">Apply</button>
                </div>
            </div>
        `;
        header.appendChild(menu);

        const searchInput = menu.querySelector('input[type="text"]');
        searchInput.addEventListener('keyup', (e) => {
            const filter = e.target.value.toLowerCase();
            menu.querySelectorAll('.filter-option').forEach(opt => {
                const label = opt.parentElement;
                label.style.display = label.textContent.toLowerCase().includes(filter) ? '' : 'none';
            });
        });

        menu.querySelector('.select-all').addEventListener('change', (e) => {
            menu.querySelectorAll('.filter-option').forEach(opt => opt.checked = e.target.checked);
        });

        menu.querySelector('.apply-filter').addEventListener('click', () => applyAllFilters(tableId));
    }

    menu.classList.toggle('hidden');
}


function applyAllFilters(tableId) {
    const table = document.getElementById(tableId);
    const filters = new Map();

    table.querySelectorAll('th[data-column-index]').forEach(th => {
        const menu = th.querySelector('.filter-menu');
        const colIndex = th.dataset.columnIndex;
        if (menu) {
            const checkedOptions = new Set([...menu.querySelectorAll('.filter-option:checked')].map(opt => opt.value));
            if (checkedOptions.size < menu.querySelectorAll('.filter-option').length) {
                filters.set(parseInt(colIndex), checkedOptions);
            }
        }
    });

    Array.from(table.tBodies[0].rows).forEach(row => {
        let shouldShow = true;
        for (const [colIndex, allowedValues] of filters.entries()) {
            const cellValue = row.cells[colIndex]?.textContent.trim();
            if (!allowedValues.has(cellValue)) {
                shouldShow = false;
                break;
            }
        }
        row.style.display = shouldShow ? '' : 'none';
    });

    document.querySelectorAll('.filter-menu').forEach(menu => menu.classList.add('hidden'));
}


function sortTable(tableId, n, type = 'str') {
    const table = document.getElementById(tableId);
    if (!table) return;

    const tbody = table.tBodies[0];
    const rows = Array.from(tbody.rows);
    const headers = table.tHead.querySelectorAll('th');
    const header = headers[n];

    const currentDir = header.getAttribute("data-dir") || "asc";
    const dir = currentDir === "asc" ? "desc" : "asc";

    headers.forEach(h => {
        h.removeAttribute("data-dir");
        h.querySelector('.sort-arrow')?.classList.remove('sorted-asc', 'sorted-desc');
    });
    header.setAttribute("data-dir", dir);
    header.querySelector('.sort-arrow')?.classList.add(dir === 'asc' ? 'sorted-asc' : 'sorted-desc');

    rows.sort((a, b) => {
        let valA = a.cells[n].textContent.trim();
        let valB = b.cells[n].textContent.trim();

        if (type === 'num') {
            valA = parseFloat(valA.replace(/[^0-9.-]+/g, "")) || 0;
            valB = parseFloat(valB.replace(/[^0-9.-]+/g, "")) || 0;
        } else {
            valA = valA.toLowerCase();
            valB = valB.toLowerCase();
        }

        if (valA < valB) return dir === 'asc' ? -1 : 1;
        if (valA > valB) return dir === 'asc' ? 1 : -1;
        return 0;
    });

    rows.forEach(row => tbody.appendChild(row));
}
