let currentMode = 'STAFF';
let activeDropdownMenu = null;
let activeDropdownBtn = null;
let updateCustomSelectLabel = null;
let allDemoAccounts = [];

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

function setLoginMode(mode) {
  currentMode = mode;
  const modeInput = document.getElementById('loginModeInput');
  if (modeInput) modeInput.value = mode;
  const tabStaff = document.getElementById('tabStaff');
  const tabSupervisor = document.getElementById('tabSupervisor');
  const identifierInput = document.getElementById('identifierInput');

  if (tabStaff && tabSupervisor && identifierInput) {
    if (mode === 'SUPERVISOR') {
      tabSupervisor.className = 'h-8 rounded text-xs font-semibold bg-white text-[#00529B] shadow-sm border border-slate-200/80 transition-all';
      tabStaff.className = 'h-8 rounded text-xs font-medium text-slate-600 hover:text-slate-900 transition-all';
      identifierInput.placeholder = 'e.g. VRA-AK-1004';
    } else {
      tabStaff.className = 'h-8 rounded text-xs font-semibold bg-white text-[#00529B] shadow-sm border border-slate-200/80 transition-all';
      tabSupervisor.className = 'h-8 rounded text-xs font-medium text-slate-600 hover:text-slate-900 transition-all';
      identifierInput.placeholder = 'e.g. VRA-AK-3041';
    }
  }

  // Filter demo dropdown options to match selected login tab
  const select = document.getElementById('quickDemoSelect');
  if (select) {
    select.innerHTML = '';
    const placeholderOpt = document.createElement('option');
    placeholderOpt.value = '';
    placeholderOpt.textContent = mode === 'SUPERVISOR'
      ? 'Select a Supervisor account...'
      : 'Select a Staff / Store account...';
    select.appendChild(placeholderOpt);

    allDemoAccounts
      .filter(a => mode === 'SUPERVISOR' ? a.role === 'SUPERVISOR' : a.role !== 'SUPERVISOR')
      .forEach(a => {
        const opt = document.createElement('option');
        opt.value = a.staffId;
        opt.textContent = `${a.name} (${a.dept} / ${a.roleLabel})`;
        select.appendChild(opt);
      });
  }

  closeCustomDropdown();
  if (updateCustomSelectLabel) updateCustomSelectLabel();
}

function fillLogin(staffId) {
  const idInput = document.getElementById('identifierInput');
  const pwdInput = document.getElementById('passwordInput');
  const form = document.getElementById('loginForm');
  if (idInput && pwdInput && form) {
    idInput.value = staffId;
    pwdInput.value = 'vra123';
    form.submit();
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const dataEl = document.getElementById('demoAccountsData');
  if (dataEl) {
    try {
      allDemoAccounts = JSON.parse(dataEl.textContent);
    } catch (e) {
      console.error('Error parsing demo accounts data', e);
    }
  }

  const modeAttr = document.body.getAttribute('data-login-mode');
  if (modeAttr) currentMode = modeAttr;

  const select = document.getElementById('quickDemoSelect');
  if (!select) return;

  select.classList.add('sr-only');
  select.setAttribute('tabindex', '-1');

  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'w-full h-8 bg-slate-50 hover:bg-slate-100/80 rounded-md border border-slate-200 px-2.5 text-xs text-slate-600 flex items-center justify-between gap-2 text-left focus:outline-none focus:border-[#00529B] transition-all';

  const labelSpan = document.createElement('span');
  labelSpan.className = 'truncate block';
  updateCustomSelectLabel = () => {
    const selOpt = select.options[select.selectedIndex];
    labelSpan.textContent = selOpt ? selOpt.textContent.trim() : 'Select...';
  };

  const chevron = document.createElement('span');
  chevron.className = 'dd-chevron text-slate-400 shrink-0 transition-transform duration-150';
  chevron.innerHTML = `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>`;

  btn.appendChild(labelSpan);
  btn.appendChild(chevron);
  select.parentNode.insertBefore(btn, select.nextSibling);

  setLoginMode(currentMode);

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

    const menuWidth = Math.min(Math.max(rect.width, 220), window.innerWidth - 20);
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
      item.innerHTML = `<span class="leading-snug break-words">${opt.textContent.trim()}</span>`;
      item.addEventListener('click', (ev) => {
        ev.stopPropagation();
        select.selectedIndex = idx;
        select.value = opt.value;
        updateCustomSelectLabel();
        closeCustomDropdown();
        select.dispatchEvent(new Event('change', { bubbles: true }));
      });
      menu.appendChild(item);
    });

    document.body.appendChild(menu);
    activeDropdownMenu = menu;
  });
});

document.addEventListener('click', closeCustomDropdown);
window.addEventListener('resize', closeCustomDropdown);
