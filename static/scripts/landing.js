document.addEventListener('DOMContentLoaded', () => {
    const albumGrid = document.querySelector('.album-grid');
    const backgroundCarousel = document.querySelector('.background-carousel');
    const columns = document.querySelectorAll('.album-column');
    let isAnimationPaused = false;

    columns.forEach((column, columnIndex) => {
        const items = Array.from(column.querySelectorAll('.album-item'));

        const imageHeight = 200;
        const spacing = 50; // Increased spacing between items in pixels
        const totalItemHeight = imageHeight + spacing;

        items.forEach((item, index) => {
            item.style.animation = 'none';

            const startY = -150 + (index * totalItemHeight);

            const columnOffset = columnIndex * 20;

            item.style.transform = `translateY(${startY + columnOffset}px)`;
        });

        column.items = items;
        column.speed = 0.7 + (columnIndex * 0.1);
    });

    function animateColumns() {
        if (isAnimationPaused) return;

        columns.forEach(column => {
            column.items.forEach((item, index) => {
                const transform = item.style.transform;
                let currentY = parseFloat(transform.replace('translateY(', '').replace('px)', ''));

                currentY += column.speed;

                item.style.transform = `translateY(${currentY}px)`;

                if (currentY > window.innerHeight + 200) {
                    let topItemY = Infinity;
                    column.items.forEach(otherItem => {
                        if (otherItem === item) return;
                        const otherY = parseFloat(otherItem.style.transform.replace('translateY(', '').replace('px)', ''));
                        if (otherY < topItemY) {
                            topItemY = otherY;
                        }
                    });

                    const imageHeight = 200;
                    const spacing = 50;
                    const newY = topItemY - imageHeight - spacing;
                    item.style.transform = `translateY(${newY}px)`;
                }
            });
        });

        requestAnimationFrame(animateColumns);
    }

    // Start animation
    requestAnimationFrame(animateColumns);

    // Pause animation on hover
    backgroundCarousel.addEventListener('mouseenter', () => {
        isAnimationPaused = true;
    });

    backgroundCarousel.addEventListener('mouseleave', () => {
        isAnimationPaused = false;
        requestAnimationFrame(animateColumns);
    });
});