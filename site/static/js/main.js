/* =====================================================
   CuidaCare — main.js
   Interatividade básica em JavaScript vanilla (seção 2.7).
   ===================================================== */

(function () {
    "use strict";

    // Menu hambúrguer (navbar colapsável — seção 2.7.4)
    const navbar = document.querySelector(".navbar");
    const toggle = document.querySelector(".navbar__toggle");

    if (toggle && navbar) {
        toggle.addEventListener("click", function () {
            const isOpen = navbar.classList.toggle("is-open");
            toggle.setAttribute("aria-expanded", String(isOpen));
            toggle.setAttribute("aria-label", isOpen ? "Fechar menu" : "Abrir menu");
        });

        // Fecha o menu ao clicar em um link
        navbar.querySelectorAll(".navbar__nav a").forEach(function (link) {
            link.addEventListener("click", function () {
                navbar.classList.remove("is-open");
                toggle.setAttribute("aria-expanded", "false");
            });
        });
    }
})();
