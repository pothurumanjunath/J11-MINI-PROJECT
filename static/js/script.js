document.addEventListener("DOMContentLoaded", function () {

    const uploadForm = document.getElementById("uploadForm");
    const cropImage = document.getElementById("cropImage");
    const dropZone = document.getElementById("dropZone");
    const fileName = document.getElementById("fileName");
    const imagePreview = document.getElementById("imagePreview");
    const previewContainer = document.getElementById("previewContainer");
    const analyzeBtn = document.getElementById("analyzeBtn");
    const loadingMessage = document.getElementById("loadingMessage");

    if (!uploadForm || !cropImage || !dropZone) {
        return;
    }

    // FILE VALIDATION AND PREVIEW

    function handleFile(file) {

        if (!file) {
            return;
        }

        const allowedTypes = ["image/jpeg", "image/png"];

        if (!allowedTypes.includes(file.type)) {
            alert("Please select a JPG, JPEG, or PNG image.");

            cropImage.value = "";
            fileName.textContent = "";
            previewContainer.style.display = "none";
            analyzeBtn.disabled = true;

            return;
        }

        const maxSize = 10 * 1024 * 1024;

        if (file.size > maxSize) {
            alert("Image size must be less than 10 MB.");

            cropImage.value = "";
            fileName.textContent = "";
            previewContainer.style.display = "none";
            analyzeBtn.disabled = true;

            return;
        }

        fileName.textContent = "Selected: " + file.name;

        const reader = new FileReader();

        reader.onload = function (event) {
            imagePreview.src = event.target.result;
            previewContainer.style.display = "block";
            analyzeBtn.disabled = false;
        };

        reader.onerror = function () {
            alert("Unable to preview this image. Please try another file.");
            analyzeBtn.disabled = true;
        };

        reader.readAsDataURL(file);
    }


    // CHOOSE IMAGE

    cropImage.addEventListener("change", function () {
        handleFile(this.files[0]);
    });


    // DRAG AND DROP

    dropZone.addEventListener("dragover", function (event) {
        event.preventDefault();
        dropZone.classList.add("dragover");
    });

    dropZone.addEventListener("dragleave", function () {
        dropZone.classList.remove("dragover");
    });

    dropZone.addEventListener("drop", function (event) {
        event.preventDefault();

        dropZone.classList.remove("dragover");

        const files = event.dataTransfer.files;

        if (files.length > 0) {

            const file = files[0];

            try {
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                cropImage.files = dataTransfer.files;
            } catch (error) {
                console.error("Unable to attach dropped file:", error);
            }

            handleFile(file);
        }
    });


    // LOADING ANIMATION

    uploadForm.addEventListener("submit", function (event) {

        if (!cropImage.files.length) {
            event.preventDefault();
            alert("Please select a crop image.");
            return;
        }

        const plantId = document.getElementById("plant_id");

        if (!plantId.value.trim()) {
            event.preventDefault();
            alert("Please enter a Plant ID.");
            plantId.focus();
            return;
        }

        analyzeBtn.disabled = true;
        analyzeBtn.textContent = "Analyzing...";

        loadingMessage.style.display = "block";
    });

});