(() => {
    const fileInput = document.querySelector('input[type="file"][name="avatar"]');
    if (!fileInput) return;

    fileInput.addEventListener("change", () => {
        const file = fileInput.files[0];
        if (file && file.size > 5 * 1024 * 1024) {
            alert("Profile image must be smaller than 5 MB.");
            fileInput.value = "";
        }
    });
})();
