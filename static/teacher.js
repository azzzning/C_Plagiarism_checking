const LOCAL_KEY = 'selected_files_global';
let selectedFiles = new Set();

function loadSelectedFromStorage() {
  const stored = localStorage.getItem(LOCAL_KEY);
  if (stored) {
    try {
      const parsed = JSON.parse(stored);
      selectedFiles = new Set(parsed);
    } catch (e) {
      selectedFiles = new Set();
    }
  }
}

function saveSelectedToStorage() {
  localStorage.setItem(LOCAL_KEY, JSON.stringify(Array.from(selectedFiles)));
}

window.addEventListener("DOMContentLoaded", () => {
  loadSelectedFromStorage();

  const selectPageBox = document.getElementById("select-page");
  const selectAllBtn = document.getElementById("select-all-btn");
  const clearAllBtn = document.getElementById("clear-all-btn");
  const searchBox = document.getElementById("search-box");
  const form = document.getElementById("main-form");

  const checkboxes = document.querySelectorAll(".select-box");
  const fileItems = document.querySelectorAll(".file-item");

  const allFilenames = Array.from(document.querySelectorAll(".all-filename"))
    .map(input => input.value);

  // 初始化：恢复勾选状态
  checkboxes.forEach(cb => {
    cb.checked = selectedFiles.has(cb.value);
    cb.addEventListener("change", () => {
      cb.checked ? selectedFiles.add(cb.value) : selectedFiles.delete(cb.value);
      saveSelectedToStorage();
    });
  });

  // 当前页全选
  selectPageBox.addEventListener("change", () => {
    checkboxes.forEach(cb => {
      cb.checked = selectPageBox.checked;
      if (cb.checked) selectedFiles.add(cb.value);
      else selectedFiles.delete(cb.value);
    });
    saveSelectedToStorage();
  });

  // 全选所有文件
  selectAllBtn.addEventListener("click", () => {
    allFilenames.forEach(f => selectedFiles.add(f));
    checkboxes.forEach(cb => cb.checked = true);
    selectPageBox.checked = true;
    saveSelectedToStorage();
  });

  // 清除所有选择
  clearAllBtn.addEventListener("click", () => {
    selectedFiles.clear();
    checkboxes.forEach(cb => cb.checked = false);
    selectPageBox.checked = false;
    saveSelectedToStorage();
  });

  // 搜索功能
  searchBox.addEventListener("input", () => {
    const keyword = searchBox.value.trim().toLowerCase();
    fileItems.forEach(item => {
      const name = item.getAttribute("data-name");
      item.style.display = !keyword || name.includes(keyword) ? "block" : "none";
    });
  });

  // ✅ 表单提交前：注入所有选中的文件（哪怕不在当前页）
  form.addEventListener("submit", () => {
    // 1. 移除页面已有的 <input name="selected">
    document.querySelectorAll('input[name="selected"]').forEach(el => el.remove());

    // 2. 动态插入所有选中文件为隐藏 input
    selectedFiles.forEach(filename => {
      const hiddenInput = document.createElement("input");
      hiddenInput.type = "hidden";
      hiddenInput.name = "selected";
      hiddenInput.value = filename;
      form.appendChild(hiddenInput);
    });
  });
});

