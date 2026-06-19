/* =====================================================
   CuidaCare — prontuario.js
   Tela "Prontuário": popup de "Adicionar Anotação".
   ===================================================== */

(function () {
    "use strict";

    function configurarModal(modal) {
        if (!modal) return null;
        function abrir() {
            modal.hidden = false;
            document.body.style.overflow = "hidden";
            var primeiro = modal.querySelector("input, textarea, select");
            if (primeiro) setTimeout(function () { primeiro.focus(); }, 50);
        }
        function fechar() {
            modal.hidden = true;
            document.body.style.overflow = "";
        }
        modal.querySelectorAll("[data-close]").forEach(function (el) {
            el.addEventListener("click", fechar);
        });
        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape" && !modal.hidden) fechar();
        });
        if (!modal.hidden) document.body.style.overflow = "hidden";
        return { abrir: abrir, fechar: fechar };
    }

    var modal = configurarModal(document.getElementById("modal-anotacao"));
    var abrir = document.getElementById("abrir-anotacao");
    if (modal && abrir) {
        abrir.addEventListener("click", modal.abrir);
    }
})();
