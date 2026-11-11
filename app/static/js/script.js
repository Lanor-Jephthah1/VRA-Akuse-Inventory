function toggleMobileMenu(open) {
  const sidebar = document.getElementById('appSidebar');
  const backdrop = document.getElementById('mobileSidebarBackdrop');
  if (open) {
    sidebar.classList.remove('-translate-x-full');
    backdrop.classList.remove('hidden');
  } else {
    sidebar.classList.add('-translate-x-full');
    backdrop.classList.add('hidden');
  }
}

// Smooth numeric counter animation for KPI metrics
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-count]').forEach(el => {
    const target = parseInt(el.getAttribute('data-count'), 10);
    if (isNaN(target) || target === 0) return;
    let current = 0;
    const step = Math.max(1, Math.ceil(target / 18));
    const timer = setInterval(() => {
      current += step;
      if (current >= target) {
        el.textContent = target;
        clearInterval(timer);
      } else {
        el.textContent = current;
      }
    }, 20);
  });
});

// Global Modal Centering & Viewport Lock Helper
function relocateModalsToBody() {
  let anyOpen = false;
  document.querySelectorAll('[id$="Modal"]').forEach(modal => {
    if (modal.parentNode !== document.body) {
      document.body.appendChild(modal);
    }
    if (!modal.classList.contains('hidden')) {
      anyOpen = true;
      modal.scrollTop = 0;
    }
  });
  if (anyOpen) {
    document.body.style.overflow = 'hidden';
  }
}
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', relocateModalsToBody);
} else {
  relocateModalsToBody();
}
window.addEventListener('load', relocateModalsToBody);

function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;
  if (modal.parentNode !== document.body) {
    document.body.appendChild(modal);
  }
  modal.classList.remove('hidden');
  document.body.style.overflow = 'hidden';
  modal.scrollTop = 0;
  const innerScroll = modal.querySelector('.overflow-y-auto');
  if (innerScroll) innerScroll.scrollTop = 0;
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add('hidden');
  const anyOpen = Array.from(document.querySelectorAll('[id$="Modal"]')).some(m => !m.classList.contains('hidden'));
  if (!anyOpen) {
    document.body.style.overflow = '';
  }
  closeCustomDropdown();
}

// Close any open modal on Escape key or clicking the dark backdrop
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('[id$="Modal"]').forEach(m => closeModal(m.id));
  }
});
document.addEventListener('click', (e) => {
  if (e.target && e.target.id && e.target.id.endsWith('Modal')) {
    closeModal(e.target.id);
  }
});

// Compact Custom Dropdown Enhancer (prevents oversized mobile OS native select pickers)
let activeDropdownMenu = null;
let activeDropdownBtn = null;

function closeCustomDropdown() {
  if (activeDropdownMenu) {
    activeDropdownMenu.remove();
    activeDropdownMenu = null;
  }
  if (activeDropdownBtn) {
    const icon = activeDropdownBtn.querySelector('.dd-chevron');
    if (icon) icon.classList.remove('rotate-180');
    activeDropdownBtn = null;
  }
}

function initCustomSelects() {
  document.querySelectorAll('select:not([data-custom-select])').forEach(select => {
    select.setAttribute('data-custom-select', 'true');
    const isFullWidth = select.classList.contains('w-full');
    const heightClass = select.classList.contains('h-7') ? 'h-7' : (select.classList.contains('h-9') ? 'h-9' : 'h-8');
    const bgClass = select.classList.contains('bg-slate-50') ? 'bg-slate-50 hover:bg-slate-100/80' : 'bg-white hover:bg-slate-50/80';

    select.classList.add('sr-only');
    select.setAttribute('tabindex', '-1');

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = `${isFullWidth ? 'w-full' : 'inline-flex min-w-[130px] max-w-full'} ${heightClass} ${bgClass} rounded-md border border-slate-200 px-2.5 text-xs text-slate-700 flex items-center justify-between gap-2 text-left focus:outline-none focus:border-[#00529B] focus:ring-2 focus:ring-[#00529B]/10 transition-all`;

    const labelSpan = document.createElement('span');
    labelSpan.className = 'truncate block';
    const updateBtnLabel = () => {
      const selOpt = select.options[select.selectedIndex];
      labelSpan.textContent = selOpt ? selOpt.textContent.trim() : 'Select...';
    };
    updateBtnLabel();

    const chevron = document.createElement('span');
    chevron.className = 'dd-chevron text-slate-400 shrink-0 transition-transform duration-150';
    chevron.innerHTML = `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>`;

    btn.appendChild(labelSpan);
    btn.appendChild(chevron);
    select.parentNode.insertBefore(btn, select.nextSibling);

    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (activeDropdownBtn === btn) {
        closeCustomDropdown();
        return;
      }
      closeCustomDropdown();
      activeDropdownBtn = btn;
      chevron.classList.add('rotate-180');

      const rect = btn.getBoundingClientRect();
      const menu = document.createElement('div');
      menu.className = 'fixed z-[100050] bg-white border border-slate-200 rounded-lg shadow-2xl py-1 pb-3 text-xs overflow-y-auto ring-1 ring-slate-900/10';

      const menuWidth = Math.min(Math.max(rect.width, 210), window.innerWidth - 20);
      let leftPos = rect.left;
      if (leftPos + menuWidth > window.innerWidth - 10) {
        leftPos = Math.max(10, window.innerWidth - menuWidth - 10);
      }
      menu.style.width = `${menuWidth}px`;
      menu.style.left = `${leftPos}px`;

      const spaceBelow = window.innerHeight - rect.bottom - 16;
      const spaceAbove = rect.top - 16;

      if (spaceBelow < 180 && spaceAbove > spaceBelow) {
        menu.style.bottom = `${window.innerHeight - rect.top + 4}px`;
        menu.style.maxHeight = `${Math.max(120, Math.min(spaceAbove, 260))}px`;
      } else {
        menu.style.top = `${rect.bottom + 4}px`;
        menu.style.maxHeight = `${Math.max(120, Math.min(spaceBelow, 260))}px`;
      }

      Array.from(select.options).forEach((opt, idx) => {
        const item = document.createElement('button');
        item.type = 'button';
        const isSelected = idx === select.selectedIndex;
        item.className = `w-full px-3 py-2 text-left flex items-center justify-between gap-2 transition-colors ${isSelected ? 'bg-slate-100/90 font-semibold text-[#00529B]' : 'text-slate-700 hover:bg-slate-50'}`;
        item.innerHTML = `<span class="leading-snug break-words">${opt.textContent.trim()}</span>` +
          (isSelected ? `<svg class="w-3.5 h-3.5 text-[#00529B] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.2" d="M5 13l4 4L19 7"/></svg>` : '');

        item.addEventListener('click', (ev) => {
          ev.stopPropagation();
          select.selectedIndex = idx;
          select.value = opt.value;
          updateBtnLabel();
          closeCustomDropdown();
          select.dispatchEvent(new Event('change', { bubbles: true }));
        });
        menu.appendChild(item);
      });

      document.body.appendChild(menu);
      activeDropdownMenu = menu;
    });
  });
}

document.addEventListener('DOMContentLoaded', initCustomSelects);
document.addEventListener('click', closeCustomDropdown);
window.addEventListener('resize', closeCustomDropdown);
window.addEventListener('scroll', (e) => {
  if (activeDropdownMenu && !activeDropdownMenu.contains(e.target)) {
    closeCustomDropdown();
  }
}, true);

function printVoucher() {
  window.print();
}

// Personnel Directory Filtering, Sorting, and Client Pagination
function filterPersonnelByDept(deptCode) {
  const deptSelect = document.getElementById('personnelDeptFilter');
  if (deptSelect) {
    deptSelect.value = deptCode;
    deptSelect.dispatchEvent(new Event('change'));
    const dirEl = document.getElementById('personnelDirectorySection');
    if (dirEl) {
      dirEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }
}

function initPersonnelDirectory() {
  const table = document.getElementById('personnelTable');
  if (!table) return;

  const searchInput = document.getElementById('personnelSearch');
  const deptFilter = document.getElementById('personnelDeptFilter');
  const roleFilter = document.getElementById('personnelRoleFilter');
  const sortSelect = document.getElementById('personnelSort');
  const pageSizeSelect = document.getElementById('personnelPageSize');
  const prevBtn = document.getElementById('personnelPrevBtn');
  const nextBtn = document.getElementById('personnelNextBtn');
  const pageIndicator = document.getElementById('personnelPageIndicator');
  const countDisplay = document.getElementById('personnelCountDisplay');
  const emptyRow = document.getElementById('personnelEmptyRow');

  const rows = Array.from(table.querySelectorAll('tbody tr.personnel-row'));
  let currentPage = 1;

  function updateDirectory() {
    const query = (searchInput?.value || '').trim().toLowerCase();
    const selectedDept = deptFilter?.value || 'ALL';
    const selectedRole = roleFilter?.value || 'ALL';
    const sortBy = sortSelect?.value || 'name-asc';
    const pageSize = pageSizeSelect?.value === 'ALL' ? 999999 : parseInt(pageSizeSelect?.value || '8', 10);

    // 1. Filter rows
    let visibleRows = rows.filter(row => {
      const name = row.getAttribute('data-name') || '';
      const staffId = row.getAttribute('data-staff-id') || '';
      const title = row.getAttribute('data-title') || '';
      const email = row.getAttribute('data-email') || '';
      const dept = row.getAttribute('data-dept') || '';
      const role = row.getAttribute('data-role') || '';

      const matchesQuery = !query || name.includes(query) || staffId.includes(query) || title.includes(query) || email.includes(query);
      const matchesDept = selectedDept === 'ALL' || dept === selectedDept;
      const matchesRole = selectedRole === 'ALL' || role === selectedRole;

      return matchesQuery && matchesDept && matchesRole;
    });

    // 2. Sort visible rows
    visibleRows.sort((a, b) => {
      if (sortBy === 'name-asc') {
        return (a.getAttribute('data-name') || '').localeCompare(b.getAttribute('data-name') || '');
      } else if (sortBy === 'name-desc') {
        return (b.getAttribute('data-name') || '').localeCompare(a.getAttribute('data-name') || '');
      } else if (sortBy === 'id-asc') {
        return (a.getAttribute('data-staff-id') || '').localeCompare(b.getAttribute('data-staff-id') || '');
      } else if (sortBy === 'dept-asc') {
        return (a.getAttribute('data-dept') || '').localeCompare(b.getAttribute('data-dept') || '');
      } else if (sortBy === 'role-asc') {
        return (a.getAttribute('data-role') || '').localeCompare(b.getAttribute('data-role') || '');
      }
      return 0;
    });

    // Re-append sorted rows in order
    const tbody = table.querySelector('tbody');
    visibleRows.forEach(row => tbody.appendChild(row));
    if (emptyRow) tbody.appendChild(emptyRow);

    // 3. Paginate
    const totalVisible = visibleRows.length;
    const totalPages = Math.max(1, Math.ceil(totalVisible / pageSize));
    if (currentPage > totalPages) currentPage = totalPages;
    if (currentPage < 1) currentPage = 1;

    const startIdx = (currentPage - 1) * pageSize;
    const endIdx = startIdx + pageSize;

    rows.forEach(r => r.style.display = 'none');
    visibleRows.slice(startIdx, endIdx).forEach(r => r.style.display = '');

    if (emptyRow) {
      emptyRow.style.display = totalVisible === 0 ? '' : 'none';
    }

    // 4. Update UI labels
    if (countDisplay) {
      if (totalVisible === 0) {
        countDisplay.textContent = '0 personnel';
      } else {
        const displayStart = startIdx + 1;
        const displayEnd = Math.min(endIdx, totalVisible);
        countDisplay.textContent = `Showing ${displayStart}–${displayEnd} of ${totalVisible} personnel`;
      }
    }

    if (pageIndicator) {
      pageIndicator.textContent = `Page ${currentPage} of ${totalPages}`;
    }

    if (prevBtn) {
      prevBtn.disabled = currentPage <= 1;
      prevBtn.classList.toggle('opacity-40', currentPage <= 1);
      prevBtn.classList.toggle('cursor-not-allowed', currentPage <= 1);
    }

    if (nextBtn) {
      nextBtn.disabled = currentPage >= totalPages;
      nextBtn.classList.toggle('opacity-40', currentPage >= totalPages);
      nextBtn.classList.toggle('cursor-not-allowed', currentPage >= totalPages);
    }
  }

  searchInput?.addEventListener('input', () => { currentPage = 1; updateDirectory(); });
  deptFilter?.addEventListener('change', () => { currentPage = 1; updateDirectory(); });
  roleFilter?.addEventListener('change', () => { currentPage = 1; updateDirectory(); });
  sortSelect?.addEventListener('change', () => { currentPage = 1; updateDirectory(); });
  pageSizeSelect?.addEventListener('change', () => { currentPage = 1; updateDirectory(); });

  prevBtn?.addEventListener('click', () => {
    if (currentPage > 1) {
      currentPage--;
      updateDirectory();
    }
  });

  nextBtn?.addEventListener('click', () => {
    currentPage++;
    updateDirectory();
  });

  updateDirectory();
}

document.addEventListener('DOMContentLoaded', initPersonnelDirectory);

// Dynamic Multi-Item Requisition Builder
function toggleReturnDateField(checkbox) {
  const container = document.getElementById('expectedReturnDateContainer');
  if (container) {
    if (checkbox.checked) {
      container.classList.remove('hidden');
    } else {
      container.classList.add('hidden');
    }
  }
}

function updateRequisitionItemsSummary() {
  const container = document.getElementById('requisitionItemsContainer');
  const summary = document.getElementById('requisitionItemsSummary');
  if (!container || !summary) return;
  const rows = container.querySelectorAll('.requisition-item-row');
  const count = rows.length;
  summary.textContent = `${count} ${count === 1 ? 'item' : 'items'} in this requisition`;
}

function addRequisitionItemRow() {
  const container = document.getElementById('requisitionItemsContainer');
  const template = document.getElementById('requisitionRowTemplate');
  if (!container || !template) return;
  const clone = template.content.cloneNode(true);
  container.appendChild(clone);
  if (typeof initCustomSelects === 'function') {
    initCustomSelects();
  }
  updateRequisitionItemsSummary();
  const newRow = container.lastElementChild;
  if (newRow) {
    const input = newRow.querySelector('input[name="quantities"]');
    if (input) validateRequisitionRow(input);
  }
}

function removeRequisitionItemRow(btn) {
  const container = document.getElementById('requisitionItemsContainer');
  if (!container) return;
  const rows = container.querySelectorAll('.requisition-item-row');
  if (rows.length <= 1) {
    alert('A requisition must contain at least one item.');
    return;
  }
  const row = btn.closest('.requisition-item-row');
  if (row) {
    row.remove();
    updateRequisitionItemsSummary();
    updateRequisitionFormSubmitState();
  }
}

// Real-time Quantity & Stock Limit Validator & Message Box
function validateRequisitionRow(el) {
  const row = el.closest('.requisition-item-row');
  if (!row) return;

  const select = row.querySelector('select[name="item_ids"]');
  const qtyInput = row.querySelector('input[name="quantities"]');
  const feedback = row.querySelector('.req-row-feedback');
  if (!select || !qtyInput || !feedback) return;

  const selectedOpt = select.options[select.selectedIndex];
  if (!selectedOpt) return;

  const stock = parseInt(selectedOpt.getAttribute('data-stock') || '0', 10);
  const unit = selectedOpt.getAttribute('data-unit') || 'units';
  const code = selectedOpt.getAttribute('data-code') || '';
  const rawVal = qtyInput.value;
  const qty = parseInt(rawVal, 10);

  qtyInput.setAttribute('max', stock);

  // Check state
  if (isNaN(qty) || rawVal === '' || qty < 1) {
    qtyInput.classList.add('border-amber-400', 'focus:ring-amber-200');
    qtyInput.classList.remove('border-rose-500', 'text-rose-700', 'bg-rose-50/30', 'border-slate-300');
    feedback.className = 'req-row-feedback text-[11px] p-2 rounded-md bg-amber-50 border border-amber-200 text-amber-800 flex items-center gap-1.5';
    feedback.innerHTML = `<svg class="w-3.5 h-3.5 text-amber-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg><span>Please enter a requested quantity of 1 or more (Max available: <strong>${stock} ${unit}</strong>).</span>`;
    feedback.classList.remove('hidden');
  } else if (qty > stock) {
    // EXCEEDS STOCK! (The user's exact issue shown in screenshot)
    qtyInput.classList.add('border-rose-500', 'text-rose-700', 'bg-rose-50/30', 'focus:ring-rose-200');
    qtyInput.classList.remove('border-slate-300', 'border-amber-400');
    feedback.className = 'req-row-feedback text-[11px] p-2 rounded-md bg-rose-50 border border-rose-200 text-rose-800 flex items-start gap-2';
    feedback.innerHTML = `<svg class="w-4 h-4 text-rose-600 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg><div><span class="font-semibold">Insufficient Store Stock:</span> You entered <strong>${qty} ${unit}</strong>, but only <strong>${stock} ${unit}</strong> are currently available in stores for <em>${code}</em>. Please enter <strong>${stock}</strong> or fewer.</div>`;
    feedback.classList.remove('hidden');
  } else {
    // Valid quantity within stock limit
    qtyInput.classList.remove('border-rose-500', 'text-rose-700', 'bg-rose-50/30', 'border-amber-400');
    qtyInput.classList.add('border-slate-300');
    const remaining = stock - qty;
    feedback.className = 'req-row-feedback text-[11px] px-2.5 py-1.5 rounded-md bg-slate-100 text-slate-700 border border-slate-200 flex items-center gap-1.5';
    feedback.innerHTML = `<svg class="w-3.5 h-3.5 text-emerald-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.2" d="M5 13l4 4L19 7"/></svg><span>Available in store: <strong>${stock} ${unit}</strong> (${remaining} ${unit} will remain in store).</span>`;
    feedback.classList.remove('hidden');
  }

  updateRequisitionFormSubmitState();
}

function updateRequisitionFormSubmitState() {
  const container = document.getElementById('requisitionItemsContainer');
  const submitBtn = document.getElementById('submitReqBtn');
  if (!container || !submitBtn) return;

  const rows = container.querySelectorAll('.requisition-item-row');
  let hasError = false;

  rows.forEach(r => {
    const select = r.querySelector('select[name="item_ids"]');
    const qtyInput = r.querySelector('input[name="quantities"]');
    if (select && qtyInput) {
      const selectedOpt = select.options[select.selectedIndex];
      const stock = parseInt(selectedOpt?.getAttribute('data-stock') || '0', 10);
      const qty = parseInt(qtyInput.value || '0', 10);
      if (isNaN(qty) || qty < 1 || qty > stock) {
        hasError = true;
      }
    }
  });

  if (hasError) {
    submitBtn.disabled = true;
    submitBtn.classList.add('opacity-50', 'cursor-not-allowed', 'pointer-events-none');
    submitBtn.title = 'Please adjust requested quantity to available stock limit';
  } else {
    submitBtn.disabled = false;
    submitBtn.classList.remove('opacity-50', 'cursor-not-allowed', 'pointer-events-none');
    submitBtn.title = '';
  }
}

// Initialise row validation on modal open
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('#requisitionItemsContainer .requisition-item-row').forEach(row => {
    const input = row.querySelector('input[name="quantities"]');
    if (input) validateRequisitionRow(input);
  });
});