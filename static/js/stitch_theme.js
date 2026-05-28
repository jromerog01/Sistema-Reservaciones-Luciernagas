const homeHeader = document.querySelector("[data-home-header]");
const homeHeroImage = document.querySelector("[data-home-hero-image]");

const updateHomeHeader = () => {
    if (!homeHeader) {
        return;
    }

    homeHeader.classList.toggle("is-scrolled", window.scrollY > 50);
};

const updateHomeHeroParallax = () => {
    if (!homeHeroImage) {
        return;
    }

    homeHeroImage.style.transform = `translateY(${window.scrollY * 0.18}px)`;
};

window.addEventListener("scroll", () => {
    updateHomeHeader();
    updateHomeHeroParallax();
}, { passive: true });

updateHomeHeader();
updateHomeHeroParallax();
