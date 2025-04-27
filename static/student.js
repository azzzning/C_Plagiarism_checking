document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("form");
    const fileInput = document.querySelector("input[type='file']");
    const fileLabel = document.createElement("p");

    fileInput.parentNode.insertBefore(fileLabel, fileInput.nextSibling);

    fileInput.addEventListener("change", () => {
        const file = fileInput.files[0];
        if (file) {
            fileLabel.textContent = `已选择文件：${file.name}`;
        } else {
            fileLabel.textContent = '';
        }
    });

    form.addEventListener("submit", (e) => {
        const name = form.querySelector("input[name='name']").value.trim();
        const cls = form.querySelector("input[name='class']").value.trim();
        const file = fileInput.files[0];

        if (!name || !cls) {
            alert("请填写姓名和班级！");
            e.preventDefault();
            return;
        }

        if (!file) {
            alert("请上传代码文件！");
            e.preventDefault();
            return;
        }

        const allowed = ['txt', 'c'];
        const ext = file.name.split('.').pop().toLowerCase();
        if (!allowed.includes(ext)) {
            alert("仅支持 .txt 或 .c 文件！");
            e.preventDefault();
        }
    });
});
