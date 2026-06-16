/* =====================================================
   CuidaCare — medicos.js
   Abas (Cards/Tabela) e popups de cadastro/edição de médico.
   ===================================================== */

(function () {
    "use strict";

    // ---------- Abas Cards / Tabela ----------
    var tabs = document.querySelectorAll(".med-tab");
    var views = {
        cards: document.getElementById("view-cards"),
        tabela: document.getElementById("view-tabela"),
    };
    var CHAVE_VIEW = "cuidacare:medicos-view";

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
            var primeiro = modal.querySelector("input, select, textarea");
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

    // ---------- Popup "Novo Médico" ----------
    var modalNovo = configurarModal(document.getElementById("modal-medico"));
    var abrirNovo = document.getElementById("abrir-novo-medico");
    if (modalNovo && abrirNovo) {
        abrirNovo.addEventListener("click", modalNovo.abrir);
    }

    // ---------- Popup "Editar Médico" ----------
    var modalEditarEl = document.getElementById("modal-editar");
    var modalEditar = configurarModal(modalEditarEl);
    if (modalEditar && modalEditarEl) {
        var form = document.getElementById("form-editar");
        var campos = [
            "nome", "tipo", "especialidade", "crm_cnpj",
            "telefone", "email", "endereco", "cidade", "uf",
        ];
        function preencher(campo, valor) {
            var el = document.getElementById("edit_" + campo);
            if (el) el.value = valor || "";
        }
        document.querySelectorAll(".med-edit").forEach(function (botao) {
            botao.addEventListener("click", function () {
                if (form) form.action = botao.getAttribute("data-action") || "";
                campos.forEach(function (campo) {
                    preencher(campo, botao.getAttribute("data-" + campo));
                });
                modalEditar.abrir();
            });
        });
    }

    // ---------- Campos só-dígitos (telefone) ----------
    document.querySelectorAll(".js-digits").forEach(function (input) {
        input.addEventListener("input", function () {
            var limpo = input.value.replace(/\D/g, "");
            if (input.value !== limpo) input.value = limpo;
        });
    });
})();
