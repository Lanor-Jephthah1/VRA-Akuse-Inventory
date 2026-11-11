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
  document.querySelectorAll('[id$="Modal"]').forEach(modal => {
    if (modal.parentNode !== document.body) {
      document.body.appendChild(modal);
    }
  });
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
      menu.className = 'fixed z-[100] bg-white border border-slate-200 rounded-md shadow-lg py-1 text-xs max-h-56 overflow-y-auto';

      const menuWidth = Math.min(Math.max(rect.width, 190), window.innerWidth - 20);
      let leftPos = rect.left;
      if (leftPos + menuWidth > window.innerWidth - 10) {
        leftPos = Math.max(10, window.innerWidth - menuWidth - 10);
      }
      menu.style.width = `${menuWidth}px`;
      menu.style.left = `${leftPos}px`;

      const spaceBelow = window.innerHeight - rect.bottom;
      if (spaceBelow < 220 && rect.top > 220) {
        menu.style.bottom = `${window.innerHeight - rect.top + 4}px`;
      } else {
        menu.style.top = `${rect.bottom + 4}px`;
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