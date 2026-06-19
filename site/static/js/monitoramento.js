/* =====================================================
   CuidaCare — monitoramento.js
   Tela "Ponto" (familiar): popup de editar plantão.
   ===================================================== */

(function () {
    "use strict";

    var modal = document.getElementById("modal-editar-plantao");
    if (!modal) return;

    var form = document.getElementById("form-editar-plantao");
    var sub = document.getElementById("modal-ep-sub");
    var entrada = document.getElementById("ep_entrada");
    var saida = document.getElementById("ep_saida");

    function abrir() {
        modal.hidden = false;
        document.body.style.overflow = "hidden";
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

    document.querySelectorAll(".mon-edit").forEach(function (botao) {
        botao.addEventListener("click", function () {
            if (form) form.action = botao.getAttribute("data-action") || "";
            if (entrada) entrada.value = botao.getAttribute("data-entrada") || "";
            if (saida) saida.value = botao.getAttribute("data-saida") || "";
            if (sub) sub.textContent = "Ajuste os horários do plantão de " +
                (botao.getAttribute("data-nome") || "cuidador") + ".";
            abrir();
        });
    });
})();
