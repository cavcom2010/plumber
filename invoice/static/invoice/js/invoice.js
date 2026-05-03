(function () {
    'use strict';

    // -- Product row management (manage form) --
    var container = document.getElementById('products-container');
    var addBtn = document.getElementById('add-product-btn');
    if (container && addBtn) {
        var rowCount = container.querySelectorAll('.inv-product-row').length;

        addBtn.addEventListener('click', function () {
            var idx = rowCount;
            var row = document.createElement('div');
            row.className = 'inv-product-row';
            row.innerHTML =
                '<input type="hidden" name="product_id_' + idx + '" value="">' +
                '<input type="text" name="product_name_' + idx + '" class="inv-product-col inv-product-col-name" placeholder="e.g. Worcester Bosch Greenstar 8000">' +
                '<input type="text" name="product_serial_' + idx + '" class="inv-product-col inv-product-col-serial" placeholder="Serial #">' +
                '<input type="number" name="product_price_' + idx + '" class="inv-product-col inv-product-col-price" step="0.01" min="0" placeholder="0">' +
                '<input type="number" name="product_qty_' + idx + '" class="inv-product-col inv-product-col-qty" min="1" value="1">' +
                '<input type="text" name="product_warranty_' + idx + '" class="inv-product-col inv-product-col-warranty" placeholder="e.g. 5 years">' +
                '<label class="inv-product-col inv-product-col-delete"><input type="checkbox" name="delete_product_' + idx + '" value="1"></label>';

            container.appendChild(row);
            rowCount++;

            var emptyMsg = container.querySelector('.inv-empty');
            if (emptyMsg) emptyMsg.remove();
        });
    }

    // -- Image preview (manage form) --
    function initImagePreviews() {
        ['new-before-image', 'new-after-image'].forEach(function (inputId) {
            var input = document.getElementById(inputId);
            if (!input) return;

            var preview = document.createElement('div');
            preview.className = 'inv-image-preview';
            input.parentElement.appendChild(preview);

            input.addEventListener('change', function () {
                if (this.files && this.files[0]) {
                    var reader = new FileReader();
                    reader.onload = function (e) {
                        preview.innerHTML =
                            '<img src="' + e.target.result + '" alt="Preview">' +
                            '<button type="button" class="inv-preview-remove" aria-label="Remove photo">Remove</button>';
                        preview.classList.add('has-image');
                    };
                    reader.readAsDataURL(this.files[0]);
                }
            });

            preview.addEventListener('click', function (e) {
                if (e.target.classList.contains('inv-preview-remove')) {
                    input.value = '';
                    preview.innerHTML = '';
                    preview.classList.remove('has-image');
                }
            });
        });
    }

    initImagePreviews();

    // -- Review modal (create form) --
    var createForm = document.querySelector('form[action*="invoice"][method="post"]:not([enctype])') ||
                     document.getElementById('invoiceCreateForm');
    var reviewOverlay = document.getElementById('invReviewOverlay');
    var reviewContent = document.getElementById('invReviewContent');
    var reviewEditBtn = document.getElementById('invReviewEditBtn');
    var reviewConfirmBtn = document.getElementById('invReviewConfirmBtn');

    if (createForm && reviewOverlay && reviewContent) {
        function getFieldValue(el) {
            if (!el) return '—';
            return el.value.trim() || '—';
        }

        function getCheckedLabel(name) {
            var checked = document.querySelector('input[name="' + name + '"]:checked');
            if (!checked) return '—';
            var card = checked.closest('.inv-radio-card');
            if (card) {
                var span = card.querySelector('span');
                if (span) return span.textContent.trim();
            }
            return checked.value;
        }

        function fieldHasError(wrapperSelector) {
            var el = document.querySelector(wrapperSelector);
            return el && el.classList.contains('inv-error');
        }

        function reviewField(labelText, value, hasError) {
            var cls = 'inv-review-field';
            if (hasError) cls += ' inv-review-error';
            return '<div class="' + cls + '"><span class="inv-review-label">' + labelText + '</span><span class="inv-review-value">' + value + '</span></div>';
        }

        function buildReviewContent() {
            var html = '';
            html += '<div class="inv-review-section">';
            html += '<div class="inv-review-section-title">Client Details</div>';
            html += reviewField('Name', getFieldValue(document.getElementById('inv-name')), fieldHasError('.inv-form-group:has(#inv-name)'));
            html += reviewField('Phone', getFieldValue(document.getElementById('inv-phone')), fieldHasError('.inv-form-group:has(#inv-phone)'));
            html += reviewField('Email', getFieldValue(document.getElementById('inv-email')) || '(not provided)', false);
            html += reviewField('Address', getFieldValue(document.getElementById('inv-address')), fieldHasError('.inv-form-group:has(#inv-address)'));
            html += reviewField('Postcode', getFieldValue(document.getElementById('inv-postcode')), fieldHasError('.inv-form-group:has(#inv-postcode)'));
            html += '</div>';

            html += '<div class="inv-review-section">';
            html += '<div class="inv-review-section-title">Job Details</div>';
            html += reviewField('Service', getCheckedLabel('service_type'), fieldHasError('.inv-form-group:has(.inv-radio-grid)'));
            html += reviewField('Description', getFieldValue(document.getElementById('inv-description')), fieldHasError('.inv-form-group:has(#inv-description)'));
            html += '</div>';

            return html;
        }

        function openReview() {
            reviewContent.innerHTML = buildReviewContent();
            reviewOverlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        }

        function closeReview() {
            reviewOverlay.classList.remove('active');
            document.body.style.overflow = '';
        }

        if (reviewEditBtn) {
            reviewEditBtn.addEventListener('click', function () {
                closeReview();
                var firstField = document.getElementById('inv-name');
                if (firstField) firstField.focus();
            });
        }

        if (reviewConfirmBtn) {
            reviewConfirmBtn.addEventListener('click', function () {
                closeReview();
                createForm.requestSubmit();
            });
        }

        if (reviewOverlay) {
            reviewOverlay.addEventListener('click', function (event) {
                if (event.target === reviewOverlay) closeReview();
            });
        }

        createForm.addEventListener('submit', function (event) {
            if (reviewOverlay.classList.contains('active')) {
                return;
            }
            event.preventDefault();
            openReview();
        });

        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape' && reviewOverlay.classList.contains('active')) {
                closeReview();
            }
        });
    }
})();
