let fileList = [];
let selected = new Set();

const input = document.getElementById("file-input");
const fileListDiv = document.getElementById("file-list");
const resultDiv = document.getElementById("result-output");

input.addEventListener("change", (e) => {
    const newFile = e.target.files[0];
    if (newFile && !fileList.find(f => f.name === newFile.name)) {
        fileList.push(newFile);
        selected.add(newFile.name);
        renderFileList();
    }
    input.value = '';
});

document.getElementById("clear-btn").addEventListener("click", () => {
    fileList = [];
    selected.clear();
    renderFileList();
});

function renderFileList() {
    fileListDiv.innerHTML = "";
    fileList.forEach((file) => {
        const div = document.createElement("div");
        div.className = "file-item";

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.checked = selected.has(file.name);

        checkbox.addEventListener("change", () => {
            if (checkbox.checked) selected.add(file.name);
            else selected.delete(file.name);
        });

        const label = document.createElement("label");
        label.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;

        div.appendChild(checkbox);
        div.appendChild(label);
        fileListDiv.appendChild(div);
    });
}

document.getElementById("analyze-btn").addEventListener("click", async () => {
    if (selected.size < 2) {
        alert("请至少选择两个文件");
        return;
    }

    const formData = new FormData();
    fileList.forEach(file => formData.append("files[]", file));
    selected.forEach(name => formData.append("selected[]", name));

    resultDiv.innerHTML = "正在分析，请稍候...";

    const res = await fetch("/analyze", {
        method: "POST",
        body: formData
    });

    const data = await res.json();
    renderResult(data);
});

function renderResult(data) {
    resultDiv.innerHTML = "";

    if (data.error) {
        resultDiv.innerHTML = `<div class="error">${data.error}</div>`;
        return;
    }

    const renderBlock = (file1, file2, similarity, level, matches) => {
        let block = `<div class="result-card">
            <h3>${file1} vs ${file2}</h3>
            <p>相似度：<strong>${similarity}%</strong></p>
            <p>判断结果：<span class="level">${level}</span></p>
        `;

        if (matches.length > 0) {
            block += `<h4>相似片段：</h4>`;
            matches.forEach(m => {
                block += `<pre><code><mark>${m.code1}</mark></code></pre>`;
                block += `<pre><code><mark>${m.code2}</mark></code></pre>`;
            });
        }

        block += `</div>`;
        return block;
    };

    if (data.mode === "pair") {
        resultDiv.innerHTML += renderBlock(data.file1, data.file2, data.similarity, data.level, data.matches);
    } else {
        if (data.results.length === 0) {
            resultDiv.innerHTML = "<p>未检测到高度相似文件。</p>";
        } else {
            data.results.forEach(r => {
                resultDiv.innerHTML += renderBlock(r.file1, r.file2, r.similarity, r.level, r.matches);
            });
        }
    }
}
