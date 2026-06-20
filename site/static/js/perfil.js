/* =====================================================
   CuidaCare — perfil.js
   Alterna a tela "Meu Perfil" entre leitura e edição,
   e envia o formulário ao trocar a foto.
   ===================================================== */

(function () {
    "use strict";

    var form = document.getElementById("perfil-form");
    if (!form) return;

    // Editar só a seção (container) clicada.
    document.querySelectorAll("[data-editar]").forEach(function (botao) {
        botao.addEventListener("click", function () {
            var secao = botao.closest(".pf-section");
            if (secao) secao.classList.add("is-editing");
        });
    });

    // Cancelar: recarrega a tela, descartando as alterações.
    document.querySelectorAll("[data-cancelar]").forEach(function (botao) {
        botao.addEventListener("click", function () {
            window.location = window.location.pathname;
        });
    });

    // "Alterar Foto": ao escolher um arquivo, envia o formulário (salva já).
    var foto = document.getElementById("id_foto");
    if (foto) {
        foto.addEventListener("change", function () {
            if (foto.files && foto.files.length) {
                form.submit();
            }
        });
    }
})();
