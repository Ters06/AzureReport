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
