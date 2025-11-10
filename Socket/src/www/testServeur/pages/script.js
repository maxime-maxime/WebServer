<script>
// 1. Collapse/Expand sections
document.querySelectorAll('h2').forEach(h2 => {
    h2.style.cursor = 'pointer';
    const next = h2.nextElementSibling;
    if(next.tagName === 'TABLE' || next.tagName === 'P' || next.tagName === 'FORM'){
        next.style.transition = 'max-height 0.5s ease, opacity 0.5s ease';
        next.style.overflow = 'hidden';
        next.style.maxHeight = '500px';
        next.style.opacity = '1';
    }
    h2.addEventListener('click', () => {
        const element = h2.nextElementSibling;
        if(element.style.maxHeight && element.style.maxHeight !== '0px'){
            element.style.maxHeight = '0px';
            element.style.opacity = '0';
        } else {
            element.style.maxHeight = '500px';
            element.style.opacity = '1';
        }
    });
});

// 2. Highlight rows on hover with JS (plus progressif)
document.querySelectorAll('table tr').forEach(tr => {
    tr.addEventListener('mouseenter', () => {
        tr.style.backgroundColor = 'rgba(255,165,0,0.3)';
        tr.style.transition = 'background-color 0.3s';
    });
    tr.addEventListener('mouseleave', () => {
        tr.style.backgroundColor = '';
    });
});

// 3. Scroll to form on load if POST
if(window.location.search.includes('message') || window.location.search.includes('fucku')){
    document.querySelector('form').scrollIntoView({behavior: 'smooth'});
}

// 4. Fade-in tables on page load
window.addEventListener('load', () => {
    document.querySelectorAll('table').forEach(table => {
        table.style.opacity = '0';
        table.style.transition = 'opacity 0.7s ease';
        setTimeout(() => { table.style.opacity = '1'; }, 50);
    });
});
</script>
