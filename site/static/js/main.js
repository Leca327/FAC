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

    // -------------------------------------------------------------------
    // Limpeza de modais ao fechar
    // Sempre que QUALQUER popup (.modal) é fechado (o atributo `hidden`
    // passa a estar presente), os formulários dentro dele são resetados.
    // Assim o texto digitado não "fica lá" ao reabrir, qualquer que tenha
    // sido a forma de fechar (clique no X/overlay, tecla Esc, etc.).
    // Usa MutationObserver para captar todas as formas de fechamento,
    // independentemente do JS específico de cada tela.
    // -------------------------------------------------------------------
    document.querySelectorAll(".modal").forEach(function (modal) {
        const observer = new MutationObserver(function () {
            if (modal.hidden) {
                modal.querySelectorAll("form").forEach(function (form) {
                    form.reset();
                });
                // Limpa também mensagens de erro de validação exibidas.
                modal.querySelectorAll(".field__error").forEach(function (el) {
                    el.remove();
                });
            }
        });
        observer.observe(modal, { attributes: true, attributeFilter: ["hidden"] });
    });
})();
