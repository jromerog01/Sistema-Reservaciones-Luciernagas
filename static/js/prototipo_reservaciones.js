const roomInput = document.querySelector("#hospedaje");
const roomButtons = document.querySelectorAll(".select-room");
const stateButtons = document.querySelectorAll("[data-lodging-state-filter]");
const homeMapStateButtons = document.querySelectorAll("[data-home-map-state-filter]");
const lodgingMinimumsElement = document.querySelector("#lodging-minimums-data");
const lodgingFields = document.querySelectorAll("[data-lodging-field][data-lodging-type]");
const dialogTriggers = document.querySelectorAll("[data-dialog-target]");
const dialogs = document.querySelectorAll(".floating-dialog");
const mapElement = document.querySelector("#parks-map");
const mapDataElement = document.querySelector("#parks-map-data");
const parksCarousel = document.querySelector("[data-parks-carousel]");
const carouselPrevButton = document.querySelector("[data-carousel-prev]");
const carouselNextButton = document.querySelector("[data-carousel-next]");
const reviewsCarousel = document.querySelector("[data-reviews-carousel]");
const reviewsCarouselPrevButton = document.querySelector("[data-reviews-carousel-prev]");
const reviewsCarouselNextButton = document.querySelector("[data-reviews-carousel-next]");
const parkFilterButtons = document.querySelectorAll("[data-park-filter]");
const parkCards = document.querySelectorAll("[data-park-card]");
const activeFilterPanel = document.querySelector("[data-active-filter-panel]");
const activeFilterList = document.querySelector("[data-active-filters]");
const clearParkFiltersButton = document.querySelector("[data-clear-park-filters]");
const parkFilterEmpty = document.querySelector("[data-filter-empty]");
const parksCount = document.querySelector("[data-parks-count]");
const mapFilterButtons = document.querySelectorAll("[data-map-filter]");
const mapActiveFilterPanel = document.querySelector("[data-map-active-filter-panel]");
const mapActiveFilterList = document.querySelector("[data-map-active-filters]");
const clearMapFiltersButton = document.querySelector("[data-clear-map-filters]");
const mapFilterEmpty = document.querySelector("[data-map-filter-empty]");
const mapParksCount = document.querySelector("[data-map-parks-count]");
const miniMapElements = document.querySelectorAll("[data-mini-map]");

let lodgingMinimumsByState = {};

const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#039;",
})[character]);

const renderMapTags = (tags = [], emptyMessage = "Sin registros") => {
    if (!tags.length) {
        return `<span>${escapeHtml(emptyMessage)}</span>`;
    }

    return tags.map((tag) => `<span>${escapeHtml(tag)}</span>`).join("");
};

const initializeMiniParkMaps = () => {
    if (!miniMapElements.length || !window.L) {
        return;
    }

    const leaflet = window.L;
    const miniIcon = leaflet.divIcon({
        className: "park-map-pin mini-park-map-pin",
        html: "<span></span>",
        iconSize: [24, 32],
        iconAnchor: [12, 32],
    });

    miniMapElements.forEach((element) => {
        const latitude = Number(element.dataset.lat);
        const longitude = Number(element.dataset.lng);

        if (
            !Number.isFinite(latitude)
            || !Number.isFinite(longitude)
            || element.dataset.initialized === "true"
            || element.offsetParent === null
        ) {
            return;
        }

        const miniMap = leaflet.map(element, {
            attributionControl: false,
            boxZoom: false,
            dragging: false,
            doubleClickZoom: false,
            keyboard: false,
            scrollWheelZoom: false,
            tap: false,
            touchZoom: false,
            zoomControl: false,
        }).setView([latitude, longitude], 14);

        leaflet.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 19,
            referrerPolicy: "origin",
        }).addTo(miniMap);

        leaflet.marker([latitude, longitude], {
            icon: miniIcon,
            title: element.dataset.title || "",
        }).addTo(miniMap);

        element.dataset.initialized = "true";
        setTimeout(() => miniMap.invalidateSize(), 0);
    });
};

if (lodgingMinimumsElement) {
    try {
        lodgingMinimumsByState = JSON.parse(lodgingMinimumsElement.textContent);
    } catch (error) {
        lodgingMinimumsByState = {};
    }
}

const formatLodgingField = (field, values = {}) => {
    if (field === "precio") {
        return `desde ${values.precio || "no disponible"}`;
    }

    if (field === "capacidad") {
        return values.capacidad
            ? `Capacidad: desde ${values.capacidad} personas`
            : "Capacidad: desde no disponible";
    }

    if (field === "unidades") {
        return values.unidades
            ? `Disponibles: desde ${values.unidades} ${values.unidadDisponible || "unidades"}`
            : "Disponibles: desde no disponible";
    }

    return "";
};

const updateLodgingMinimums = (state) => {
    const lodgingMinimums = lodgingMinimumsByState[state];

    if (!lodgingMinimums || !lodgingFields.length) {
        return;
    }

    lodgingFields.forEach((fieldElement) => {
        const values = lodgingMinimums[fieldElement.dataset.lodgingType];
        const text = formatLodgingField(fieldElement.dataset.lodgingField, values);

        if (text) {
            fieldElement.textContent = text;
        }
    });
};

const initializeParksMap = () => {
    if (!mapElement || !mapDataElement || !window.L) {
        return;
    }

    let parks = [];

    try {
        parks = JSON.parse(mapDataElement.textContent);
    } catch (error) {
        return;
    }

    const leaflet = window.L;
    const map = leaflet.map(mapElement, {
        scrollWheelZoom: false,
    }).setView([19.32, -98.16], 8);

    leaflet.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        referrerPolicy: "origin",
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);

    const markerGroup = leaflet.featureGroup().addTo(map);
    const parkMarkers = [];
    const parkIcon = leaflet.divIcon({
        className: "park-map-pin",
        html: "<span></span>",
        iconSize: [34, 44],
        iconAnchor: [17, 44],
        popupAnchor: [0, -38],
    });

    parks.forEach((park) => {
        const latitude = Number(park.latitud);
        const longitude = Number(park.longitud);

        if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
            return;
        }

        const marker = leaflet.marker([latitude, longitude], {
            icon: parkIcon,
            title: park.nombre,
        }).bindPopup(`
            <article class="map-popup">
                <span class="map-popup-state">${escapeHtml(park.estado)}</span>
                <h3>${escapeHtml(park.nombre)}</h3>
                <p>${escapeHtml(park.descripcion)}</p>

                <details open>
                    <summary>Informacion</summary>
                    <dl>
                        <div>
                            <dt>Horario</dt>
                            <dd>${escapeHtml(park.horario)}</dd>
                        </div>
                        <div>
                            <dt>Direccion</dt>
                            <dd>${escapeHtml(park.direccion)}</dd>
                        </div>
                    </dl>
                </details>

                <details>
                    <summary>Servicios</summary>
                    <div class="map-popup-services">
                        ${renderMapTags(park.servicios, "Sin servicios registrados")}
                    </div>
                </details>

                <details>
                    <summary>Hospedaje</summary>
                    <div class="map-popup-services">
                        ${renderMapTags(park.hospedajes, "Sin hospedajes registrados")}
                    </div>
                </details>

                <a class="map-popup-link" href="${escapeHtml(park.url)}">Ver detalle</a>
            </article>
        `);

        marker.addTo(markerGroup);
        parkMarkers.push({ marker, park });
    });

    const getSelectedMapFilters = () => Array.from(mapFilterButtons)
        .filter((button) => button.getAttribute("aria-pressed") === "true")
        .map((button) => ({
            type: button.dataset.filterType,
            value: button.dataset.filterValue,
            label: button.textContent.trim(),
        }));

    const groupMapFilters = (filters) => filters.reduce((groups, filter) => {
        if (!groups[filter.type]) {
            groups[filter.type] = [];
        }

        groups[filter.type].push(filter.value);
        return groups;
    }, {});

    const mapParkMatchesFilters = (park, groupedFilters) => {
        const selectedStates = groupedFilters.estado || [];
        const selectedLodgings = groupedFilters.hospedaje || [];
        const selectedServices = groupedFilters.servicio || [];
        const parkLodgings = park.hospedajesValores || [];
        const parkServices = park.serviciosValores || [];

        if (selectedStates.length && !selectedStates.includes(park.estadoValor)) {
            return false;
        }

        if (selectedLodgings.length && !selectedLodgings.every((lodging) => parkLodgings.includes(lodging))) {
            return false;
        }

        return !selectedServices.length || selectedServices.every((service) => parkServices.includes(service));
    };

    const renderActiveMapFilters = (filters) => {
        if (!mapActiveFilterPanel || !mapActiveFilterList) {
            return;
        }

        mapActiveFilterPanel.hidden = !filters.length;
        mapActiveFilterList.innerHTML = filters.map((filter) => `
            <button type="button" class="active-filter-chip" data-filter-type="${escapeHtml(filter.type)}" data-filter-value="${escapeHtml(filter.value)}">
                ${escapeHtml(filter.label)}
            </button>
        `).join("");
    };

    const fitVisibleMarkers = () => {
        if (!markerGroup.getLayers().length) {
            return;
        }

        map.fitBounds(markerGroup.getBounds(), {
            padding: [38, 38],
            maxZoom: 14,
        });
    };

    const updateMapFilters = () => {
        const filters = getSelectedMapFilters();
        const groupedFilters = groupMapFilters(filters);
        let visibleCount = 0;

        markerGroup.clearLayers();

        parkMarkers.forEach(({ marker, park }) => {
            if (!mapParkMatchesFilters(park, groupedFilters)) {
                return;
            }

            marker.addTo(markerGroup);
            visibleCount += 1;
        });

        renderActiveMapFilters(filters);

        if (mapFilterEmpty) {
            mapFilterEmpty.hidden = visibleCount > 0;
        }

        if (mapParksCount) {
            mapParksCount.textContent = `${visibleCount} ${visibleCount === 1 ? "parque" : "parques"}`;
        }

        fitVisibleMarkers();
    };

    const updateHomeMapStateFilter = (state) => {
        if (!homeMapStateButtons.length) {
            return;
        }

        let visibleCount = 0;
        markerGroup.clearLayers();

        parkMarkers.forEach(({ marker, park }) => {
            if (state !== "todos" && park.estadoValor !== state) {
                return;
            }

            marker.addTo(markerGroup);
            visibleCount += 1;
        });

        if (mapFilterEmpty) {
            mapFilterEmpty.hidden = visibleCount > 0;
        }

        fitVisibleMarkers();
    };

    mapFilterButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const isPressed = button.getAttribute("aria-pressed") === "true";

            button.setAttribute("aria-pressed", String(!isPressed));
            button.classList.toggle("active", !isPressed);
            updateMapFilters();
        });
    });

    mapActiveFilterList?.addEventListener("click", (event) => {
        const chip = event.target.closest("[data-filter-type][data-filter-value]");

        if (!chip) {
            return;
        }

        const filterButton = Array.from(mapFilterButtons).find((button) => (
            button.dataset.filterType === chip.dataset.filterType
            && button.dataset.filterValue === chip.dataset.filterValue
        ));

        if (filterButton) {
            filterButton.setAttribute("aria-pressed", "false");
            filterButton.classList.remove("active");
            updateMapFilters();
        }
    });

    clearMapFiltersButton?.addEventListener("click", () => {
        mapFilterButtons.forEach((button) => {
            button.setAttribute("aria-pressed", "false");
            button.classList.remove("active");
        });

        updateMapFilters();
    });

    homeMapStateButtons.forEach((button) => {
        button.addEventListener("click", () => {
            homeMapStateButtons.forEach((item) => {
                item.classList.remove("active");
                item.setAttribute("aria-pressed", "false");
            });

            button.classList.add("active");
            button.setAttribute("aria-pressed", "true");
            updateHomeMapStateFilter(button.dataset.homeMapStateFilter);
        });
    });

    fitVisibleMarkers();
};

initializeParksMap();
initializeMiniParkMaps();

const scrollCarouselByCard = (carousel, cardSelector, direction, fallbackWidth, shouldLoop = false) => {
    if (!carousel) {
        return;
    }

    const card = carousel.querySelector(cardSelector);
    const styles = window.getComputedStyle(carousel);
    const gap = Number.parseFloat(styles.columnGap || styles.gap) || 0;
    const scrollAmount = card ? card.getBoundingClientRect().width + gap : fallbackWidth;
    const maxScroll = carousel.scrollWidth - carousel.clientWidth;
    const nextScroll = carousel.scrollLeft + (direction * scrollAmount);
    let targetScroll = nextScroll;

    if (shouldLoop && maxScroll > 0) {
        if (direction > 0 && nextScroll >= maxScroll - 2) {
            targetScroll = 0;
        } else if (direction < 0 && nextScroll <= 0) {
            targetScroll = maxScroll;
        }
    }

    carousel.scrollTo({
        left: targetScroll,
        behavior: "smooth",
    });
};

const scrollParksCarousel = (direction) => {
    scrollCarouselByCard(parksCarousel, ".park-carousel-card", direction, 420);
};

carouselPrevButton?.addEventListener("click", () => {
    scrollParksCarousel(-1);
});

carouselNextButton?.addEventListener("click", () => {
    scrollParksCarousel(1);
});

const scrollReviewsCarousel = (direction) => {
    scrollCarouselByCard(reviewsCarousel, ".review-card", direction, 360, true);
};

reviewsCarouselPrevButton?.addEventListener("click", () => {
    scrollReviewsCarousel(-1);
});

reviewsCarouselNextButton?.addEventListener("click", () => {
    scrollReviewsCarousel(1);
});

const splitFilterValues = (value) => String(value ?? "").split(/\s+/).filter(Boolean);

const getSelectedParkFilters = () => Array.from(parkFilterButtons)
    .filter((button) => button.getAttribute("aria-pressed") === "true")
    .map((button) => ({
        type: button.dataset.filterType,
        value: button.dataset.filterValue,
        label: button.textContent.trim(),
    }));

const groupParkFilters = (filters) => filters.reduce((groups, filter) => {
    if (!groups[filter.type]) {
        groups[filter.type] = [];
    }

    groups[filter.type].push(filter.value);
    return groups;
}, {});

const parkMatchesFilters = (card, groupedFilters) => {
    const selectedStates = groupedFilters.estado || [];
    const selectedLodgings = groupedFilters.hospedaje || [];
    const selectedServices = groupedFilters.servicio || [];
    const cardLodgings = splitFilterValues(card.dataset.hospedajes);
    const cardServices = splitFilterValues(card.dataset.servicios);

    if (selectedStates.length && !selectedStates.includes(card.dataset.estado)) {
        return false;
    }

    if (selectedLodgings.length && !selectedLodgings.every((lodging) => cardLodgings.includes(lodging))) {
        return false;
    }

    return !selectedServices.length || selectedServices.every((service) => cardServices.includes(service));
};

const renderActiveParkFilters = (filters) => {
    if (!activeFilterPanel || !activeFilterList) {
        return;
    }

    activeFilterPanel.hidden = !filters.length;
    activeFilterList.innerHTML = filters.map((filter) => `
        <button type="button" class="active-filter-chip" data-filter-type="${escapeHtml(filter.type)}" data-filter-value="${escapeHtml(filter.value)}">
            ${escapeHtml(filter.label)}
        </button>
    `).join("");
};

const updateParkFilters = () => {
    if (!parkCards.length) {
        return;
    }

    const filters = getSelectedParkFilters();
    const groupedFilters = groupParkFilters(filters);
    let visibleCount = 0;

    parkCards.forEach((card) => {
        const isVisible = parkMatchesFilters(card, groupedFilters);
        card.hidden = !isVisible;
        card.classList.toggle("is-filtered-out", !isVisible);

        if (isVisible) {
            visibleCount += 1;
        }
    });

    renderActiveParkFilters(filters);

    if (parkFilterEmpty) {
        parkFilterEmpty.hidden = visibleCount > 0;
    }

    if (parksCount) {
        parksCount.textContent = `${visibleCount} ${visibleCount === 1 ? "parque" : "parques"}`;
    }
};

parkFilterButtons.forEach((button) => {
    button.addEventListener("click", () => {
        const isPressed = button.getAttribute("aria-pressed") === "true";

        button.setAttribute("aria-pressed", String(!isPressed));
        button.classList.toggle("active", !isPressed);
        updateParkFilters();
    });
});

activeFilterList?.addEventListener("click", (event) => {
    const chip = event.target.closest("[data-filter-type][data-filter-value]");

    if (!chip) {
        return;
    }

    const filterButton = Array.from(parkFilterButtons).find((button) => (
        button.dataset.filterType === chip.dataset.filterType
        && button.dataset.filterValue === chip.dataset.filterValue
    ));

    if (filterButton) {
        filterButton.setAttribute("aria-pressed", "false");
        filterButton.classList.remove("active");
        updateParkFilters();
    }
});

clearParkFiltersButton?.addEventListener("click", () => {
    parkFilterButtons.forEach((button) => {
        button.setAttribute("aria-pressed", "false");
        button.classList.remove("active");
    });

    updateParkFilters();
});

roomButtons.forEach((button) => {
    button.addEventListener("click", () => {
        if (roomInput) {
            roomInput.value = button.dataset.room;
        }

        document.querySelector("#reservar")?.scrollIntoView({ behavior: "smooth" });
    });
});

stateButtons.forEach((button) => {
    button.addEventListener("click", () => {
        updateLodgingMinimums(button.dataset.lodgingStateFilter);

        stateButtons.forEach((item) => {
            item.classList.remove("active");
            item.setAttribute("aria-pressed", "false");
        });

        button.classList.add("active");
        button.setAttribute("aria-pressed", "true");
    });
});

const activeStateButton = Array.from(stateButtons).find((button) => button.getAttribute("aria-pressed") === "true");
updateLodgingMinimums(activeStateButton?.dataset.lodgingStateFilter);

dialogTriggers.forEach((button) => {
    button.addEventListener("click", () => {
        const dialog = document.querySelector(`#${button.dataset.dialogTarget}`);

        if (dialog) {
            dialog.showModal();
            initializeMiniParkMaps();
        }
    });
});

dialogs.forEach((dialog) => {
    dialog.querySelectorAll("[data-dialog-close]").forEach((button) => {
        button.addEventListener("click", () => {
            dialog.close();
        });
    });

    dialog.addEventListener("click", (event) => {
        if (event.target === dialog) {
            dialog.close();
        }
    });
});
