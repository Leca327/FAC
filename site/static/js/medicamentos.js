/* =====================================================
   CuidaCare — medicamentos.js
   Abas (Cards/Tabela) e popups de cadastro/edição de medicamento.
   ===================================================== */

(function () {
    "use strict";

    // ---------- Abas Cards / Tabela ----------
    // A aba escolhida é lembrada (localStorage) para sobreviver ao reload
    // que acontece ao buscar/ordenar (o toolbar é um form GET).
    var tabs = document.querySelectorAll(".med-tab");
    var views = {
        cards: document.getElementById("view-cards"),
        tabela: document.getElementById("view-tabela"),
    };
    var CHAVE_VIEW = "cuidacare:med-view";

    function ativarView(alvo) {
        if (!views[alvo]) alvo = "cards";
        tabs.forEach(function (t) {
            t.classList.toggle("is-active", t.getAttribute("data-view") === alvo);
        });
        Object.keys(views).forEach(function (chave) {
            if (views[chave]) views[chave].hidden = chave !== alvo;
        });
    }

    tabs.forEach(function (tab) {
        tab.addEventListener("click", function () {
            var alvo = tab.getAttribute("data-view");
            try { localStorage.setItem(CHAVE_VIEW, alvo); } catch (e) {}
            ativarView(alvo);
        });
    });

    try {
        var salva = localStorage.getItem(CHAVE_VIEW);
        if (salva) ativarView(salva);
    } catch (e) {}

    // ---------- Infra de modal ----------
    function configurarModal(modal) {
        if (!modal) return null;

        function abrir() {
            modal.hidden = false;
            document.body.style.overflow = "hidden";
            var primeiro = modal.querySelector("input, textarea");
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

        // O servidor pode ter reaberto o modal por erro de validação
        if (!modal.hidden) document.body.style.overflow = "hidden";

        return { abrir: abrir, fechar: fechar };
    }

    // ---------- Popup "Novo Medicamento" ----------
    var modalNovo = configurarModal(document.getElementById("modal-medicamento"));
    var abrirNovo = document.getElementById("abrir-novo-medicamento");
    if (modalNovo && abrirNovo) {
        abrirNovo.addEventListener("click", modalNovo.abrir);
    }

    // ---------- Popup "Editar Medicamento" ----------
    var modalEditarEl = document.getElementById("modal-editar");
    var modalEditar = configurarModal(modalEditarEl);
    if (modalEditar && modalEditarEl) {
        var form = document.getElementById("form-editar");
        function preencher(id, valor) {
            var campo = document.getElementById(id);
            if (campo) campo.value = valor || "";
        }
        document.querySelectorAll(".med-edit").forEach(function (botao) {
            botao.addEventListener("click", function () {
                if (form) form.action = botao.getAttribute("data-action") || "";
                preencher("edit_nome", botao.getAttribute("data-nome"));
                preencher("edit_dosagem", botao.getAttribute("data-dosagem"));
                preencher("edit_forma", botao.getAttribute("data-forma"));
                preencher("edit_medico", botao.getAttribute("data-medico"));
                modalEditar.abrir();
            });
        });
    }
})();
