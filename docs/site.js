/* Progressive enhancement for the static site. No form data is posted or stored. */
(() => {
  'use strict';

  const menu = document.querySelector('.menu-toggle');
  const navigation = document.querySelector('#primary-navigation');
  if (menu && navigation) {
    const setMenu = (open) => menu.setAttribute('aria-expanded', String(open));
    menu.addEventListener('click', () => setMenu(menu.getAttribute('aria-expanded') !== 'true'));
    navigation.addEventListener('click', (event) => {
      if (event.target.closest('a')) setMenu(false);
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && menu.getAttribute('aria-expanded') === 'true') {
        setMenu(false);
        menu.focus();
      }
    });
    document.addEventListener('click', (event) => {
      if (!event.target.closest('header')) setMenu(false);
    });
    menu.hidden = false;
    document.querySelector('header').classList.add('nav-ready');
  }

  const form = document.querySelector('[data-request-form]');
  if (!form) return;
  const result = document.querySelector('.request-result');
  const preparedRequest = result.querySelector('textarea');
  const emailDraft = result.querySelector('.email-draft');
  const copyStatus = result.querySelector('.copy-status');
  const isProject = form.dataset.requestForm === 'project';

  // Prefill only recognized service choices; never inject URL content into the page.
  if (isProject) {
    const service = new URLSearchParams(window.location.search).get('service');
    if (['documents', 'pdf', 'data', 'research', 'other'].includes(service)) {
      form.elements.service.value = service;
    }
  }

  const date = form.elements.date;
  const today = new Date();
  date.min = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;

  form.querySelectorAll('[required]').forEach((input) => {
    input.addEventListener('input', () => {
      input.setCustomValidity(input.value.trim() ? '' : 'Please complete this field.');
    });
  });

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    form.querySelectorAll('[required]').forEach((input) => {
      input.setCustomValidity(input.value.trim() ? '' : 'Please complete this field.');
    });
    if (!form.reportValidity()) return;
    const value = (name, fallback = 'Not provided') => form.elements[name].value.trim() || fallback;
    const subject = isProject ? 'Project quote request — CincyDocs' : 'Notary appointment request — CincyDocs';
    const lines = [
      subject,
      '',
      `Name: ${value('name')}`,
      `Reply email: ${value('email')}`,
    ];
    if (isProject) {
      lines.push(
        `Business / organization: ${value('organization')}`,
        `Service: ${form.elements.service.selectedOptions[0].textContent.trim()}`,
        `Desired completion date: ${value('date', 'Flexible / to be agreed')}`,
        `File count / dataset size: ${value('size')}`,
        '',
        'Project description:',
      );
    } else {
      lines.push(
        `Phone: ${value('phone')}`,
        `Appointment area / ZIP: ${value('location')}`,
        `Preferred date: ${value('date', 'Flexible / to be agreed')}`,
        `Preferred time: ${value('time', 'Flexible / to be agreed')}`,
        `General document type: ${value('document_type')}`,
        `Number of signers: ${value('signers', 'Not known')}`,
        '',
        'Additional appointment information:',
      );
    }
    lines.push(value('description'), '', 'Please reply to discuss scope, requirements, price, and availability.');
    const body = lines.join('\n').replace(/\r?\n/g, '\r\n');
    // encodeURIComponent keeps ampersands, newlines, and user text inside the email body.
    emailDraft.href = `mailto:hello@cincydocs.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    preparedRequest.value = body;
    copyStatus.textContent = '';
    result.hidden = false;
    result.querySelector('h3').focus();
  });

  result.querySelector('.copy-request').addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(preparedRequest.value);
      copyStatus.textContent = 'Request copied. Paste it into an email to hello@cincydocs.com, then send it.';
    } catch {
      preparedRequest.focus();
      preparedRequest.select();
      copyStatus.textContent = 'Automatic copy is unavailable. The request text is selected; use your device’s Copy command, then paste it into an email to hello@cincydocs.com.';
    }
  });
  form.hidden = false;
})();
