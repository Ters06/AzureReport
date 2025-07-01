// This file should only define the function. The main execution call is in ui.js.
function initializeInteractiveTable() {
    const table = document.querySelector('.table-sortable');
    if (!table) return;

    // --- Sorting Logic ---
    table.querySelectorAll('thead th.sortable').forEach(th => {
        th.addEventListener('click', (e) => {
            // Stop if the filter button was clicked
            if (e.target.closest('.filter-btn')) return;

            const columnKey = th.dataset.columnKey;
            const currentSortBy = th.dataset.currentSortBy;
            const currentSortOrder = th.dataset.currentSortOrder;

            let newSortOrder = 'asc';
            if (columnKey === currentSortBy) {
                newSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
            }

            const url = new URL(window.location);
            url.searchParams.set('sort_by', columnKey);
            url.searchParams.set('sort_order', newSortOrder);
            url.searchParams.set('page', '1');
            window.location = url.toString();
        });
    });

    // --- Filtering Logic ---
    table.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleFilterMenu(e.currentTarget);
        });
    });
}

function toggleFilterMenu(button) {
    const header = button.closest('th');
    const filterKey = header.dataset.columnKey;

    // Close all other filter menus
    document.querySelectorAll('.filter-menu').forEach(menu => {
        if (menu.dataset.filterKey !== filterKey) {
            menu.classList.add('hidden');
        }
    });

    let menu = header.querySelector('.filter-menu');
    if (!menu) {
        // Create the menu if it doesn't exist
        menu = createFilterMenu(header, filterKey);
        header.appendChild(menu);
    }

    menu.classList.toggle('hidden');
}

function createFilterMenu(header, filterKey) {
    const menu = document.createElement('div');
    menu.className = 'filter-menu hidden absolute mt-2 w-56 bg-white dark:bg-gray-800 rounded-md shadow-lg py-1 z-20 border dark:border-gray-600';
    menu.dataset.filterKey = filterKey;
    menu.addEventListener('click', e => e.stopPropagation()); // Prevent menu from closing on inner click

    // `tableFilterData` and `activeFilters` are expected to be global JS objects defined in the HTML template
    const options = tableFilterData[filterKey] || [];
    const activeOptions = new Set(activeFilters[filterKey] || []);

    const optionsHTML = options.map(opt => `
        <label class="block px-2 py-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
            <input type="checkbox" class="mr-2 filter-option" value="${opt}" ${activeOptions.has(opt) ? 'checked' : ''}>
            ${opt || '(Blank)'}
        </label>
    `).join('');

    menu.innerHTML = `
        <div class="p-2 text-gray-800 dark:text-gray-200">
            <div class="max-h-48 overflow-y-auto border-b dark:border-gray-600 py-1">
                ${optionsHTML}
            </div>
            <div class="flex justify-end mt-2 space-x-2">
                <button class="px-3 py-1 text-xs bg-gray-500 text-white rounded hover:bg-gray-600 clear-filter">Clear</button>
                <button class="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 apply-filters">Apply</button>
            </div>
        </div>
    `;

    menu.querySelector('.apply-filters').addEventListener('click', applyAllFilters);
    menu.querySelector('.clear-filter').addEventListener('click', () => {
        menu.querySelectorAll('.filter-option').forEach(opt => opt.checked = false);
        applyAllFilters();
    });

    return menu;
}

function applyAllFilters() {
    const url = new URL(window.location);

    document.querySelectorAll('.filter-menu').forEach(menu => {
        const filterKey = menu.dataset.filterKey;
        const checkedOptions = [...menu.querySelectorAll('.filter-option:checked')].map(opt => opt.value);

        if (checkedOptions.length > 0) {
            url.searchParams.set(filterKey, checkedOptions.join(','));
        } else {
            url.searchParams.delete(filterKey);
        }
    });

    url.searchParams.set('page', '1');
    window.location = url.toString();
}
