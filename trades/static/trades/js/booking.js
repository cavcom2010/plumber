(function () {
    const dateInput = document.getElementById('date');
    const emergencyCheck = document.getElementById('emergencyCheck');
    const emergencyNote = document.getElementById('emergencyNote');
    const emergencyToggle = document.getElementById('emergencyToggle');
    const form = document.getElementById('bookingForm');
    const submitBtn = document.getElementById('submitBtn');
    const successOverlay = document.getElementById('successOverlay');
    const closeSuccessBtn = document.getElementById('closeSuccessBtn');
    const reviewOverlay = document.getElementById('reviewOverlay');
    const reviewContent = document.getElementById('reviewContent');
    const reviewEditBtn = document.getElementById('reviewEditBtn');
    const reviewConfirmBtn = document.getElementById('reviewConfirmBtn');

    if (!form) return;

    const today = new Date();
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, '0');
    const dd = String(today.getDate()).padStart(2, '0');
    const todayString = `${yyyy}-${mm}-${dd}`;
    if (dateInput) dateInput.setAttribute('min', todayString);

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

    // -- Image preview --
    function initImagePreviews() {
        document.querySelectorAll('.diagnostic-upload-row input[type="file"]').forEach(function (input) {
            var preview = input.parentElement.querySelector('.image-preview');
            if (!preview) return;

            input.addEventListener('change', function () {
                if (this.files && this.files[0]) {
                    var reader = new FileReader();
                    reader.onload = function (e) {
                        preview.innerHTML =
                            '<img src="' + e.target.result + '" alt="Preview">' +
                            '<button type="button" class="preview-remove" aria-label="Remove photo">Remove</button>';
                        preview.classList.add('has-image');
                    };
                    reader.readAsDataURL(this.files[0]);
                }
            });

            preview.addEventListener('click', function (e) {
                if (e.target.classList.contains('preview-remove')) {
                    input.value = '';
                    preview.innerHTML = '';
                    preview.classList.remove('has-image');
                }
            });
        });
    }

    initImagePreviews();

    // -- Booking lookup --
    var lookupDropdown = document.getElementById('bookingLookupDropdown');
    if (lookupDropdown) {
        var lookupTimer = null;
        var lookupAbort = null;
        var LOOKUP_DEBOUNCE = 300;

        function fillBookingFields(booking) {
            var fields = {
                'name': booking.full_name,
                'phone': booking.phone,
                'email': booking.email || '',
                'address': booking.address,
                'postcode': booking.postcode,
                'description': booking.description,
            };
            Object.keys(fields).forEach(function (id) {
                var el = document.getElementById(id);
                if (el) el.value = fields[id];
            });

            var radio = document.querySelector('input[name="service"][value="' + booking.service + '"]');
            if (radio) radio.checked = true;
        }

        function escapeHtml(str) {
            var div = document.createElement('div');
            div.appendChild(document.createTextNode(str));
            return div.innerHTML;
        }

        function hideLookupDropdown() {
            lookupDropdown.classList.remove('active');
            lookupDropdown.innerHTML = '';
        }

        function showLookupDropdown(html) {
            lookupDropdown.innerHTML = html;
            lookupDropdown.classList.add('active');
        }

        function positionDropdown(input) {
            var rect = input.getBoundingClientRect();
            lookupDropdown.style.top = (rect.bottom + window.scrollY + 2) + 'px';
            lookupDropdown.style.left = (rect.left + window.scrollX) + 'px';
            lookupDropdown.style.width = rect.width + 'px';
        }

        function fetchBookings(query, input) {
            if (lookupAbort) lookupAbort.abort();
            lookupAbort = new AbortController();

            fetch('/invoice/api/bookings/?q=' + encodeURIComponent(query), {
                signal: lookupAbort.signal,
            })
                .then(function (resp) {
                    if (!resp.ok) throw new Error('Lookup failed');
                    return resp.json();
                })
                .then(function (data) {
                    if (!data.length) {
                        showLookupDropdown(
                            '<div class="lookup-item lookup-empty">No matching bookings</div>'
                        );
                        return;
                    }
                    var html = '';
                    data.forEach(function (b) {
                        html +=
                            '<div class="lookup-item" data-booking=\'' +
                            JSON.stringify(b).replace(/'/g, '&#39;') +
                            '\'>' +
                            '<span class="lookup-name">' + escapeHtml(b.full_name) + '</span>' +
                            '<span class="lookup-sub">' + escapeHtml(b.phone) + ' &mdash; ' + escapeHtml(b.service_display) + '</span>' +
                            '</div>';
                    });
                    showLookupDropdown(html);
                    positionDropdown(input);
                })
                .catch(function () {});
        }

        lookupDropdown.addEventListener('click', function (e) {
            var item = e.target.closest('.lookup-item');
            if (!item || !item.dataset.booking) return;
            var booking = JSON.parse(item.dataset.booking);
            fillBookingFields(booking);
            hideLookupDropdown();
        });

        document.addEventListener('click', function (e) {
            if (!lookupDropdown.contains(e.target)) {
                hideLookupDropdown();
            }
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') {
                hideLookupDropdown();
            }
        });

        ['name', 'phone'].forEach(function (fieldId) {
            var input = document.getElementById(fieldId);
            if (!input) return;

            input.addEventListener('input', function () {
                var query = this.value.trim();
                if (query.length < 2) {
                    hideLookupDropdown();
                    return;
                }
                clearTimeout(lookupTimer);
                var self = this;
                lookupTimer = setTimeout(function () {
                    fetchBookings(query, self);
                }, LOOKUP_DEBOUNCE);
            });

            input.addEventListener('focus', function () {
                var query = this.value.trim();
                if (query.length >= 2) {
                    clearTimeout(lookupTimer);
                    var self = this;
                    lookupTimer = setTimeout(function () {
                        fetchBookings(query, self);
                    }, LOOKUP_DEBOUNCE);
                }
            });
        });
    }

    // -- Review modal --
    function getFieldValue(selector, fallback) {
        var el = document.querySelector(selector);
        if (!el || !el.value) return fallback || '—';
        return el.value.trim();
    }

    function getCheckedLabel(name, fallback) {
        var checked = document.querySelector('input[name="' + name + '"]:checked');
        if (!checked) return fallback || '—';
        var card = checked.closest('label');
        if (card) {
            var span = card.querySelector('.card-label, .pill-label');
            if (span) return span.textContent.trim();
        }
        return checked.value;
    }

    function getEmergencyText() {
        if (emergencyCheck && emergencyCheck.checked) return 'Yes';
        return 'No';
    }

    function fieldHasError(groupId) {
        var group = document.getElementById(groupId);
        return group && group.classList.contains('error');
    }

    function reviewField(labelText, value, hasError) {
        var cls = 'review-field';
        if (hasError) cls += ' review-error';
        return '<div class="' + cls + '"><span class="review-label">' + labelText + '</span><span class="review-value">' + value + '</span></div>';
    }

    function buildReviewContent() {
        var html = '';

        html += '<div class="review-section">';
        html += '<div class="review-section-title">Client Details</div>';
        html += reviewField('Name', getFieldValue('#name'), fieldHasError('group-name'));
        html += reviewField('Phone', getFieldValue('#phone'), fieldHasError('group-phone'));
        var emailVal = getFieldValue('#email', '');
        html += reviewField('Email', emailVal || '(not provided)', false);
        html += reviewField('Address', getFieldValue('#address'), fieldHasError('group-address'));
        html += reviewField('Postcode', getFieldValue('#postcode'), fieldHasError('group-postcode'));
        html += '</div>';

        html += '<div class="review-section">';
        html += '<div class="review-section-title">Job Details</div>';
        html += reviewField('Service', getCheckedLabel('service'), fieldHasError('group-service'));
        html += reviewField('Date', getFieldValue('#date'), fieldHasError('group-date'));
        html += reviewField('Time', getCheckedLabel('timeslot'), fieldHasError('group-time'));
        html += reviewField('Emergency', getEmergencyText(), false);
        html += reviewField('Description', getFieldValue('#description'), fieldHasError('group-description'));
        html += '</div>';

        html += '<div class="review-section">';
        html += '<div class="review-section-title">Diagnostic Photos</div>';
        html += '<div class="review-images">';
        var hasImages = false;
        for (var i = 1; i <= 3; i++) {
            var previewEl = document.querySelector('.diagnostic-upload-row:nth-child(' + i + ') .image-preview img');
            if (previewEl) {
                html += '<img src="' + previewEl.src + '" alt="Diagnostic photo ' + i + '">';
                hasImages = true;
            }
        }
        if (!hasImages) {
            html += '<span class="review-empty">No photos uploaded</span>';
        }
        html += '</div>';
        html += '</div>';

        return html;
    }

    function openReview() {
        if (!reviewOverlay || !reviewContent) return;
        reviewContent.innerHTML = buildReviewContent();
        reviewOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeReview() {
        if (!reviewOverlay) return;
        reviewOverlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    if (reviewEditBtn) {
        reviewEditBtn.addEventListener('click', function () {
            closeReview();
            var firstField = document.getElementById('name');
            if (firstField) firstField.focus();
        });
    }

    if (reviewConfirmBtn) {
        reviewConfirmBtn.addEventListener('click', function () {
            closeReview();
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Submitting...';
            }
            form.requestSubmit();
        });
    }

    if (reviewOverlay) {
        reviewOverlay.addEventListener('click', function (event) {
            if (event.target === reviewOverlay) closeReview();
        });
    }

    form.addEventListener('submit', function (event) {
        if (!validateForm()) {
            event.preventDefault();
            return;
        }

        if (reviewOverlay && !reviewOverlay.classList.contains('active')) {
            event.preventDefault();
            openReview();
            return;
        }

        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Submitting...';
        }
    });

    // -- Success overlay --
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
        if (event.key === 'Escape') {
            if (reviewOverlay && reviewOverlay.classList.contains('active')) {
                closeReview();
            } else if (successOverlay && successOverlay.classList.contains('active')) {
                closeSuccess();
            }
        }
    });
})();
