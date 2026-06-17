/* =====================================================
   CuidaCare — consultas.js
   Tela "Consultas e Exames": popups de novo/editar agendamento
   e de marcar como realizada (com resultado).
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

    function preencher(id, valor) {
        var campo = document.getElementById(id);
        if (campo) campo.value = valor || "";
    }

    // Mostra/oculta o campo "Título" conforme o médico selecionado:
    // - médico            -> some (título = especialidade dele);
    // - clínica/laboratório -> aparece como "Qual Exame?" (obrigatório);
    // - nada selecionado   -> some.
    function atualizarTitulo(select) {
        var campo = document.getElementById(select.getAttribute("data-titulo-campo"));
        if (!campo) return;
        var label = document.getElementById(select.getAttribute("data-titulo-label"));
        var input = campo.querySelector("input");
        var opt = select.options[select.selectedIndex];
        var tipo = opt ? opt.getAttribute("data-tipo") : "";

        if (tipo === "clinica" || tipo === "laboratorio") {
            campo.hidden = false;
            if (label) label.textContent = "Qual Exame?";
            if (input) input.required = true;
        } else {
            campo.hidden = true;
            if (input) input.required = false;
        }
    }

    var medicoSelects = document.querySelectorAll(".js-medico-select");
    medicoSelects.forEach(function (sel) {
        sel.addEventListener("change", function () { atualizarTitulo(sel); });
        atualizarTitulo(sel);
    });

    // ---------- Novo Agendamento ----------
    var modalNovo = configurarModal(document.getElementById("modal-consulta"));
    var abrirNovo = document.getElementById("abrir-consulta");
    if (modalNovo && abrirNovo) {
        abrirNovo.addEventListener("click", modalNovo.abrir);
    }

    // ---------- Editar Agendamento ----------
    var modalEditarEl = document.getElementById("modal-consulta-editar");
    var modalEditar = configurarModal(modalEditarEl);
    if (modalEditar && modalEditarEl) {
        var formEd = document.getElementById("form-consulta-editar");
        document.querySelectorAll(".cons__editar").forEach(function (botao) {
            botao.addEventListener("click", function () {
                if (formEd) formEd.action = botao.getAttribute("data-action") || "";
                preencher("ec_titulo", botao.getAttribute("data-titulo"));
                preencher("ec_medico", botao.getAttribute("data-medico"));
                preencher("ec_data", botao.getAttribute("data-data"));
                preencher("ec_hora", botao.getAttribute("data-hora"));
                preencher("ec_obs", botao.getAttribute("data-obs"));
                // Ajusta o campo Título conforme o tipo do médico selecionado.
                var selMed = document.getElementById("ec_medico");
                if (selMed) atualizarTitulo(selMed);
                modalEditar.abrir();
            });
        });
    }

    // ---------- Marcar como realizada (resultado) ----------
    var modalResEl = document.getElementById("modal-resultado");
    var modalRes = configurarModal(modalResEl);
    if (modalRes && modalResEl) {
        var formRes = document.getElementById("form-resultado");
        var sub = document.getElementById("modal-resultado-sub");
        var texto = document.getElementById("res_texto");
        document.querySelectorAll(".cons__marcar").forEach(function (botao) {
            botao.addEventListener("click", function () {
                if (formRes) formRes.action = botao.getAttribute("data-action") || "";
                if (texto) texto.value = "";
                if (sub) {
                    var titulo = botao.getAttribute("data-titulo") || "compromisso";
                    sub.textContent = "Registre o resultado de " + titulo + ".";
                }
                modalRes.abrir();
            });
        });
    }
})();
