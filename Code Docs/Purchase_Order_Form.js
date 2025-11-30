/*
 * Purchase_Order_Form.js
 * Corrected JavaScript implementation for the purchase order form.
 * Located inside the repository so HTML files can reference it.
 */

function formatCurrency(amount) {
    return `$${Number(amount).toFixed(2)}`;
}

function addItemRow() {
    const tableBody = document.querySelector('#itemTable tbody');
    if (!tableBody) return;

    const newRow = tableBody.insertRow();

    // 1. ISBN/Book ID
    let cell1 = newRow.insertCell();
    cell1.innerHTML = '<input type="text" class="isbn" required>';

    // 2. Quantity
    let cell2 = newRow.insertCell();
    cell2.innerHTML = '<input type="number" class="quantity" value="1" min="1" required>';

    // 3. Unit Cost
    let cell3 = newRow.insertCell();
    cell3.innerHTML = '<input type="number" class="cost" value="0.00" min="0" step="0.01" required>';

    // 4. Line Total (Read-only output)
    let cell4 = newRow.insertCell();
    cell4.classList.add('line-total');
    cell4.textContent = formatCurrency(0);

    // 5. Delete Button
    let cell5 = newRow.insertCell();
    cell5.innerHTML = '<button type="button" class="delete-row">Delete</button>';

    // Attach event listeners for the inputs and delete button
    const qtyInput = newRow.querySelector('.quantity');
    const costInput = newRow.querySelector('.cost');
    const deleteBtn = newRow.querySelector('.delete-row');

    const recalc = () => calculateLineTotal(newRow);
    qtyInput.addEventListener('input', recalc);
    costInput.addEventListener('input', recalc);
    deleteBtn.addEventListener('click', () => deleteItemRow(newRow));

    // Calculate initial line total
    calculateLineTotal(newRow);
}

function calculateLineTotal(rowOrElement) {
    // Accept either the row element or an input within the row
    const row = rowOrElement.tagName === 'TR' ? rowOrElement : rowOrElement.closest('tr');
    if (!row) return;

    const quantity = parseFloat(row.querySelector('.quantity')?.value) || 0;
    const cost = parseFloat(row.querySelector('.cost')?.value) || 0;
    const lineTotal = quantity * cost;

    const lineCell = row.querySelector('.line-total');
    if (lineCell) lineCell.textContent = formatCurrency(lineTotal);

    calculateGrandTotal();
}

function calculateGrandTotal() {
    let grandTotal = 0;
    document.querySelectorAll('.line-total').forEach(cell => {
        const totalValue = parseFloat(cell.textContent.replace('$', '')) || 0;
        grandTotal += totalValue;
    });

    const grandEl = document.getElementById('grandTotal');
    if (grandEl) grandEl.textContent = formatCurrency(grandTotal);
}

function deleteItemRow(rowOrButton) {
    // Accept either the <tr> element or the button inside the row
    const row = rowOrButton.tagName === 'TR' ? rowOrButton : rowOrButton.closest('tr');
    if (!row) return;
    row.remove();
    calculateGrandTotal();
}

// If the table exists, ensure there's at least one row on load
document.addEventListener('DOMContentLoaded', () => {
    const tableBody = document.querySelector('#itemTable tbody');
    if (tableBody && tableBody.rows.length === 0) addItemRow();
});

// Export functions for Node / test environments (optional)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        addItemRow,
        calculateLineTotal,
        calculateGrandTotal,
        deleteItemRow,
        formatCurrency
    };
}
