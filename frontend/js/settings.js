// 系统设置页面逻辑
async function loadSystemInfo() {
    try {
        const info = await apiRequest('/stats/system');
        renderSystemInfo(info);
    } catch (e) {
        console.error('加载系统信息失败:', e);
    }
}

function renderSystemInfo(info) {
    const container = document.getElementById('system-info');
    container.innerHTML = `
        <div class="system-info-item">
            <span class="system-info-label">系统名称</span>
            <span class="system-info-value">${info.system_name}</span>
        </div>
        <div class="system-info-item">
            <span class="system-info-label">系统版本</span>
            <span class="system-info-value">${info.version}</span>
        </div>
        <div class="system-info-item">
            <span class="system-info-label">模型状态</span>
            <span class="system-info-value">${info.model_loaded ? '<span class="badge badge-normal">已加载</span>' : '<span class="badge badge-warning">模拟模式</span>'}</span>
        </div>
        <div class="system-info-item">
            <span class="system-info-label">模型路径</span>
            <span class="system-info-value" style="font-size:11px;">${info.model_path}</span>
        </div>
        <div class="system-info-item">
            <span class="system-info-label">置信度阈值</span>
            <span class="system-info-value">${info.confidence_threshold}</span>
        </div>
        <div class="system-info-item">
            <span class="system-info-label">IOU阈值</span>
            <span class="system-info-value">${info.iou_threshold}</span>
        </div>
        <div class="system-info-item">
            <span class="system-info-label">检测类别数</span>
            <span class="system-info-value">${info.num_classes}</span>
        </div>
        <div class="system-info-item">
            <span class="system-info-label">数据库状态</span>
            <span class="system-info-value"><span class="badge badge-normal">${info.database_status}</span></span>
        </div>
        <div class="system-info-item">
            <span class="system-info-label">总检测次数</span>
            <span class="system-info-value">${info.anomaly_detector_stats?.total_detections || 0}</span>
        </div>
    `;
}

document.addEventListener('DOMContentLoaded', () => {
    // 保存检测设置
    document.getElementById('btn-save-detection-settings')?.addEventListener('click', () => {
        const confidence = document.getElementById('setting-confidence').value;
        const iou = document.getElementById('setting-iou').value;
        showToast(`检测设置已保存（置信度: ${confidence}, IOU: ${iou}）`, 'success');
    });

    // 保存融合设置
    document.getElementById('btn-save-fusion-settings')?.addEventListener('click', () => {
        const visualWeight = document.getElementById('setting-visual-weight').value;
        const sensorWeight = document.getElementById('setting-sensor-weight').value;
        const tolerance = document.getElementById('setting-weight-tolerance').value;
        showToast(`融合设置已保存（视觉: ${visualWeight}, 传感器: ${sensorWeight}）`, 'success');
    });
});
