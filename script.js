const header = document.querySelector('.site-header');
const menuToggle = document.querySelector('.menu-toggle');
const form = document.querySelector('#register-form');
const message = document.querySelector('.form-message');
const supabaseConfig = window.SUPABASE_CONFIG || {};

menuToggle.addEventListener('click', () => {
  const isOpen = header.classList.toggle('menu-open');
  menuToggle.setAttribute('aria-expanded', String(isOpen));
  menuToggle.textContent = isOpen ? 'Cerrar' : 'Menu';
});

document.querySelectorAll('.site-nav a').forEach((link) => {
  link.addEventListener('click', () => {
    header.classList.remove('menu-open');
    menuToggle.setAttribute('aria-expanded', 'false');
    menuToggle.textContent = 'Menu';
  });
});

form.addEventListener('submit', (event) => {
  event.preventDefault();
  const formData = new FormData(form);
  const registration = {
    event_slug: 'avivamiento-mexicano',
    full_name: formData.get('full_name'),
    email: formData.get('email'),
    phone: formData.get('phone'),
    church: formData.get('church'),
    city: formData.get('city'),
    consent: formData.get('consent') === 'on'
  };

  submitRegistration(registration);
});

async function submitRegistration(registration) {
  message.textContent = 'Enviando tu registro...';

  if (!supabaseConfig.url || !supabaseConfig.anonKey) {
    message.textContent = 'El formulario está listo. Falta conectar Supabase.';
    return;
  }

  try {
    const response = await fetch(`${supabaseConfig.url}/rest/v1/registrations`, {
      method: 'POST',
      headers: {
        apikey: supabaseConfig.anonKey,
        Authorization: `Bearer ${supabaseConfig.anonKey}`,
        'Content-Type': 'application/json',
        Prefer: 'return=minimal'
      },
      body: JSON.stringify(registration)
    });

    if (!response.ok) throw new Error('No se pudo guardar el registro.');
    message.textContent = 'Registro completado. Te compartiremos los próximos detalles pronto.';
    form.reset();
  } catch (error) {
    message.textContent = 'No pudimos guardar tu registro. Intenta de nuevo.';
  }
}