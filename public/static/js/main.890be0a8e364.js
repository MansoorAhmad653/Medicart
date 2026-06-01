// MediCart Main JS

document.addEventListener('DOMContentLoaded', function () {

  // --- Auto-dismiss alerts after 5 seconds ---
  const alerts = document.querySelectorAll('.alert.alert-dismissible');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });

  // --- Navbar scroll shadow ---
  const navbar = document.getElementById('mainNav');
  if (navbar) {
    window.addEventListener('scroll', function () {
      if (window.scrollY > 10) {
        navbar.classList.add('scrolled');
      } else {
        navbar.classList.remove('scrolled');
      }
    });
  }

  // --- File upload zone label ---
  const fileInputs = document.querySelectorAll('.file-upload-zone input[type="file"]');
  fileInputs.forEach(function (input) {
    input.addEventListener('change', function () {
      const zone = input.closest('.file-upload-zone');
      const files = input.files;
      if (files.length > 0) {
        const p = zone.querySelector('p');
        if (p) p.textContent = files[0].name;
        zone.style.borderColor = 'var(--primary)';
        zone.style.background = 'var(--primary-light)';
      }
    });
  });

  // --- Drag and drop for upload zones ---
  const uploadZones = document.querySelectorAll('.file-upload-zone');
  uploadZones.forEach(function (zone) {
    zone.addEventListener('dragover', function (e) {
      e.preventDefault();
      zone.style.borderColor = 'var(--primary)';
    });
    zone.addEventListener('dragleave', function () {
      zone.style.borderColor = '';
    });
    zone.addEventListener('drop', function (e) {
      e.preventDefault();
      const input = zone.querySelector('input[type="file"]');
      if (input && e.dataTransfer.files.length > 0) {
        input.files = e.dataTransfer.files;
        input.dispatchEvent(new Event('change'));
      }
    });
  });

  // --- Add to cart button loading state ---
  document.querySelectorAll('form[action*="add"]').forEach(function (form) {
    form.addEventListener('submit', function () {
      const btn = form.querySelector('button[type="submit"]');
      if (btn) {
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
        btn.disabled = true;
      }
    });
  });

  // --- Quantity buttons: prevent negative via double click ---
  document.querySelectorAll('.qty-form').forEach(function (form) {
    const decreaseBtn = form.querySelector('[value="decrease"]');
    const qtyVal = form.querySelector('.qty-val');
    if (decreaseBtn && qtyVal) {
      const currentQty = parseInt(qtyVal.textContent);
      if (currentQty <= 1) {
        decreaseBtn.style.opacity = '0.4';
      }
    }
  });

  // --- Scroll to top button ---
  const scrollBtn = document.createElement('button');
  scrollBtn.id = 'scrollTopBtn';
  scrollBtn.innerHTML = '<i class="bi bi-arrow-up"></i>';
  scrollBtn.style.cssText = `
    position: fixed; bottom: 24px; right: 24px; z-index: 999;
    width: 44px; height: 44px; border-radius: 12px; border: none;
    background: var(--primary); color: white; font-size: 18px;
    display: none; align-items: center; justify-content: center;
    box-shadow: 0 4px 16px rgba(15,110,86,.3); cursor: pointer;
    transition: all 0.22s; opacity: 0;
  `;
  document.body.appendChild(scrollBtn);

  window.addEventListener('scroll', function () {
    if (window.scrollY > 400) {
      scrollBtn.style.display = 'flex';
      setTimeout(() => { scrollBtn.style.opacity = '1'; }, 10);
    } else {
      scrollBtn.style.opacity = '0';
      setTimeout(() => { scrollBtn.style.display = 'none'; }, 220);
    }
  });

  scrollBtn.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  scrollBtn.addEventListener('mouseenter', function () {
    this.style.transform = 'translateY(-3px)';
    this.style.boxShadow = '0 8px 24px rgba(15,110,86,.4)';
  });
  scrollBtn.addEventListener('mouseleave', function () {
    this.style.transform = '';
    this.style.boxShadow = '0 4px 16px rgba(15,110,86,.3)';
  });

});
