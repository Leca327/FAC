/* =====================================================
   CuidaCare — familia.js
   Abas (Cards/Tabela) e popups de convidar/editar membro.
   ===================================================== */

(function () {
    "use strict";

    // ---------- Abas Cards / Tabela ----------
    var tabs = document.querySelectorAll(".med-tab");
    var views = {
        cards: document.getElementById("view-cards"),
        tabela: document.getElementById("view-tabela"),
    };
    var CHAVE_VIEW = "cuidacare:familia-view";

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

    // ---------- Convidar ----------
    var modalConvidar = configurarModal(document.getElementById("modal-convidar"));
    var abrirConvidar = document.getElementById("abrir-convidar");
    if (modalConvidar && abrirConvidar) {
        abrirConvidar.addEventListener("click", modalConvidar.abrir);
    }

    // ---------- Editar ----------
    var modalEditarEl = document.getElementById("modal-editar");
    var modalEditar = configurarModal(modalEditarEl);
    if (modalEditar && modalEditarEl) {
        var form = document.getElementById("form-editar");
        function preencher(id, valor) {
            var campo = document.getElementById(id);
            if (campo) campo.value = valor || "";
        }
        document.querySelectorAll(".fam-edit").forEach(function (botao) {
            botao.addEventListener("click", function () {
                if (form) form.action = botao.getAttribute("data-action") || "";
                preencher("ed_nome", botao.getAttribute("data-nome"));
                preencher("ed_telefone", botao.getAttribute("data-telefone"));
                preencher("ed_vinculo", botao.getAttribute("data-vinculo"));
                modalEditar.abrir();
            });
        });
    }
})();
