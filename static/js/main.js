// Budget Planner - Main JavaScript File

// Utility function to format currency
function formatCurrency(amount) {
    return '$' + parseFloat(amount).toFixed(2);
}

// Utility function to format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

// Show success message
function showSuccess(message) {
    alert('✅ ' + message);
}

// Show error message
function showError(message) {
    alert('❌ ' + message);
}

// Initialize tooltips and other UI elements
document.addEventListener('DOMContentLoaded', function() {
    console.log('Budget Planner initialized');
});
