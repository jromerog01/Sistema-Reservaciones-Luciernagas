const roomInput = document.querySelector("#hospedaje");
const roomButtons = document.querySelectorAll(".select-room");
const stateButtons = document.querySelectorAll(".state-filter");
const cabinPrice = document.querySelector("#cabin-price");
const campingPrice = document.querySelector("#camping-price");
const dialogTriggers = document.querySelectorAll("[data-dialog-target]");
const dialogs = document.querySelectorAll(".floating-dialog");

const pricesByState = {
    tlaxcala: {
        cabin: "$1,450 MXN",
        camping: "$380 MXN",
    },
    puebla: {
        cabin: "$1,620 MXN",
        camping: "$420 MXN",
    },
    edomex: {
        cabin: "$1,780 MXN",
        camping: "$460 MXN",
    },
};

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
        const prices = pricesByState[button.dataset.state];

        if (!prices || !cabinPrice || !campingPrice) {
            return;
        }

        cabinPrice.textContent = prices.cabin;
        campingPrice.textContent = prices.camping;

        stateButtons.forEach((item) => {
            item.classList.remove("active");
            item.setAttribute("aria-pressed", "false");
        });

        button.classList.add("active");
        button.setAttribute("aria-pressed", "true");
    });
});

dialogTriggers.forEach((button) => {
    button.addEventListener("click", () => {
        const dialog = document.querySelector(`#${button.dataset.dialogTarget}`);

        if (dialog) {
            dialog.showModal();
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
