(function () {
    // ============================================================
    // FEATURES THAT RUN ON EVERY PAGE
    // ============================================================

    // --- CSP-safe CSS load (replaces inline onload) ---
    var preloadedCSS = document.querySelector('link[rel="preload"][as="style"]');
    if (preloadedCSS) {
        preloadedCSS.addEventListener('load', function () {
            preloadedCSS.onload = null;
            preloadedCSS.rel = 'stylesheet';
        });
    }

    // --- Mobile Menu ---
    var mobileMenuToggle = document.getElementById('mobileMenuToggle');
    var mobileMenuPanel = document.getElementById('mobileMenuPanel');

    if (mobileMenuToggle && mobileMenuPanel) {
        function closeMobileMenu() {
            mobileMenuPanel.hidden = true;
            mobileMenuToggle.classList.remove('is-open');
            mobileMenuToggle.setAttribute('aria-expanded', 'false');
            mobileMenuToggle.setAttribute('aria-label', 'Open menu');
        }

        function openMobileMenu() {
            mobileMenuPanel.hidden = false;
            mobileMenuToggle.classList.add('is-open');
            mobileMenuToggle.setAttribute('aria-expanded', 'true');
            mobileMenuToggle.setAttribute('aria-label', 'Close menu');
        }

        mobileMenuToggle.addEventListener('click', function () {
            if (mobileMenuPanel.hidden) { openMobileMenu(); }
            else { closeMobileMenu(); }
        });

        mobileMenuPanel.querySelectorAll('a').forEach(function (link) {
            link.addEventListener('click', closeMobileMenu);
        });

        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape' && !mobileMenuPanel.hidden) {
                closeMobileMenu();
                mobileMenuToggle.focus();
            }
        });

        window.addEventListener('resize', function () {
            if (window.innerWidth >= 768) { closeMobileMenu(); }
        });
    }

    // --- Skip Link ---
    var skipLink = document.querySelector('.skip-link');
    if (skipLink) {
        skipLink.addEventListener('click', function (e) {
            var target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.setAttribute('tabindex', '-1');
                target.focus({ preventScroll: false });
            }
        });
    }

    // --- Active Mobile Nav ---
    var mobileNav = document.getElementById('mobileNav');
    if (mobileNav) {
        var currentPath = window.location.pathname;
        mobileNav.querySelectorAll('.mobile-nav-item').forEach(function (item) {
            var href = item.getAttribute('href');
            if (href && (href === currentPath || (href !== '/' && currentPath.indexOf(href) === 0))) {
                item.classList.add('active');
            }
        });
    }

    // --- Back to Top ---
    var backToTop = document.getElementById('backToTop');
    if (backToTop) {
        function toggleBackToTop() {
            if (window.scrollY > 300) {
                backToTop.classList.add('visible');
            } else {
                backToTop.classList.remove('visible');
            }
        }

        window.addEventListener('scroll', toggleBackToTop, { passive: true });
        toggleBackToTop();

        backToTop.addEventListener('click', function () {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // --- Cookie Consent ---
    var cookieBanner = document.getElementById('cookieBanner');
    if (cookieBanner) {
        var hasConsent = false;
        try {
            hasConsent = !!localStorage.getItem('cookie_consent');
        } catch (e) {
            try {
                hasConsent = !!sessionStorage.getItem('cookie_consent');
            } catch (e2) {}
        }

        if (!hasConsent) {
            cookieBanner.classList.add('visible');
        }

        var acceptBtn = cookieBanner.querySelector('[data-cookie-accept]');
        if (acceptBtn) {
            acceptBtn.addEventListener('click', function () {
                var data = JSON.stringify({ accepted: true, date: new Date().toISOString() });
                try { localStorage.setItem('cookie_consent', data); } catch (e) {}
                try { sessionStorage.setItem('cookie_consent', data); } catch (e) {}
                cookieBanner.classList.add('hidden');
                cookieBanner.classList.remove('visible');
            });
        }
    }

    // --- Scroll Animations (Intersection Observer) ---
    var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!prefersReducedMotion) {
        var animatedElements = document.querySelectorAll('[data-animate]');
        if (animatedElements.length) {
            var animationObserver = new IntersectionObserver(function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('animate-in');
                        animationObserver.unobserve(entry.target);
                    }
                });
            }, { root: null, rootMargin: '0px 0px -40px 0px', threshold: 0.12 });

            animatedElements.forEach(function (el) { animationObserver.observe(el); });
        }
    }

    // --- Star Rating Rendering ---
    function renderStars(container, rating, maxStars) {
        maxStars = maxStars || 5;
        var html = '';
        for (var i = 1; i <= maxStars; i++) {
            var filled = i <= rating;
            html += '<span class="star-icon ' + (filled ? 'filled' : 'empty') + '" aria-hidden="true">';
            html += '<svg viewBox="0 0 24 24"><use href="' + (filled ? '#icon-star-filled' : '#icon-star') + '"></use></svg>';
            html += '</span>';
        }
        container.innerHTML = html;
        container.setAttribute('role', 'img');
        container.setAttribute('aria-label', rating + ' out of ' + maxStars + ' stars');
    }

    document.querySelectorAll('.testimonial-stars').forEach(function (container) {
        var rating = parseInt(container.getAttribute('data-rating'), 10);
        if (rating && rating >= 1 && rating <= 5) {
            renderStars(container, rating, 5);
        }
    });

    // --- Avatar Initials ---
    var avatarColors = [
        '#1a1f3c', '#c7962e', '#2d7d46', '#c0392b', '#1e40af',
        '#7c3aed', '#0d9488', '#b45309', '#be185d', '#4f46e5',
    ];

    function hashString(str) {
        var hash = 0;
        for (var i = 0; i < str.length; i++) {
            hash = ((hash << 5) - hash) + str.charCodeAt(i);
            hash |= 0;
        }
        return hash;
    }

    document.querySelectorAll('.avatar-initials').forEach(function (el) {
        var name = el.getAttribute('data-name') || '';
        var colorIndex = Math.abs(hashString(name)) % avatarColors.length;
        el.style.backgroundColor = avatarColors[colorIndex];
    });

    // --- Character Counters ---
    document.querySelectorAll('[data-char-counter]').forEach(function (counter) {
        var targetId = counter.getAttribute('data-char-counter');
        var max = parseInt(counter.getAttribute('data-char-max'), 10) || 0;
        var target = document.getElementById(targetId);
        if (!target) return;

        function updateCounter() {
            var len = target.value.length;
            counter.textContent = len + (max ? ' / ' + max : '');
            counter.classList.remove('warning', 'danger');
            if (max && len > max * 0.8) counter.classList.add('warning');
            if (max && len >= max) counter.classList.add('danger');
        }

        target.addEventListener('input', updateCounter);
        updateCounter();
    });

    // --- Success Overlay (universal) ---
    var successOverlay = document.getElementById('successOverlay');
    var closeSuccessBtn = document.getElementById('closeSuccessBtn');

    function openSuccess() {
        if (!successOverlay) return;
        successOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeSuccess() {
        if (!successOverlay) return;
        successOverlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    if (document.body.dataset.bookingSuccess === 'true') {
        openSuccess();
    }

    if (closeSuccessBtn) {
        closeSuccessBtn.addEventListener('click', closeSuccess);
    }

    if (successOverlay) {
        successOverlay.addEventListener('click', function (event) {
            if (event.target === successOverlay) closeSuccess();
        });
    }

    // ============================================================
    // SPINNER HELPER
    // ============================================================
    function showSpinner(button, text) {
        var originalText = button.getAttribute('data-original-text') || button.textContent;
        button.setAttribute('data-original-text', originalText);
        button.setAttribute('aria-busy', 'true');
        button.innerHTML = '<span class="spinner"><svg viewBox="0 0 24 24"><use href="#icon-spinner"></use></svg></span> ' + (text || originalText);
    }

    function restoreButton(button) {
        var originalText = button.getAttribute('data-original-text');
        if (!originalText) return;
        button.removeAttribute('aria-busy');
        button.textContent = originalText;
    }

    // ============================================================
    // TESTIMONIAL FORM
    // ============================================================
    var testimonialForm = document.querySelector('.testimonial-card-form form[method="post"]');
    if (testimonialForm) {
        testimonialForm.addEventListener('submit', function () {
            var btn = this.querySelector('button[type="submit"]');
            if (btn) {
                btn.disabled = true;
                showSpinner(btn, 'Sending...');
            }
        });
    }

    // ============================================================
    // BOOKING FORM WIZARD
    // ============================================================
    var form = document.getElementById('bookingForm');
    if (!form) return;

    var LS_KEY = 'booking_form_draft';

    // --- DOM refs ---
    var dateInput = document.getElementById('date');
    var emergencyCheck = document.getElementById('emergencyCheck');
    var emergencyNote = document.getElementById('emergencyNote');
    var emergencyToggle = document.getElementById('emergencyToggle');
    var asapChip = document.getElementById('asapChip');
    var timeSlotGrid = document.getElementById('timeSlotGrid');
    var wizardProgress = document.getElementById('wizardProgress');
    var wizardNav = document.getElementById('wizardNav');
    var wizardBackBtn = document.getElementById('wizardBackBtn');
    var wizardNextBtn = document.getElementById('wizardNextBtn');
    var bookingSummaryContent = document.getElementById('bookingSummaryContent');
    var currentStep = 1;
    var totalSteps = 4;
    var submitting = false;

    // --- Date min ---
    var today = new Date();
    var yyyy = today.getFullYear();
    var mm = String(today.getMonth() + 1).padStart(2, '0');
    var dd = String(today.getDate()).padStart(2, '0');
    var todayString = yyyy + '-' + mm + '-' + dd;
    if (dateInput) dateInput.setAttribute('min', todayString);

    // --- Emergency toggle ---
    function syncEmergencyState() {
        var checked = Boolean(emergencyCheck && emergencyCheck.checked);
        if (emergencyNote) emergencyNote.classList.toggle('visible', checked);
        if (emergencyToggle) emergencyToggle.classList.toggle('is-active', checked);
    }

    if (emergencyCheck) {
        syncEmergencyState();
        emergencyCheck.addEventListener('change', syncEmergencyState);
    }

    // --- File upload helpers ---
    function ensureFileDisplay(input) {
        var row = input.closest('.diagnostic-upload-row');
        if (!row) return;
        var display = row.querySelector('.file-name-display');
        if (!display) {
            display = document.createElement('span');
            display.className = 'file-name-display';
            row.appendChild(display);
        }
        return display;
    }

    function initImagePreviews() {
        document.querySelectorAll('.diagnostic-upload-row input[type="file"]').forEach(function (input) {
            var preview = input.parentElement.querySelector('.image-preview');
            if (!preview) return;

            input.addEventListener('change', function () {
                var display = ensureFileDisplay(input);
                if (this.files && this.files[0]) {
                    if (display) { display.textContent = this.files[0].name; display.classList.add('visible'); }
                    var reader = new FileReader();
                    reader.onload = function (e) {
                        preview.innerHTML = '<img src="' + e.target.result + '" alt="Preview">' +
                            '<button type="button" class="preview-remove" aria-label="Remove photo">Remove</button>';
                        preview.classList.add('has-image');
                    };
                    reader.readAsDataURL(this.files[0]);
                } else {
                    if (display) display.classList.remove('visible');
                }
            });

            preview.addEventListener('click', function (e) {
                if (e.target.classList.contains('preview-remove')) {
                    input.value = '';
                    preview.innerHTML = '';
                    preview.classList.remove('has-image');
                    var display = ensureFileDisplay(input);
                    if (display) { display.textContent = ''; display.classList.remove('visible'); }
                }
            });

            var row = input.closest('.diagnostic-upload-row');
            if (row) {
                row.addEventListener('dragover', function (e) { e.preventDefault(); row.classList.add('drag-over'); });
                row.addEventListener('dragleave', function () { row.classList.remove('drag-over'); });
                row.addEventListener('drop', function (e) {
                    e.preventDefault();
                    row.classList.remove('drag-over');
                    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                        input.files = e.dataTransfer.files;
                        input.dispatchEvent(new Event('change'));
                    }
                });
            }
        });
    }

    initImagePreviews();

    // --- Validation helpers ---
    function clearErrors() {
        document.querySelectorAll('#bookingForm .form-group.error').forEach(function (group) { group.classList.remove('error'); });
        document.querySelectorAll('#bookingForm input.error, #bookingForm textarea.error').forEach(function (field) {
            field.classList.remove('error');
            field.removeAttribute('aria-invalid');
        });
    }

    function showError(fieldId, groupId) {
        var group = document.getElementById(groupId);
        var field = document.getElementById(fieldId);
        if (group) group.classList.add('error');
        if (field) {
            field.classList.add('error');
            field.setAttribute('aria-invalid', 'true');
        }
    }

    function showGroupError(groupId) {
        var group = document.getElementById(groupId);
        if (group) group.classList.add('error');
    }

    function normalisePhone(phone) {
        return phone.replace(/[\s().-]/g, '').replace(/^0044/, '+44');
    }

    // --- Per-step validation ---
    function validateStep(step) {
        clearErrors();
        var isValid = true;

        if (step === 1) {
            if (!document.querySelector('input[name="service"]:checked')) { showGroupError('group-service'); isValid = false; }
            var description = document.getElementById('description').value.trim();
            if (description.length < 10) { showError('description', 'group-description'); isValid = false; }
        }

        if (step === 2) {
            var dateVal = dateInput ? dateInput.value : '';
            if (!dateVal) { showError('date', 'group-date'); isValid = false; }
            else {
                var selectedDate = new Date(dateVal + 'T00:00:00');
                var todayStart = new Date(); todayStart.setHours(0, 0, 0, 0);
                if (selectedDate < todayStart) { showError('date', 'group-date'); isValid = false; }
            }
            if (!document.querySelector('input[name="timeslot"]:checked')) { showGroupError('group-time'); isValid = false; }
        }

        if (step === 3) {
            var name = document.getElementById('name').value.trim();
            if (name.length < 2 || name.split(/\s+/).length < 2) { showError('name', 'group-name'); isValid = false; }

            var phone = normalisePhone(document.getElementById('phone').value.trim());
            if (!/^(?:(?:\+44)|0)\d{9,10}$/.test(phone)) { showError('phone', 'group-phone'); isValid = false; }

            var email = document.getElementById('email').value.trim();
            if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { showError('email', 'group-email'); isValid = false; }

            var address = document.getElementById('address').value.trim();
            if (address.length < 5) { showError('address', 'group-address'); isValid = false; }

            var postcode = document.getElementById('postcode').value.trim().toUpperCase();
            if (!/^(GIR\s?0AA|[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2})$/i.test(postcode)) { showError('postcode', 'group-postcode'); isValid = false; }
        }

        if (!isValid) {
            var firstError = document.querySelector('#bookingForm .form-group.error');
            if (firstError) firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        return isValid;
    }

    // --- Blur validation ---
    function attachBlurValidation() {
        var step1Fields = [
            { el: document.getElementById('description'), groupId: 'group-description', check: function (v) { return v.trim().length >= 10; } },
        ];
        var step3Fields = [
            { el: document.getElementById('name'), groupId: 'group-name', check: function (v) { var t = v.trim(); return t.length >= 2 && t.split(/\s+/).length >= 2; } },
            { el: document.getElementById('phone'), groupId: 'group-phone', check: function (v) { return /^(?:(?:\+44)|0)\d{9,10}$/.test(normalisePhone(v.trim())); } },
            { el: document.getElementById('email'), groupId: 'group-email', check: function (v) { var t = v.trim(); return !t || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(t); } },
            { el: document.getElementById('address'), groupId: 'group-address', check: function (v) { return v.trim().length >= 5; } },
            { el: document.getElementById('postcode'), groupId: 'group-postcode', check: function (v) { return /^(GIR\s?0AA|[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2})$/i.test(v.trim()); } },
        ];

        [].concat(step1Fields, step3Fields).forEach(function (item) {
            if (!item.el) return;
            item.el.addEventListener('blur', function () {
                var val = this.value;
                if (val.length === 0) return; // don't validate empty on blur
                var group = document.getElementById(item.groupId);
                if (group) {
                    if (item.check(val)) {
                        group.classList.remove('error');
                        this.classList.remove('error');
                        this.removeAttribute('aria-invalid');
                    } else {
                        group.classList.add('error');
                        this.classList.add('error');
                        this.setAttribute('aria-invalid', 'true');
                    }
                }
            });
        });

        var dateEl = document.getElementById('date');
        if (dateEl) {
            dateEl.addEventListener('change', function () {
                if (this.value) fetchAvailableSlots(this.value);
            });
        }
    }

    attachBlurValidation();

    // --- Clear error on input/change ---
    document.querySelectorAll('#bookingForm input, #bookingForm textarea').forEach(function (field) {
        field.addEventListener('input', function () {
            this.classList.remove('error');
            this.removeAttribute('aria-invalid');
            var group = this.closest('.form-group');
            if (group) group.classList.remove('error');
        });
        field.addEventListener('change', function () {
            this.classList.remove('error');
            this.removeAttribute('aria-invalid');
            var group = this.closest('.form-group');
            if (group) group.classList.remove('error');
        });
    });

    // --- Postcode service area check ---
    var servicePostcodes = form.dataset.servicePostcodes;
    if (servicePostcodes) {
        var postcodeInput = document.getElementById('postcode');
        var postcodeGroup = document.getElementById('group-postcode');
        if (postcodeInput && postcodeGroup) {
            var postcodeNote = document.createElement('div');
            postcodeNote.className = 'postcode-area-note';
            postcodeNote.style.display = 'none';
            postcodeGroup.appendChild(postcodeNote);

            postcodeInput.addEventListener('blur', function () {
                var val = this.value.trim().toUpperCase().replace(/\s/g, '');
                if (!val) return;
                var prefix = val.match(/^[A-Z]+/);
                if (!prefix) return;
                var prefixes = servicePostcodes.split(',').map(function (s) { return s.trim().toUpperCase(); });
                if (prefixes.indexOf(prefix[0]) === -1) {
                    postcodeNote.textContent = 'This postcode may be outside our normal service area. We will check availability and confirm.';
                    postcodeNote.style.display = 'block';
                } else {
                    postcodeNote.style.display = 'none';
                }
            });
        }
    }

    // --- Booking lookup (existing bookings for repeat customers) ---
    var lookupDropdown = document.getElementById('bookingLookupDropdown');
    if (lookupDropdown) {
        var lookupTimer = null;
        var lookupAbort = null;
        var LOOKUP_DEBOUNCE = 300;

        function fillBookingFields(booking) {
            var fields = { 'name': booking.full_name, 'phone': booking.phone, 'email': booking.email || '', 'address': booking.address, 'postcode': booking.postcode, 'description': booking.description };
            Object.keys(fields).forEach(function (id) { var el = document.getElementById(id); if (el) el.value = fields[id]; });
            var radio = document.querySelector('input[name="service"][value="' + booking.service + '"]');
            if (radio) radio.checked = true;
        }

        function escapeHtml(str) {
            var div = document.createElement('div');
            div.appendChild(document.createTextNode(str));
            return div.innerHTML;
        }

        function hideLookupDropdown() { lookupDropdown.classList.remove('active'); lookupDropdown.innerHTML = ''; }
        function showLookupDropdown(html) { lookupDropdown.innerHTML = html; lookupDropdown.classList.add('active'); }

        function positionDropdown(input) {
            var rect = input.getBoundingClientRect();
            lookupDropdown.style.top = (rect.bottom + window.scrollY + 2) + 'px';
            lookupDropdown.style.left = (rect.left + window.scrollX) + 'px';
            lookupDropdown.style.width = rect.width + 'px';
        }

        function fetchBookings(query, input) {
            if (lookupAbort) lookupAbort.abort();
            lookupAbort = new AbortController();

            fetch('/invoice/api/bookings/?q=' + encodeURIComponent(query), { signal: lookupAbort.signal })
                .then(function (resp) { if (!resp.ok) throw new Error('Lookup failed'); return resp.json(); })
                .then(function (data) {
                    if (!data.length) { showLookupDropdown('<div class="lookup-item lookup-empty">No matching bookings</div>'); return; }
                    var html = '';
                    data.forEach(function (b) {
                        html += '<div class="lookup-item" data-booking=\'' + JSON.stringify(b).replace(/'/g, '&#39;') + '\'>' +
                            '<span class="lookup-name">' + escapeHtml(b.full_name) + '</span>' +
                            '<span class="lookup-sub">' + escapeHtml(b.phone) + ' &mdash; ' + escapeHtml(b.service_display) + '</span></div>';
                    });
                    showLookupDropdown(html);
                    positionDropdown(input);
                })
                .catch(function () {});
        }

        lookupDropdown.addEventListener('click', function (e) {
            var item = e.target.closest('.lookup-item');
            if (!item || !item.dataset.booking) return;
            fillBookingFields(JSON.parse(item.dataset.booking));
            hideLookupDropdown();
        });

        document.addEventListener('click', function (e) { if (!lookupDropdown.contains(e.target)) hideLookupDropdown(); });
        document.addEventListener('keydown', function (e) { if (e.key === 'Escape') hideLookupDropdown(); });

        ['name', 'phone'].forEach(function (fieldId) {
            var input = document.getElementById(fieldId);
            if (!input) return;

            input.addEventListener('input', function () {
                var query = this.value.trim();
                if (query.length < 2) { hideLookupDropdown(); return; }
                clearTimeout(lookupTimer);
                var self = this;
                lookupTimer = setTimeout(function () { fetchBookings(query, self); }, LOOKUP_DEBOUNCE);
            });

            input.addEventListener('focus', function () {
                var query = this.value.trim();
                if (query.length >= 2) {
                    clearTimeout(lookupTimer);
                    var self = this;
                    lookupTimer = setTimeout(function () { fetchBookings(query, self); }, LOOKUP_DEBOUNCE);
                }
            });
        });
    }

    // --- Slot API ---
    var slotAbort = null;
    function fetchAvailableSlots(dateStr) {
        if (slotAbort) slotAbort.abort();
        slotAbort = new AbortController();

        var allPills = timeSlotGrid ? timeSlotGrid.querySelectorAll('.time-slot-pill') : [];
        allPills.forEach(function (p) { p.classList.remove('disabled'); p.querySelector('input').disabled = false; });

        if (!dateStr) return;

        fetch('/api/slots/?date=' + encodeURIComponent(dateStr), { signal: slotAbort.signal })
            .then(function (resp) { if (!resp.ok) throw new Error('Slots fetch failed'); return resp.json(); })
            .then(function (data) {
                var availableSet = new Set(data.slots || []);
                allPills.forEach(function (pill) {
                    var input = pill.querySelector('input');
                    var slotValue = input ? input.value : '';
                    if (!availableSet.has(slotValue)) {
                        pill.classList.add('disabled');
                        if (input) { input.checked = false; input.disabled = true; }
                    }
                });
            })
            .catch(function () {});
    }

    // --- ASAP logic ---
    function getOpeningHour() { try { return parseInt(document.body.dataset.openingTime || '8', 10); } catch (e) { return 8; } }
    function getClosingHour() { try { return parseInt(document.body.dataset.closingTime || '18', 10); } catch (e) { return 18; } }

    function getASAPDate() {
        var now = new Date();
        var closingHour = getClosingHour();
        if (now.getHours() >= closingHour) {
            var tomorrow = new Date(now);
            tomorrow.setDate(tomorrow.getDate() + 1);
            return tomorrow.toISOString().slice(0, 10);
        }
        return todayString;
    }

    if (asapChip && dateInput) {
        asapChip.addEventListener('click', function () {
            var asapDate = getASAPDate();
            dateInput.value = asapDate;
            fetchAvailableSlots(asapDate);
        });
    }

    // --- Wizard navigation ---
    function showStep(step) {
        currentStep = step;
        document.querySelectorAll('#bookingForm .wizard-step').forEach(function (el) {
            el.classList.toggle('active', parseInt(el.dataset.step) === step);
        });
        updateProgress();
        updateNavButtons();
        saveDraft();
    }

    function updateProgress() {
        if (!wizardProgress) return;
        var indicators = wizardProgress.querySelectorAll('.wizard-step-indicator');
        indicators.forEach(function (ind) {
            var s = parseInt(ind.dataset.step);
            ind.classList.remove('active', 'completed');
            if (s < currentStep) ind.classList.add('completed');
            if (s === currentStep) ind.classList.add('active');
        });
    }

    function updateNavButtons() {
        if (!wizardBackBtn || !wizardNextBtn) return;
        wizardBackBtn.style.display = currentStep > 1 ? '' : 'none';

        if (currentStep < totalSteps) {
            wizardNextBtn.textContent = 'Next';
            wizardNextBtn.className = 'wizard-nav-btn wizard-nav-btn-next';
        } else {
            wizardNextBtn.textContent = 'Send Booking Enquiry';
            wizardNextBtn.className = 'wizard-nav-btn wizard-nav-btn-next';
        }
        restoreButton(wizardNextBtn);
    }

    function goNext() {
        if (!validateStep(currentStep)) return;

        if (currentStep < totalSteps) {
            if (currentStep === 3) buildSummary();
            showStep(currentStep + 1);
            var bookingCard = document.querySelector('.booking-card');
            if (bookingCard) bookingCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    function goBack() {
        if (currentStep > 1) {
            showStep(currentStep - 1);
            var bookingCard = document.querySelector('.booking-card');
            if (bookingCard) bookingCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    if (wizardNextBtn) {
        wizardNextBtn.addEventListener('click', goNext);
    }
    if (wizardBackBtn) {
        wizardBackBtn.addEventListener('click', goBack);
    }

    // --- Inline Summary (Step 4) ---
    function getFieldVal(id, fallback) {
        var el = document.getElementById(id);
        return (!el || !el.value) ? (fallback || '\u2014') : el.value.trim();
    }

    function getCheckedLabel(name, fallback) {
        var checked = document.querySelector('input[name="' + name + '"]:checked');
        if (!checked) return fallback || '\u2014';
        var card = checked.closest('label');
        if (card) {
            var span = card.querySelector('.card-label, .pill-label');
            if (span) return span.textContent.trim();
        }
        return checked.value;
    }

    function summaryRow(label, value) {
        return '<div class="booking-summary-row"><span class="booking-summary-label">' + label + '</span><span class="booking-summary-value">' + value + '</span></div>';
    }

    function buildSummary() {
        if (!bookingSummaryContent) return;

        var html = '<h4>Review your booking</h4>';

        html += '<div class="booking-summary-section"><div class="booking-summary-section-title">Contact</div>';
        html += summaryRow('Name', getFieldVal('name'));
        html += summaryRow('Phone', getFieldVal('phone'));
        html += summaryRow('Email', getFieldVal('email', '(not provided)'));
        html += summaryRow('Address', getFieldVal('address'));
        html += summaryRow('Postcode', getFieldVal('postcode'));
        html += '</div>';

        html += '<div class="booking-summary-section"><div class="booking-summary-section-title">Job</div>';
        html += summaryRow('Service', getCheckedLabel('service'));
        html += summaryRow('Date', getFieldVal('date'));
        html += summaryRow('Time', getCheckedLabel('timeslot'));
        html += summaryRow('Emergency', (emergencyCheck && emergencyCheck.checked) ? 'Yes' : 'No');
        html += summaryRow('Issue', getFieldVal('description'));
        html += '</div>';

        bookingSummaryContent.innerHTML = html;
    }

    // --- Form submit ---
    function submitBooking() {
        if (submitting) return;
        submitting = true;
        showSpinner(wizardNextBtn, 'Submitting...');
        wizardNextBtn.disabled = true;
        clearDraft();
        form.submit();
    }

    form.addEventListener('submit', function (event) {
        if (currentStep < totalSteps) {
            event.preventDefault();
            if (!validateStep(currentStep)) return;
            if (currentStep === 3) buildSummary();
            showStep(currentStep + 1);
        }
    });

    if (wizardNextBtn) {
        wizardNextBtn.addEventListener('click', function () {
            if (currentStep >= totalSteps) {
                if (!validateStep(1) || !validateStep(2) || !validateStep(3)) {
                    showStep(1);
                    return;
                }
                submitBooking();
            }
        });
    }

    // --- localStorage draft ---
    function getDraft() {
        try {
            var raw = localStorage.getItem(LS_KEY);
            return raw ? JSON.parse(raw) : {};
        } catch (e) { return {}; }
    }

    function saveDraft() {
        try {
            var data = {
                full_name: getFieldVal('name', ''),
                phone: getFieldVal('phone', ''),
                email: getFieldVal('email', ''),
                address: getFieldVal('address', ''),
                postcode: getFieldVal('postcode', ''),
                description: getFieldVal('description', ''),
                preferred_date: getFieldVal('date', ''),
                timeslot: document.querySelector('input[name="timeslot"]:checked') ? document.querySelector('input[name="timeslot"]:checked').value : '',
                service: document.querySelector('input[name="service"]:checked') ? document.querySelector('input[name="service"]:checked').value : '',
                is_emergency: emergencyCheck ? emergencyCheck.checked : false,
            };
            localStorage.setItem(LS_KEY, JSON.stringify(data));
        } catch (e) {}
    }

    function clearDraft() {
        try { localStorage.removeItem(LS_KEY); } catch (e) {}
    }

    function restoreDraft() {
        var draft = getDraft();
        var hasValue = false;
        var mappings = {
            full_name: 'name', phone: 'phone', email: 'email', address: 'address',
            postcode: 'postcode', description: 'description',
        };
        Object.keys(mappings).forEach(function (key) {
            var el = document.getElementById(mappings[key]);
            if (el && draft[key]) { el.value = draft[key]; hasValue = true; }
        });
        if (draft.preferred_date && dateInput) { dateInput.value = draft.preferred_date; hasValue = true; }
        if (draft.service) {
            var serviceRadio = document.querySelector('input[name="service"][value="' + draft.service + '"]');
            if (serviceRadio) serviceRadio.checked = true;
        }
        if (draft.timeslot) {
            var slotRadio = document.querySelector('input[name="timeslot"][value="' + draft.timeslot + '"]');
            if (slotRadio) slotRadio.checked = true;
        }
        if (draft.is_emergency && emergencyCheck) emergencyCheck.checked = true;
        syncEmergencyState();
        return hasValue;
    }

    restoreDraft();

    // Auto-save on input
    var saveTimer = null;
    document.querySelectorAll('#bookingForm input, #bookingForm textarea').forEach(function (el) {
        el.addEventListener('input', function () {
            clearTimeout(saveTimer);
            saveTimer = setTimeout(saveDraft, 500);
        });
        el.addEventListener('change', function () {
            clearTimeout(saveTimer);
            saveTimer = setTimeout(saveDraft, 500);
        });
    });

    // --- Keyboard shortcut: Enter on last step submits ---
    document.addEventListener('keydown', function (event) {
        if (event.key === 'Enter' && currentStep >= totalSteps && document.activeElement && document.activeElement.closest('#bookingForm')) {
            event.preventDefault();
            if (!validateStep(1) || !validateStep(2) || !validateStep(3)) { showStep(1); return; }
            submitBooking();
        }
    });

    // --- Initialize ---
    showStep(1);
    if (dateInput && dateInput.value) fetchAvailableSlots(dateInput.value);

    // --- Sticky nav on mobile ---
    if (wizardNav && window.innerWidth < 768) {
        var wrapper = document.createElement('div');
        wrapper.className = 'wizard-mobile-sticky';
        wizardNav.parentNode.insertBefore(wrapper, wizardNav);
        wrapper.appendChild(wizardNav);
    }

    // --- Opening/closing hours from data attributes ---
    if (document.body.dataset.openingTime) getOpeningHour();
    if (document.body.dataset.closingTime) getClosingHour();
})();
