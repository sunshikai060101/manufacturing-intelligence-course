// 物料检测页面逻辑
let currentImageFile = null;
let currentImageDataUrl = null;

document.addEventListener('DOMContentLoaded', () => {
    const uploadArea = document.getElementById('upload-area');
    const imageInput = document.getElementById('image-input');
    const detectBtn = document.getElementById('btn-detect');

    // 点击上传
    uploadArea.addEventListener('click', () => imageInput.click());

    // 拖拽上传
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            handleImageFile(file);
        } else {
            showToast('请上传图像文件', 'warning');
        }
    });

    // 文件选择
    imageInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) handleImageFile(file);
    });

    // 检测按钮
    detectBtn.addEventListener('click', performDetection);
});

function handleImageFile(file) {
    currentImageFile = file;

    const reader = new FileReader();
    reader.onload = (e) => {
        currentImageDataUrl = e.target.result;
        const preview = document.getElementById('image-preview');
        preview.innerHTML = `<img src="${currentImageDataUrl}" alt="预览">`;
    };
    reader.readAsDataURL(file);

    document.getElementById('btn-detect').disabled = false;
    showToast('图像已加载，点击开始检测', 'info');
}

async function performDetection() {
    if (!currentImageFile) {
        showToast('请先上传图像', 'warning');
        return;
    }

    const detectBtn = document.getElementById('btn-detect');
    const progressContainer = document.getElementById('detection-progress');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');

    detectBtn.disabled = true;
    progressContainer.classList.remove('hidden');
    progressFill.style.width = '10%';
    progressText.textContent = '正在上传图像...';

    try {
        const formData = new FormData();
        formData.append('file', currentImageFile);
        formData.append('enable_fusion', document.getElementById('opt-fusion').checked);
        formData.append('enable_anomaly', document.getElementById('opt-anomaly').checked);
        formData.append('simulate_sensors', document.getElementById('opt-simulate').checked);

        progressFill.style.width = '40%';
        progressText.textContent = '正在执行目标检测...';

        const response = await fetch(`${API_BASE}/detection/upload`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '检测失败');
        }

        progressFill.style.width = '80%';
        progressText.textContent = '正在处理检测结果...';

        const result = await response.json();

        progressFill.style.width = '100%';
        progressText.textContent = '检测完成!';

        // 渲染结果
        renderDetectionResults(result);
        renderFusionResults(result);
        renderAnomalyResults(result);

        // 在预览图上绘制检测框
        drawDetectionBoxes(result);

        showToast(`检测完成，共发现 ${result.total_objects} 个目标`, 'success');

        setTimeout(() => {
            progressContainer.classList.add('hidden');
            detectBtn.disabled = false;
        }, 1500);

    } catch (error) {
        console.error('检测失败:', error);
        showToast(error.message || '检测失败', 'error');
        progressContainer.classList.add('hidden');
        detectBtn.disabled = false;
    }
}

function renderDetectionResults(result) {
    const container = document.getElementById('detection-results');
    document.getElementById('detection-count').textContent = `${result.total_objects} 个目标`;

    if (!result.detections || result.detections.length === 0) {
        container.innerHTML = '<div class="empty-state">未检测到目标</div>';
        return;
    }

    container.innerHTML = result.detections.map((d, i) => `
        <div class="result-card">
            <div class="result-card-header">
                <span class="result-class">#${i + 1} ${d.class_name_cn} (${d.class_name})</span>
                <span class="result-confidence">置信度: ${(d.confidence * 100).toFixed(1)}%</span>
            </div>
            <div class="result-details">
                位置: X=${d.bbox.x.toFixed(1)}, Y=${d.bbox.y.toFixed(1)}<br>
                尺寸: W=${d.bbox.w.toFixed(1)}, H=${d.bbox.h.toFixed(1)}<br>
                类别ID: ${d.class_id}
            </div>
        </div>
    `).join('');
}

function renderFusionResults(result) {
    const container = document.getElementById('fusion-results');
    if (!result.fusion_results || result.fusion_results.length === 0) {
        container.innerHTML = '<div class="empty-state">未启用多传感器融合</div>';
        return;
    }

    container.innerHTML = result.fusion_results.map((f, i) => `
        <div class="result-card">
            <div class="result-card-header">
                <span class="result-class">#${i + 1} ${f.final_class_cn}</span>
                ${getFusionBadge(f.status)}
            </div>
            <div class="result-details">
                融合置信度: ${(f.confidence * 100).toFixed(1)}%<br>
                视觉置信度: ${(f.visual_confidence * 100).toFixed(1)}%<br>
                传感器置信度: ${(f.sensor_confidence * 100).toFixed(1)}%<br>
                ${f.weight_value !== null ? `实测重量: ${f.weight_value.toFixed(2)} kg<br>` : ''}
                ${f.expected_weight_range ? `期望重量: ${f.expected_weight_range[0].toFixed(1)} - ${f.expected_weight_range[1].toFixed(1)} kg` : ''}
            </div>
            <ul class="result-reasons">
                ${f.reasons.map(r => `<li>${r}</li>`).join('')}
            </ul>
        </div>
    `).join('');
}

function renderAnomalyResults(result) {
    const container = document.getElementById('anomaly-results');
    if (!result.anomaly_results || result.anomaly_results.length === 0) {
        container.innerHTML = '<div class="empty-state">未启用异常检测</div>';
        return;
    }

    container.innerHTML = result.anomaly_results.map((a, i) => `
        <div class="result-card">
            <div class="result-card-header">
                <span class="result-class">#${i + 1} 异常分析</span>
                ${getAnomalyBadge(a.is_anomaly, a.anomaly_level)}
            </div>
            <div class="result-details">
                异常分数: ${(a.anomaly_score * 100).toFixed(1)}%<br>
                各维度评分:<br>
                ${Object.entries(a.dimension_scores).map(([k, v]) =>
                    `&nbsp;&nbsp;${k}: ${(v * 100).toFixed(1)}%`
                ).join('<br>')}
            </div>
            <ul class="result-reasons">
                ${a.reasons.map(r => `<li>${r}</li>`).join('')}
            </ul>
        </div>
    `).join('');
}

function drawDetectionBoxes(result) {
    if (!currentImageDataUrl || !result.detections) return;

    const img = new Image();
    img.onload = () => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');

        // 限制最大尺寸
        const maxWidth = 600;
        const scale = Math.min(1, maxWidth / img.width);
        canvas.width = img.width * scale;
        canvas.height = img.height * scale;

        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

        const colors = ['#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6', '#ec4899'];

        result.detections.forEach((d, i) => {
            const color = colors[i % colors.length];
            const x = (d.bbox.x - d.bbox.w / 2) * scale;
            const y = (d.bbox.y - d.bbox.h / 2) * scale;
            const w = d.bbox.w * scale;
            const h = d.bbox.h * scale;

            // 绘制框
            ctx.strokeStyle = color;
            ctx.lineWidth = 3;
            ctx.strokeRect(x, y, w, h);

            // 绘制标签背景
            const label = `${d.class_name_cn} ${(d.confidence * 100).toFixed(0)}%`;
            ctx.font = 'bold 14px sans-serif';
            const textWidth = ctx.measureText(label).width;
            ctx.fillStyle = color;
            ctx.fillRect(x, y - 24, textWidth + 12, 24);

            // 绘制标签文字
            ctx.fillStyle = '#fff';
            ctx.fillText(label, x + 6, y - 7);
        });

        const preview = document.getElementById('image-preview');
        preview.innerHTML = `<img src="${canvas.toDataURL()}" alt="检测结果">`;
    };
    img.src = currentImageDataUrl;
}
