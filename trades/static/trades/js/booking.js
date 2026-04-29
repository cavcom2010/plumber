(function () {
    const dateInput = document.getElementById('date');
    const emergencyCheck = document.getElementById('emergencyCheck');
    const emergencyNote = document.getElementById('emergencyNote');
    const emergencyToggle = document.getElementById('emergencyToggle');
    const form = document.getElementById('bookingForm');
    const submitBtn = document.getElementById('submitBtn');
    const successOverlay = document.getElementById('successOverlay');
    const closeSuccessBtn = document.getElementById('closeSuccessBtn');

    if (!form || !dateInput) return;

    const today = new Date();
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, '0');
    const dd = String(today.getDate()).padStart(2, '0');
    const todayString = `${yyyy}-${mm}-${dd}`;
    dateInput.setAttribute('min', todayString);

    function syncEmergencyState() {
        const checked = Boolean(emergencyCheck && emergencyCheck.checked);
        if (emergencyNote) emergencyNote.classList.toggle('visible', checked);
        if (emergencyToggle) emergencyToggle.classList.toggle('is-active', checked);
    }

    if (emergencyCheck) {
        syncEmergencyState();
        emergencyCheck.addEventListener('change', syncEmergencyState);
    }

    function clearErrors() {
        document.querySelectorAll('.form-group.error').forEach(group => group.classList.remove('error'));
        document.querySelectorAll('input.error, textarea.error').forEach(field => {
            field.classList.remove('error');
            field.removeAttribute('aria-invalid');
        });
    }

    function showError(fieldId, groupId) {
        const group = document.getElementById(groupId);
        const field = document.getElementById(fieldId);
        if (group) group.classList.add('error');
        if (field) {
            field.classList.add('error');
            field.setAttribute('aria-invalid', 'true');
        }
    }

    function showGroupError(groupId) {
        const group = document.getElementById(groupId);
        if (group) group.classList.add('error');
    }

    function normalisePhone(phone) {
        return phone.replace(/[\s().-]/g, '').replace(/^0044/, '+44');
    }

    function validateForm() {
        clearErrors();
        let isValid = true;

        const name = document.getElementById('name').value.trim();
        if (name.length < 2 || name.split(/\s+/).length < 2) {
            showError('name', 'group-name');
            isValid = false;
        }

        const phone = normalisePhone(document.getElementById('phone').value.trim());
        const phoneRegex = /^(?:(?:\+44)|0)\d{9,10}$/;
        if (!phoneRegex.test(phone)) {
            showError('phone', 'group-phone');
            isValid = false;
        }

        const email = document.getElementById('email').value.trim();
        if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            showError('email', 'group-email');
            isValid = false;
        }

        const dateVal = dateInput.value;
        if (!dateVal) {
            showError('date', 'group-date');
            isValid = false;
        } else {
            const selectedDate = new Date(dateVal + 'T00:00:00');
            const todayStart = new Date();
            todayStart.setHours(0, 0, 0, 0);
            if (selectedDate < todayStart) {
                showError('date', 'group-date');
                isValid = false;
            }
        }

        const address = document.getElementById('address').value.trim();
        if (address.length < 5) {
            showError('address', 'group-address');
            isValid = false;
        }

        const postcode = document.getElementById('postcode').value.trim().toUpperCase();
        const postcodeRegex = /^(GIR\s?0AA|[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2})$/i;
        if (!postcodeRegex.test(postcode)) {
            showError('postcode', 'group-postcode');
            isValid = false;
        }

        if (!document.querySelector('input[name="service"]:checked')) {
            showGroupError('group-service');
            isValid = false;
        }

        if (!document.querySelector('input[name="timeslot"]:checked')) {
            showGroupError('group-time');
            isValid = false;
        }

        const description = document.getElementById('description').value.trim();
        if (description.length < 10) {
            showError('description', 'group-description');
            isValid = false;
        }

        if (!isValid) {
            const firstError = document.querySelector('.form-group.error');
            if (firstError) firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }

        return isValid;
    }

    document.querySelectorAll('#bookingForm input, #bookingForm textarea').forEach(field => {
        field.addEventListener('input', function () {
            this.classList.remove('error');
            this.removeAttribute('aria-invalid');
            const group = this.closest('.form-group');
            if (group) group.classList.remove('error');
        });

        field.addEventListener('change', function () {
            this.classList.remove('error');
            this.removeAttribute('aria-invalid');
            const group = this.closest('.form-group');
            if (group) group.classList.remove('error');
        });
    });

    form.addEventListener('submit', function (event) {
        if (!validateForm()) {
            event.preventDefault();
            return;
        }

        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Submitting...';
        }
    });

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

    if (closeSuccessBtn) closeSuccessBtn.addEventListener('click', closeSuccess);

    if (successOverlay) {
        successOverlay.addEventListener('click', function (event) {
            if (event.target === successOverlay) closeSuccess();
        });
    }

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && successOverlay && successOverlay.classList.contains('active')) {
            closeSuccess();
        }
    });
})();
