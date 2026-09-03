// 传感器数据页面逻辑
async function loadSensorData() {
    try {
        // 加载统计数据
        const stats = await apiRequest('/sensor/stats?sensor_type=weight&hours=24');
        document.getElementById('sensor-weight-mean').textContent = stats.mean.toFixed(2);
        document.getElementById('sensor-weight-max').textContent = stats.max.toFixed(2);
        document.getElementById('sensor-weight-min').textContent = stats.min.toFixed(2);
        document.getElementById('sensor-weight-std').textContent = stats.std.toFixed(2);

        // 加载数据列表
        const data = await apiRequest('/sensor?limit=100');
        renderSensorTable(data);
    } catch (e) {
        console.error('加载传感器数据失败:', e);
    }
}

function renderSensorTable(data) {
    const tbody = document.getElementById('sensor-body');
    if (!data || data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">暂无传感器数据</td></tr>';
        return;
    }

    const typeMap = {
        weight: '重量传感器',
        infrared: '红外传感器',
        photoelectric: '光电传感器',
    };

    tbody.innerHTML = data.map(item => `
        <tr>
            <td>${item.id}</td>
            <td><span class="badge badge-info">${typeMap[item.sensor_type] || item.sensor_type}</span></td>
            <td>${item.sensor_id}</td>
            <td><strong>${item.value}</strong></td>
            <td>${item.unit || '-'}</td>
            <td>${formatTime(item.created_at)}</td>
        </tr>
    `).join('');
}
