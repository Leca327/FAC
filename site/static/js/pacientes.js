/* =====================================================
   CuidaCare — pacientes.js
   Popup "Novo Paciente": abrir/fechar e campos só-dígitos.
   ===================================================== */

(function () {
    "use strict";

    var modal = document.getElementById("modal-paciente");
    var abrir = document.getElementById("abrir-novo-paciente");
    if (!modal) return;

    function abrirModal() {
        modal.hidden = false;
        document.body.style.overflow = "hidden";
        var primeiro = modal.querySelector("input, textarea");
        if (primeiro) setTimeout(function () { primeiro.focus(); }, 50);
    }

    function fecharModal() {
        modal.hidden = true;
        document.body.style.overflow = "";
    }

    if (abrir) abrir.addEventListener("click", abrirModal);

    modal.querySelectorAll("[data-close]").forEach(function (el) {
        el.addEventListener("click", fecharModal);
    });

    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && !modal.hidden) fecharModal();
    });

    // Se o servidor reabriu o modal por causa de erros, leva o foco a ele
    if (!modal.hidden) {
        document.body.style.overflow = "hidden";
    }

    // CPF / telefone: apenas dígitos
    modal.querySelectorAll(".js-digits").forEach(function (input) {
        input.addEventListener("input", function () {
            var limpo = input.value.replace(/\D/g, "");
            if (input.value !== limpo) input.value = limpo;
        });
        input.addEventListener("keypress", function (e) {
            if (e.key.length === 1 && /\D/.test(e.key)) e.preventDefault();
        });
    });
})();
