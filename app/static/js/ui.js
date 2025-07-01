document.addEventListener('DOMContentLoaded', () => {
    // Initialize dashboard charts if on the index page
    if (document.getElementById('categoryChart')) {
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

function initializeDropdowns() {
    const dropdownToggles = document.querySelectorAll('[data-dropdown-toggle]');

    dropdownToggles.forEach(toggle => {
        toggle.addEventListener('click', (event) => {
            event.stopPropagation();
            const dropdownId = toggle.getAttribute('data-dropdown-toggle');
            const dropdownMenu = document.getElementById(dropdownId);

            // Close all other dropdowns
            document.querySelectorAll('.relative > div.absolute').forEach(menu => {
                if (menu.id !== dropdownId) {
                    menu.classList.add('hidden');
                }
            });
            // Toggle the clicked one
            dropdownMenu.classList.toggle('hidden');
        });
    });

    // Close dropdowns if clicking outside
    window.addEventListener('click', (event) => {
        if (!event.target.closest('[data-dropdown-toggle]')) {
            document.querySelectorAll('.relative > div.absolute').forEach(menu => {
                menu.classList.add('hidden');
            });
        }
    });
}
