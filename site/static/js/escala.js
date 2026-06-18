/* =====================================================
   CuidaCare — escala.js
   Editor de padrão (rodízio/semanal) e modal "Alterar Dia".
   ===================================================== */

(function () {
    "use strict";

    // ---------- Editor: alternar Rodízio / Semanal por turno ----------
    function sincronizarTipo(turno) {
        var marcado = document.querySelector('.js-tipo[data-turno="' + turno + '"]:checked');
        if (!marcado) return;
        var rod = document.querySelector('.js-bloco-rodizio[data-turno="' + turno + '"]');
        var sem = document.querySelector('.js-bloco-semanal[data-turno="' + turno + '"]');
        var ehRodizio = marcado.value === "rodizio";
        if (rod) rod.style.display = ehRodizio ? "" : "none";
        if (sem) sem.style.display = ehRodizio ? "none" : "";
    }

    document.querySelectorAll(".js-tipo").forEach(function (radio) {
        radio.addEventListener("change", function () {
            sincronizarTipo(radio.getAttribute("data-turno"));
        });
    });
    document.querySelectorAll("fieldset[data-turno]").forEach(function (fs) {
        sincronizarTipo(fs.getAttribute("data-turno"));
    });

    // ---------- Editor: adicionar / remover pessoa no rodízio ----------
    var template = document.getElementById("esc-seq-template");

    document.addEventListener("click", function (e) {
        var add = e.target.closest(".js-seq-add");
        if (add && template) {
            var turno = add.getAttribute("data-turno");
            var seq = document.querySelector('.esc-seq[data-turno="' + turno + '"]');
            var linha = template.content.firstElementChild.cloneNode(true);
            linha.querySelector("select").setAttribute("name", "rodizio_" + turno);
            seq.appendChild(linha);
            return;
        }
        var rm = e.target.closest(".js-seq-rm");
        if (rm) {
            var row = rm.closest(".esc-seq__row");
            var container = row.parentNode;
            if (container.querySelectorAll(".esc-seq__row").length > 1) {
                row.remove();
            } else {
                row.querySelector("select").selectedIndex = 0;
            }
        }
    });

    // ---------- Modal: Alterar Dia ----------
    var modal = document.getElementById("modal-alterar-dia");
    if (modal) {
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

        var botao = document.getElementById("abrir-alterar-dia");
        if (botao) botao.addEventListener("click", abrir);

        function setSelect(id, valor) {
            var el = document.getElementById(id);
            if (el) el.value = valor || "";
        }

        // Clicar numa célula da tabela abre o modal já preenchido.
        document.querySelectorAll(".esc-cell--click").forEach(function (cell) {
            cell.addEventListener("click", function () {
                setSelect("ad_data", cell.getAttribute("data-data"));
                setSelect("ad_turno", cell.getAttribute("data-turno"));
                setSelect("ad_cuidador", cell.getAttribute("data-cuidador"));
                abrir();
            });
        });
    }
})();
