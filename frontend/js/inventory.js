// 库存管理页面逻辑
async function loadInventory() {
    try {
        const items = await apiRequest('/inventory?limit=100');
        renderInventoryTable(items);
    } catch (e) {
        console.error('加载库存失败:', e);
    }
}

function renderInventoryTable(items) {
    const tbody = document.getElementById('inventory-body');
    if (!items || items.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="empty-state">暂无库存数据</td></tr>';
        return;
    }

    tbody.innerHTML = items.map(item => {
        const isLow = item.quantity <= item.min_stock;
        const isHigh = item.quantity >= item.max_stock;
        let statusBadge = '<span class="badge badge-normal">正常</span>';
        if (isLow) statusBadge = '<span class="badge badge-warning">库存不足</span>';
        if (isHigh) statusBadge = '<span class="badge badge-info">库存充足</span>';

        return `
            <tr>
                <td>${item.id}</td>
                <td>${item.class_id}</td>
                <td>${item.class_name}</td>
                <td><strong>${item.quantity}</strong></td>
                <td>${item.location || '-'}</td>
                <td>${item.min_stock}</td>
                <td>${item.max_stock}</td>
                <td>${statusBadge}</td>
                <td>
                    <button class="btn btn-sm" onclick="showInboundModal(${item.id})">入库</button>
                    <button class="btn btn-sm" onclick="showOutboundModal(${item.id})">出库</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteInventory(${item.id})">删除</button>
                </td>
            </tr>
        `;
    }).join('');
}

function showInboundModal(itemId) {
    showModal('入库操作', `
        <div class="form-group">
            <label>入库数量</label>
            <input type="number" class="form-input" id="inbound-quantity" value="1" min="1">
        </div>
    `, [
        { text: '取消', class: '', onClick: closeModal },
        { text: '确认入库', class: 'btn-primary', onClick: () => {
            const qty = parseInt(document.getElementById('inbound-quantity').value);
            if (qty > 0) {
                performInbound(itemId, qty);
            } else {
                showToast('请输入有效数量', 'warning');
            }
        }}
    ]);
}

async function performInbound(itemId, quantity) {
    try {
        await apiRequest(`/inventory/${itemId}/inbound?quantity=${quantity}`, { method: 'POST' });
        closeModal();
        showToast(`入库 ${quantity} 件成功`, 'success');
        loadInventory();
    } catch (e) {
        showToast('入库失败', 'error');
    }
}

function showOutboundModal(itemId) {
    showModal('出库操作', `
        <div class="form-group">
            <label>出库数量</label>
            <input type="number" class="form-input" id="outbound-quantity" value="1" min="1">
        </div>
    `, [
        { text: '取消', class: '', onClick: closeModal },
        { text: '确认出库', class: 'btn-primary', onClick: () => {
            const qty = parseInt(document.getElementById('outbound-quantity').value);
            if (qty > 0) {
                performOutbound(itemId, qty);
            } else {
                showToast('请输入有效数量', 'warning');
            }
        }}
    ]);
}

async function performOutbound(itemId, quantity) {
    try {
        await apiRequest(`/inventory/${itemId}/outbound?quantity=${quantity}`, { method: 'POST' });
        closeModal();
        showToast(`出库 ${quantity} 件成功`, 'success');
        loadInventory();
    } catch (e) {
        showToast('出库失败', 'error');
    }
}

async function deleteInventory(itemId) {
    if (!confirm('确定要删除该库存项吗？')) return;
    try {
        await apiRequest(`/inventory/${itemId}`, { method: 'DELETE' });
        showToast('删除成功', 'success');
        loadInventory();
    } catch (e) {
        showToast('删除失败', 'error');
    }
}
