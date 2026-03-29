const state = {
  config: null,
  slots: [],
  dashboard: null,
  language: localStorage.getItem("doctorSiteLanguage") || "en",
};

const ui = {
  doctorBio: document.querySelector("#doctorBio"),
  doctorHighlights: document.querySelector("#doctorHighlights"),
  doctorContact: document.querySelector("#doctorContact"),
  serviceGrid: document.querySelector("#serviceGrid"),
  locationGrid: document.querySelector("#locationGrid"),
  weeklySchedule: document.querySelector("#weeklySchedule"),
  serviceSelect: document.querySelector("#serviceSelect"),
  locationSelect: document.querySelector("#locationSelect"),
  slotSelect: document.querySelector("#slotSelect"),
  bookingForm: document.querySelector("#bookingForm"),
  bookingStatus: document.querySelector("#bookingStatus"),
  loginForm: document.querySelector("#loginForm"),
  loginStatus: document.querySelector("#loginStatus"),
  dashboardLogin: document.querySelector("#dashboardLogin"),
  dashboardShell: document.querySelector("#dashboardShell"),
  dashboardWelcome: document.querySelector("#dashboardWelcome"),
  notificationList: document.querySelector("#notificationList"),
  lockForm: document.querySelector("#lockForm"),
  lockStatus: document.querySelector("#lockStatus"),
  lockLocationSelect: document.querySelector("#lockLocationSelect"),
  lockList: document.querySelector("#lockList"),
  bookingList: document.querySelector("#bookingList"),
  logoutButton: document.querySelector("#logoutButton"),
  languageButtons: Array.from(document.querySelectorAll("[data-lang]")),
};

const translations = {
  en: {
    brand_subtitle: "Thoracic Surgery",
    nav_services: "Services",
    nav_book: "Book Appointment",
    call_us: "Call Us",
    hero_eyebrow: "Book Appointment With Doctor",
    hero_cta: "Make Appointment",
    email_label: "Email",
    phone_label: "Phone",
    quick_1_title: "Thoracic Surgery",
    quick_1_text: "Specialist consultations and follow-up care",
    quick_2_title: "Working Time",
    quick_2_text: "Choose from available appointment slots",
    quick_3_title: "Request Form",
    quick_3_text: "Send your booking directly online",
    quick_4_title: "Doctor Email",
    services_eyebrow: "Services",
    services_heading: "Simple specialist care for consultations and follow-up visits.",
    form_eyebrow: "Appointment Form",
    form_heading: "Book appointment with Dr. Granit Abdullahu.",
    form_intro: "Fill in your name, reason for appointment, and available time slot.",
    field_name: "Full name",
    field_phone: "Phone number",
    field_service: "Service",
    field_reason: "Reason for appointment",
    field_slot: "Available time slot",
    placeholder_name: "Patient full name",
    placeholder_phone: "044...",
    placeholder_reason: "Write shortly why you need the appointment",
    slot_choose_service: "Choose service first",
    slot_loading: "Loading slots...",
    slot_empty: "No open slots right now",
    slot_unavailable: "Unable to load slots",
    slot_choose: "Choose a slot",
    service_choose: "Choose service",
    submit_booking: "Send Booking Request",
    doctor_login: "Doctor Login",
    sending_booking: "Sending appointment request...",
    booking_success: "Appointment request sent successfully.",
    service_Thoracic_Consultation: "Thoracic Consultation",
    service_desc_Thoracic_Consultation: "Initial consultation for chest, lung, pleural, and thoracic surgical concerns.",
    service_Second_Opinion_Review: "Second Opinion Review",
    service_desc_Second_Opinion_Review: "Review imaging, reports, and treatment recommendations with a specialist perspective.",
    service_Follow_Up_Visit: "Follow-Up Visit",
    service_desc_Follow_Up_Visit: "Post-operative follow-up, recovery check, or ongoing thoracic care review.",
    highlight_1: "Thoracic consultations and diagnosis review",
    highlight_2: "Pre-operative planning and surgical second opinions",
    highlight_3: "Post-operative follow-up and recovery monitoring",
    doctor_bio:
      "Specialized thoracic surgery care with a calm, direct booking experience for consultations, follow-up visits, and second opinions.",
  },
  sq: {
    brand_subtitle: "Kirurgji Torakale",
    nav_services: "Shërbimet",
    nav_book: "Cakto Termin",
    call_us: "Na telefononi",
    hero_eyebrow: "Cakto Termin me Doktorin",
    hero_cta: "Cakto Termin",
    email_label: "Email",
    phone_label: "Telefoni",
    quick_1_title: "Kirurgji Torakale",
    quick_1_text: "Konsulta specialistike dhe kontrolla pas trajtimit",
    quick_2_title: "Orari i Punës",
    quick_2_text: "Zgjidhni nga terminet e lira",
    quick_3_title: "Forma e Kërkesës",
    quick_3_text: "Dërgojeni kërkesën për termin online",
    quick_4_title: "Email i Doktorit",
    services_eyebrow: "Shërbimet",
    services_heading: "Kujdes specialistik i thjeshtë për konsulta dhe kontrolle pasuese.",
    form_eyebrow: "Forma e Terminit",
    form_heading: "Cakto termin me Dr. Granit Abdullahu.",
    form_intro: "Shkruani emrin tuaj, arsyen e terminit dhe zgjidhni kohën e lirë.",
    field_name: "Emri i plotë",
    field_phone: "Numri i telefonit",
    field_service: "Shërbimi",
    field_reason: "Arsyeja e terminit",
    field_slot: "Koha e lirë",
    placeholder_name: "Emri dhe mbiemri",
    placeholder_phone: "044...",
    placeholder_reason: "Shkruani shkurt pse ju nevojitet termini",
    slot_choose_service: "Zgjidhni shërbimin së pari",
    slot_loading: "Duke ngarkuar terminet...",
    slot_empty: "Nuk ka termine të lira tani",
    slot_unavailable: "Terminet nuk mund të ngarkohen",
    slot_choose: "Zgjidhni një termin",
    service_choose: "Zgjidhni shërbimin",
    submit_booking: "Dërgo Kërkesën",
    doctor_login: "Hyrja e Doktorit",
    sending_booking: "Duke dërguar kërkesën për termin...",
    booking_success: "Kërkesa për termin u dërgua me sukses.",
    service_Thoracic_Consultation: "Konsultë Torakale",
    service_desc_Thoracic_Consultation: "Konsultë fillestare për shqetësime të kraharorit, mushkërive, pleurës dhe kirurgjisë torakale.",
    service_Second_Opinion_Review: "Mendim i Dytë",
    service_desc_Second_Opinion_Review: "Rishikim i imazherisë, raporteve dhe rekomandimeve të trajtimit nga këndvështrimi specialistik.",
    service_Follow_Up_Visit: "Vizitë Kontrolli",
    service_desc_Follow_Up_Visit: "Kontroll pas operacionit, vlerësim i rikuperimit dhe ndjekje e vazhdueshme.",
    highlight_1: "Konsulta torakale dhe rishikim i diagnozës",
    highlight_2: "Planifikim para operacionit dhe mendime të dyta kirurgjikale",
    highlight_3: "Kontrolle pas operacionit dhe monitorim i rikuperimit",
    doctor_bio:
      "Kujdes specialistik në kirurgjinë torakale me një mënyrë të thjeshtë rezervimi për konsulta, kontrolla pasuese dhe mendime të dyta.",
  },
};

function t(key) {
  return translations[state.language]?.[key] || translations.en[key] || key;
}

function serviceKey(name) {
  return name.replace(/[^A-Za-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
}

function applyStaticTranslations() {
  document.documentElement.lang = state.language;
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    element.placeholder = t(element.dataset.i18nPlaceholder);
  });
  ui.languageButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.lang === state.language);
  });
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || "Something went wrong.");
  }
  return payload;
}

function setStatus(element, message, tone = "neutral") {
  if (!element) {
    return;
  }
  element.textContent = message || "";
  element.dataset.tone = tone;
}

function renderConfig() {
  const { profile, services, locations, schedule } = state.config;
  if (ui.doctorBio) {
    ui.doctorBio.textContent = t("doctor_bio");
  }

  if (ui.doctorHighlights) {
    const highlightKeys = ["highlight_1", "highlight_2", "highlight_3"];
    ui.doctorHighlights.innerHTML = highlightKeys.map((key) => `<li>${t(key)}</li>`).join("");
  }
  if (ui.serviceGrid) {
    ui.serviceGrid.innerHTML = services
      .map(
        (service) => `
          <article class="service-card">
            <p class="service-duration">${service.durationMinutes} min</p>
            <h3>${t(`service_${serviceKey(service.name)}`)}</h3>
            <p>${t(`service_desc_${serviceKey(service.name)}`)}</p>
            <span class="pill">${service.priceLabel}</span>
          </article>
        `
      )
      .join("");
  }

  const serviceOptions = services
    .map((service) => `<option value="${service.id}">${t(`service_${serviceKey(service.name)}`)} (${service.durationMinutes} min)</option>`)
    .join("");
  const locationOptions = locations
    .map((location) => `<option value="${location.id}">${location.name}</option>`)
    .join("");

  if (ui.serviceSelect) {
    ui.serviceSelect.innerHTML = `<option value="">${t("service_choose")}</option>${serviceOptions}`;
  }
  if (ui.locationSelect) {
    ui.locationSelect.innerHTML = locationOptions;
    if (locations[0]) {
      ui.locationSelect.value = String(locations[0].id);
    }
  }
  if (ui.lockLocationSelect) {
    ui.lockLocationSelect.innerHTML = `<option value="">All locations</option>${locationOptions}`;
  }
}

async function loadSlots() {
  if (!ui.serviceSelect || !ui.locationSelect || !ui.slotSelect) {
    return;
  }
  const serviceId = ui.serviceSelect.value;
  const locationId = ui.locationSelect.value;
  if (!serviceId || !locationId) {
    ui.slotSelect.innerHTML = `<option value="">${t("slot_choose_service")}</option>`;
    return;
  }

  ui.slotSelect.innerHTML = `<option value="">${t("slot_loading")}</option>`;
  try {
    const data = await api(`/api/public/slots?serviceId=${serviceId}&locationId=${locationId}`);
    state.slots = data.slots;
    if (!data.slots.length) {
      ui.slotSelect.innerHTML = `<option value="">${t("slot_empty")}</option>`;
      return;
    }
    ui.slotSelect.innerHTML = `<option value="">${t("slot_choose")}</option>${data.slots
      .map((slot) => `<option value="${slot.startAt}">${slot.label}</option>`)
      .join("")}`;
  } catch (error) {
    ui.slotSelect.innerHTML = `<option value="">${t("slot_unavailable")}</option>`;
    setStatus(ui.bookingStatus, error.message, "error");
  }
}

function formatDateTime(isoString) {
  return new Date(isoString).toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function bookingActionsMarkup(booking) {
  return `
    <div class="booking-actions">
      <button class="mini-button" data-status-booking="${booking.id}" data-status-value="confirmed">Confirm</button>
      <button class="mini-button ghost" data-status-booking="${booking.id}" data-status-value="cancelled">Cancel</button>
    </div>
  `;
}

function renderDashboard() {
  if (!state.dashboard || !ui.dashboardWelcome || !ui.notificationList || !ui.lockList || !ui.bookingList) {
    return;
  }

  ui.dashboardWelcome.textContent = `Signed in as ${state.dashboard.doctor.name}`;
  ui.notificationList.innerHTML = state.dashboard.notifications.length
    ? state.dashboard.notifications
        .map(
          (item) => `
            <article class="notification-item ${item.isRead ? "" : "unread"}">
              <h4>${item.title}</h4>
              <p>${item.message}</p>
              <span>${formatDateTime(item.createdAt)}</span>
            </article>
          `
        )
        .join("")
    : `<p class="empty-state">No notifications yet.</p>`;

  ui.lockList.innerHTML = state.dashboard.locks.length
    ? state.dashboard.locks
        .map(
          (lock) => `
            <article class="lock-item">
              <div>
                <strong>${lock.locationName || "All locations"}</strong>
                <p>${formatDateTime(lock.startAt)} to ${formatDateTime(lock.endAt)}</p>
                <span>${lock.note || ""}</span>
              </div>
              <button class="mini-button ghost" data-delete-lock="${lock.id}">Remove</button>
            </article>
          `
        )
        .join("")
    : `<p class="empty-state">No blocked dates or hours.</p>`;

  ui.bookingList.innerHTML = state.dashboard.bookings.length
    ? state.dashboard.bookings
        .map(
          (booking) => `
            <article class="booking-item">
              <div class="booking-copy">
                <div class="booking-heading">
                  <h4>${booking.patientName}</h4>
                  <span class="pill status-${booking.status}">${booking.status}</span>
                </div>
                <p><strong>${booking.serviceName}</strong> at ${booking.locationName}</p>
                <p>${formatDateTime(booking.appointmentAt)}</p>
                <p>${booking.patientEmail}${booking.patientPhone ? ` • ${booking.patientPhone}` : ""}</p>
                <p class="muted">${booking.reason}</p>
              </div>
              ${booking.status === "pending" ? bookingActionsMarkup(booking) : ""}
            </article>
          `
        )
        .join("")
    : `<p class="empty-state">No appointment requests yet.</p>`;

  if (ui.dashboardLogin) {
    ui.dashboardLogin.classList.add("hidden");
  }
  if (ui.dashboardShell) {
    ui.dashboardShell.classList.remove("hidden");
  }
}

async function refreshDashboard() {
  const data = await api("/api/doctor/me");
  state.dashboard = data;
  renderDashboard();
}

async function bootstrap() {
  state.config = await api("/api/public/config");
  applyStaticTranslations();
  renderConfig();

  try {
    await refreshDashboard();
  } catch (_error) {
    state.dashboard = null;
  }
}

if (ui.serviceSelect) {
  ui.serviceSelect.addEventListener("change", loadSlots);
}

if (ui.locationSelect) {
  ui.locationSelect.addEventListener("change", loadSlots);
}

if (ui.bookingForm) {
  ui.bookingForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(ui.bookingForm);
    const payload = Object.fromEntries(formData.entries());
    setStatus(ui.bookingStatus, t("sending_booking"), "neutral");
    try {
      const data = await api("/api/public/bookings", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setStatus(ui.bookingStatus, t("booking_success"), "success");
      ui.bookingForm.reset();
      if (ui.slotSelect) {
        ui.slotSelect.innerHTML = `<option value="">${t("slot_choose_service")}</option>`;
      }
      if (ui.locationSelect && state.config?.locations?.[0]) {
        ui.locationSelect.value = String(state.config.locations[0].id);
      }
      if (state.dashboard) {
        await refreshDashboard();
      }
    } catch (error) {
      setStatus(ui.bookingStatus, error.message, "error");
    }
  });
}

ui.languageButtons.forEach((button) => {
  button.addEventListener("click", () => {
    state.language = button.dataset.lang;
    localStorage.setItem("doctorSiteLanguage", state.language);
    applyStaticTranslations();
    if (state.config) {
      renderConfig();
      if (ui.slotSelect) {
        ui.slotSelect.innerHTML = `<option value="">${t("slot_choose_service")}</option>`;
      }
    }
  });
});

if (ui.loginForm) {
  ui.loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(ui.loginForm);
    setStatus(ui.loginStatus, "Checking credentials...", "neutral");
    try {
      await api("/api/doctor/login", {
        method: "POST",
        body: JSON.stringify(Object.fromEntries(formData.entries())),
      });
      setStatus(ui.loginStatus, "");
      await refreshDashboard();
    } catch (error) {
      setStatus(ui.loginStatus, error.message, "error");
    }
  });
}

if (ui.lockForm) {
  ui.lockForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(ui.lockForm);
    const values = Object.fromEntries(formData.entries());
    const payload = {
      ...values,
      startAt: values.startAt ? new Date(values.startAt).toISOString() : "",
      endAt: values.endAt ? new Date(values.endAt).toISOString() : "",
    };
    setStatus(ui.lockStatus, "Saving lock...", "neutral");
    try {
      const data = await api("/api/doctor/locks", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      state.dashboard.locks = data.locks;
      setStatus(ui.lockStatus, "Locked successfully.", "success");
      ui.lockForm.reset();
      renderDashboard();
      await loadSlots();
    } catch (error) {
      setStatus(ui.lockStatus, error.message, "error");
    }
  });
}

if (ui.bookingList) {
  ui.bookingList.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-status-booking]");
    if (!button) {
      return;
    }
    const bookingId = button.getAttribute("data-status-booking");
    const status = button.getAttribute("data-status-value");
    try {
      const data = await api(`/api/doctor/bookings/${bookingId}/status`, {
        method: "POST",
        body: JSON.stringify({ status }),
      });
      state.dashboard.bookings = data.bookings;
      state.dashboard.notifications = data.notifications;
      renderDashboard();
    } catch (error) {
      setStatus(ui.loginStatus, error.message, "error");
    }
  });
}

if (ui.lockList) {
  ui.lockList.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-delete-lock]");
    if (!button) {
      return;
    }
    const lockId = button.getAttribute("data-delete-lock");
    try {
      const data = await api(`/api/doctor/locks/${lockId}`, { method: "DELETE" });
      state.dashboard.locks = data.locks;
      renderDashboard();
      await loadSlots();
    } catch (error) {
      setStatus(ui.lockStatus, error.message, "error");
    }
  });
}

if (ui.logoutButton) {
  ui.logoutButton.addEventListener("click", async () => {
    await api("/api/doctor/logout", { method: "POST", body: JSON.stringify({}) });
    state.dashboard = null;
    if (ui.dashboardShell) {
      ui.dashboardShell.classList.add("hidden");
    }
    if (ui.dashboardLogin) {
      ui.dashboardLogin.classList.remove("hidden");
    }
    if (ui.dashboardWelcome) {
      ui.dashboardWelcome.textContent = "";
    }
  });
}

bootstrap().catch((error) => {
  setStatus(ui.bookingStatus, error.message, "error");
});
