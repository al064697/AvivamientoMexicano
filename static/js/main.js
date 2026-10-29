const header = document.querySelector('.site-header');
const menuToggle = document.querySelector('.menu-toggle');
const registrationForm = document.querySelector('#registration-form');
const formMessage = document.querySelector('.form-message');

if (menuToggle && header) {
  menuToggle.addEventListener('click', () => {
    const isOpen = header.classList.toggle('menu-open');
    menuToggle.setAttribute('aria-expanded', String(isOpen));
    menuToggle.textContent = isOpen ? 'Cerrar' : 'Menu';
  });
}

if (registrationForm) {
  registrationForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const submitButton = registrationForm.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    formMessage.textContent = 'Enviando tu registro...';

    try {
      const response = await fetch('/api/registro', {
        body: JSON.stringify(Object.fromEntries(new FormData(registrationForm))),
        headers: { 'Content-Type': 'application/json' },
        method: 'POST'
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'No se pudo completar el registro.');
      registrationForm.reset();
      formMessage.textContent = result.message;
    } catch (error) {
      formMessage.textContent = error.message;
    } finally {
      submitButton.disabled = false;
    }
  });
}