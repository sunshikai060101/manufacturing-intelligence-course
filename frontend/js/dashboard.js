// 仪表盘逻辑
async function loadDashboard() {
    try {
        const stats = await apiRequest('/stats/dashboard');

        // 更新统计卡片
        document.getElementById('stat-total-detections').textContent = stats.total_detections;
        document.getElementById('stat-today-detections').textContent = stats.today_detections;
        document.getElementById('stat-total-inventory').textContent = stats.total_inventory;
        document.getElementById('stat-anomaly-count').textContent = stats.anomaly_count;
        document.getElementById('stat-pass-rate').textContent = stats.pass_rate + '%';

        // 类别分布
        renderClassDistribution(stats.class_distribution);

        // 最近记录
        renderRecentRecords(stats.recent_detections);

        // 趋势图
        loadTrendChart();
    } catch (e) {
        console.error('加载仪表盘失败:', e);
    }
}

function renderClassDistribution(classStats) {
    const container = document.getElementById('class-distribution');
    if (!classStats || classStats.length === 0) {
        container.innerHTML = '<div class="empty-state">暂无数据</div>';
        return;
    }

    const maxCount = Math.max(...classStats.map(c => c.count), 1);
    const colors = ['#2563eb', '#16a34a', '#ea580c', '#dc2626', '#0d9488', '#7c3aed'];

    container.innerHTML = classStats.map((c, i) => `
        <div class="class-bar-item">
            <div class="class-bar-label">${c.class_name_cn}</div>
            <div class="class-bar-track">
                <div class="class-bar-fill" style="width: ${(c.count / maxCount * 100).toFixed(1)}%; background: ${colors[i % colors.length]};"></div>
            </div>
            <div class="class-bar-value">${c.count}</div>
        </div>
    `).join('');
}

function renderRecentRecords(records) {
    const tbody = document.getElementById('recent-records-body');
    if (!records || records.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="empty-state">暂无检测记录</td></tr>';
        return;
    }

    tbody.innerHTML = records.map(r => `
        <tr>
            <td>${r.id}</td>
            <td>${r.image_name.substring(0, 20)}${r.image_name.length > 20 ? '...' : ''}</td>
            <td>${r.class_name}</td>
            <td>${(r.confidence * 100).toFixed(1)}%</td>
            <td>${getFusionBadge(r.fusion_result)}</td>
            <td>${r.is_anomaly ? '<span class="badge badge-anomaly">异常</span>' : '<span class="badge badge-normal">正常</span>'}</td>
            <td>${getSortBadge(r.sort_status)}</td>
            <td>${formatTime(r.created_at)}</td>
        </tr>
    `).join('');
}

async function loadTrendChart() {
    try {
        const data = await apiRequest('/stats/trend?days=7');
        const canvas = document.getElementById('trend-chart');
        const ctx = canvas.getContext('2d');

        // 清空画布
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const chartData = data.data;
        if (!chartData || chartData.length === 0) return;

        const padding = { top: 20, right: 20, bottom: 40, left: 50 };
        const chartWidth = canvas.width - padding.left - padding.right;
        const chartHeight = canvas.height - padding.top - padding.bottom;

        const maxVal = Math.max(...chartData.map(d => d.total), 1);

        // 绘制网格线
        ctx.strokeStyle = '#e2e8f0';
        ctx.lineWidth = 1;
        for (let i = 0; i <= 4; i++) {
            const y = padding.top + (chartHeight / 4) * i;
            ctx.beginPath();
            ctx.moveTo(padding.left, y);
            ctx.lineTo(canvas.width - padding.right, y);
            ctx.stroke();

            // Y轴标签
            ctx.fillStyle = '#64748b';
            ctx.font = '11px sans-serif';
            ctx.textAlign = 'right';
            ctx.fillText(Math.round(maxVal * (1 - i / 4)), padding.left - 8, y + 4);
        }

        // 绘制柱状图
        const barWidth = chartWidth / chartData.length * 0.6;
        const barGap = chartWidth / chartData.length * 0.4;

        chartData.forEach((d, i) => {
            const x = padding.left + i * (barWidth + barGap) + barGap / 2;
            const barHeight = (d.total / maxVal) * chartHeight;
            const y = padding.top + chartHeight - barHeight;

            // 柱子
            const gradient = ctx.createLinearGradient(x, y, x, y + barHeight);
            gradient.addColorStop(0, '#3b82f6');
            gradient.addColorStop(1, '#2563eb');
            ctx.fillStyle = gradient;
            ctx.fillRect(x, y, barWidth, barHeight);

            // 数值标签
            ctx.fillStyle = '#1e293b';
            ctx.font = 'bold 11px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(d.total, x + barWidth / 2, y - 6);

            // X轴标签
            ctx.fillStyle = '#64748b';
            ctx.font = '10px sans-serif';
            const dateLabel = d.date.substring(5); // MM-DD
            ctx.fillText(dateLabel, x + barWidth / 2, canvas.height - padding.bottom + 16);
        });

        // X轴标题
        ctx.fillStyle = '#64748b';
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('日期', canvas.width / 2, canvas.height - 5);

        // Y轴标题
        ctx.save();
        ctx.translate(12, canvas.height / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText('检测次数', 0, 0);
        ctx.restore();
    } catch (e) {
        console.error('加载趋势图失败:', e);
    }
}
