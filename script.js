// script.js
 document.addEventListener('DOMContentLoaded', function() {
    const iframe = document.getElementById('live-stream');
    const statusBadge = document.querySelector('.status-badge');
    const streamNote = document.querySelector('.stream-note');

    // Only run on live.html when the live-stream iframe exists
    if (iframe) {
        iframe.addEventListener('load', function() {
            console.log('Live stream loaded');
        });
    }

    // Optional: Add any other functionality here
});