function previewImage(event) {
    var reader = new FileReader();
    reader.onload = function() {
        var output = document.getElementById('imagePreview');
        var container = document.getElementById('imagePreviewContainer');
        output.src = reader.result;
        output.style.display = 'block';
        container.style.display = 'flex'; // Mostrar o contêiner
    }
    reader.readAsDataURL(event.target.files[0]);
}

document.getElementById('image').addEventListener('change', previewImage);
