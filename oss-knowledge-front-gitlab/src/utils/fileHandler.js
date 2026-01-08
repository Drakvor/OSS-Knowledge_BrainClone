// 파일 크기 포맷팅
export const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 Bytes";

    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

// 파일 타입 검증
export const validateFileType = (file) => {
    const allowedTypes = {
        "text/plain": "txt",
        "image/png": "png",
        "image/jpeg": "jpg",
        "image/jpg": "jpg",
        "application/pdf": "pdf",
    };

    return allowedTypes[file.type] || null;
};

// 파일 크기 검증 (10MB 제한)
export const validateFileSize = (file) => {
    const maxSize = 10 * 1024 * 1024; // 10MB
    return file.size <= maxSize;
};

// 파일 읽기
export const readFileAsDataURL = (file) => {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
};

// 파일을 Base64 문자열로 변환 (Excel 등 바이너리 파일용)
export const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            // data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,UEsD...
            // 형태에서 base64 부분만 추출
            const result = e.target.result;
            if (!result || !result.includes(",")) {
                reject(new Error("Invalid data URL format"));
                return;
            }
            const base64String = result.split(",")[1];
            if (!base64String) {
                reject(new Error("Failed to extract Base64 content"));
                return;
            }
            resolve(base64String);
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
};

// 파일을 UTF-8 텍스트 문자열로 변환 (텍스트 파일용)
export const fileToText = (file) => {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = reject;
        reader.readAsText(file, "utf-8");
    });
};

// 파일 아이콘 가져오기
export const getFileIcon = (fileType) => {
    const icons = {
        txt: "📄",
        png: "🖼️",
        jpg: "🖼️",
        jpeg: "🖼️",
        pdf: "📑",
    };

    return icons[fileType] || "📎";
};
