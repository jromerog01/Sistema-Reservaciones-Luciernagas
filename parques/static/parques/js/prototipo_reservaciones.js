const roomInput = document.querySelector("#hospedaje");
const roomButtons = document.querySelectorAll(".select-room");

roomButtons.forEach((button) => {
    button.addEventListener("click", () => {
        roomInput.value = button.dataset.room;
        document.querySelector("#reservar").scrollIntoView({ behavior: "smooth" });
    });
});
