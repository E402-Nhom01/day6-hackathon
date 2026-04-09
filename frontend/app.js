const userSavedPlaces = {
  home: 'Home · 24 Lotus Street',
  work: 'Work · 88 Skyline Ave'
};

const micBtn = document.getElementById('micBtn');
const micLabel = document.getElementById('micLabel');
const statusPill = document.getElementById('statusPill');
const liveInput = document.getElementById('liveInput');
const parseBtn = document.getElementById('parseBtn');
const clearBtn = document.getElementById('clearBtn');
const destA = document.getElementById('destA');
const destB = document.getElementById('destB');
const vehicle = document.getElementById('vehicle');
const suggestions = document.getElementById('suggestions');
const confirmBtn = document.getElementById('confirmBtn');
const editBtn = document.getElementById('editBtn');
const formNote = document.getElementById('formNote');
const modal = document.getElementById('modal');
const closeModal = document.getElementById('closeModal');

let listening = false;
let recognition;

function normalize(text) {
  return text.trim().toLowerCase();
}

function detectVehicle(text) {
  const lower = normalize(text);
  if (lower.includes('car')) return 'Car';
  if (lower.includes('bike') || lower.includes('motorbike')) return 'Bike';
  return '';
}

function detectSavedPlace(text) {
  const lower = normalize(text);
  if (lower.includes('home')) return userSavedPlaces.home;
  if (lower.includes('work')) return userSavedPlaces.work;
  return '';
}

function extractDestinations(text) {
  const lower = normalize(text);
  let a = '';
  let b = '';

  const fromMatch = lower.match(/from\s+(.+?)\s+to\s+(.+)/);
  if (fromMatch) {
    a = fromMatch[1];
    b = fromMatch[2];
  } else if (lower.includes(' to ')) {
    const parts = lower.split(' to ');
    a = parts[0].replace('go', '').replace('going', '').trim();
    b = parts.slice(1).join(' to ').trim();
  }

  return { a: a.trim(), b: b.trim() };
}

function applyFormFromText(text) {
  const saved = detectSavedPlace(text);
  const { a, b } = extractDestinations(text);
  const vehicleName = detectVehicle(text);

  if (saved) {
    if (!destA.value) destA.value = saved;
    else if (!destB.value) destB.value = saved;
  }

  if (a && !destA.value) destA.value = a;
  if (b && !destB.value) destB.value = b;

  if (vehicleName && !vehicle.value) vehicle.value = vehicleName;

  toggleSuggestions();
}

function toggleSuggestions() {
  if (!vehicle.value) {
    suggestions.classList.add('active');
  } else {
    suggestions.classList.remove('active');
  }
}

function setStatus(text, active) {
  statusPill.textContent = text;
  if (active) {
    statusPill.classList.add('success');
  } else {
    statusPill.classList.remove('success');
  }
}

function startListening() {
  listening = true;
  micBtn.classList.add('active');
  micBtn.setAttribute('aria-pressed', 'true');
  micLabel.textContent = 'Listening';
  setStatus('Listening', true);

  if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.onresult = (event) => {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        transcript += event.results[i][0].transcript;
      }
      liveInput.value = transcript.trim();
      applyFormFromText(liveInput.value);
    };
    recognition.start();
  }
}

function stopListening() {
  listening = false;
  micBtn.classList.remove('active');
  micBtn.setAttribute('aria-pressed', 'false');
  micLabel.textContent = 'Start Listening';
  setStatus('Idle', false);
  if (recognition) {
    recognition.stop();
  }
}

micBtn.addEventListener('click', () => {
  if (!listening) startListening();
  else stopListening();
});

liveInput.addEventListener('input', (event) => {
  applyFormFromText(event.target.value);
});

parseBtn.addEventListener('click', () => {
  applyFormFromText(liveInput.value);
  formNote.textContent = 'Check the details and confirm to finish booking.';
});

clearBtn.addEventListener('click', () => {
  liveInput.value = '';
  destA.value = '';
  destB.value = '';
  vehicle.value = '';
  formNote.textContent = 'Validate the trip info to complete the booking.';
  toggleSuggestions();
});

suggestions.addEventListener('click', (event) => {
  const target = event.target.closest('.suggestion');
  if (!target) return;
  vehicle.value = target.dataset.vehicle;
  toggleSuggestions();
});

confirmBtn.addEventListener('click', () => {
  if (!destA.value || !destB.value) {
    formNote.textContent = 'Please confirm both destinations before completing.';
    formNote.style.color = '#ffb085';
    return;
  }
  formNote.style.color = '';
  modal.classList.add('show');
  modal.setAttribute('aria-hidden', 'false');
});

editBtn.addEventListener('click', () => {
  formNote.textContent = 'Edit the fields manually or speak again.';
});

closeModal.addEventListener('click', () => {
  modal.classList.remove('show');
  modal.setAttribute('aria-hidden', 'true');
});

window.addEventListener('load', () => {
  toggleSuggestions();
});
