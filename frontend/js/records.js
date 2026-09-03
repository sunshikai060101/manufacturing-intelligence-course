// 检测记录页面逻辑
async function loadRecords() {
    try {
        const classFilter = document.getElementById('record-class-filter')?.value;
        const fusionFilter = document.getElementById('record-fusion-filter')?.value;

        let url = `/detection/records?skip=${(AppState.recordsPage - 1) * AppState.recordsPerPage}&limit=${AppState.recordsPerPage}`;
        if (classFilter) url += `&class_id=${classFilter}`;
        if (fusionFilter) url += `&fusion_result=${fusionFilter}`;

        const records = await apiRequest(url);
        renderRecordsTable(records);

        document.getElementById('page-info').textContent = `第 ${AppState.recordsPage} 页`;
    } catch (e) {
        console.error('加载检测记录失败:', e);
    }
}

function renderRecordsTable(records) {
    const tbody = document.getElementById('records-body');
    if (!records || records.length === 0) {
        tbody.innerHTML = '<tr><td colspan="11" class="empty-state">暂无检测记录</td></tr>';
        return;
    }

    tbody.innerHTML = records.map(r => `
        <tr>
            <td>${r.id}</td>
            <td title="${r.image_name}">${r.image_name.substring(0, 15)}${r.image_name.length > 15 ? '...' : ''}</td>
            <td>${r.class_name}</td>
            <td>${(r.confidence * 100).toFixed(1)}%</td>
            <td>${getFusionBadge(r.fusion_result)}</td>
            <td>${r.fusion_confidence ? (r.fusion_confidence * 100).toFixed(1) + '%' : '-'}</td>
            <td>${r.is_anomaly ? '<span class="badge badge-anomaly">是</span>' : '<span class="badge badge-normal">否</span>'}</td>
            <td>${r.anomaly_score ? (r.anomaly_score * 100).toFixed(1) + '%' : '-'}</td>
            <td>${getSortBadge(r.sort_status)}</td>
            <td>${formatTime(r.created_at)}</td>
            <td>
                <select class="form-select" style="width: auto; padding: 2px 6px; font-size: 11px;"
                        onchange="updateSortStatus(${r.id}, this.value)">
                    <option value="pending" ${r.sort_status === 'pending' ? 'selected' : ''}>待分拣</option>
                    <option value="sorting" ${r.sort_status === 'sorting' ? 'selected' : ''}>分拣中</option>
                    <option value="sorted" ${r.sort_status === 'sorted' ? 'selected' : ''}>已分拣</option>
                    <option value="failed" ${r.sort_status === 'failed' ? 'selected' : ''}>失败</option>
                </select>
                <button class="btn btn-sm btn-danger" onclick="deleteRecord(${r.id})" style="margin-top:4px;">删除</button>
            </td>
        </tr>
    `).join('');
}

async function updateSortStatus(recordId, status) {
    try {
        await apiRequest(`/detection/records/${recordId}/sort?status=${status}`, { method: 'PUT' });
        showToast(`分拣状态已更新`, 'success');
    } catch (e) {
        showToast('更新失败', 'error');
        loadRecords();
    }
}

async function deleteRecord(recordId) {
    if (!confirm('确定要删除该记录吗？')) return;
    try {
        await apiRequest(`/detection/records/${recordId}`, { method: 'DELETE' });
        showToast('删除成功', 'success');
        loadRecords();
    } catch (e) {
        showToast('删除失败', 'error');
    }
}

// 分页
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('btn-prev-page')?.addEventListener('click', () => {
        if (AppState.recordsPage > 1) {
            AppState.recordsPage--;
            loadRecords();
        }
    });

    document.getElementById('btn-next-page')?.addEventListener('click', () => {
        AppState.recordsPage++;
        loadRecords();
    });

    document.getElementById('record-class-filter')?.addEventListener('change', () => {
        AppState.recordsPage = 1;
        loadRecords();
    });

    document.getElementById('record-fusion-filter')?.addEventListener('change', () => {
        AppState.recordsPage = 1;
        loadRecords();
    });
});
