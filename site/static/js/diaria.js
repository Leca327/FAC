/* =====================================================
   CuidaCare — diaria.js
   Tela "Medicação Diária": popups de adicionar/editar rotina.
   ===================================================== */

(function () {
    "use strict";

    // ---------- Tag-input de horários ----------
    // Transforma um <input> comum num campo de marcadores: cada horário
    // digitado + espaço/vírgula/Enter vira um "chip". O <input> original
    // vira oculto e continua carregando o valor (CSV) enviado ao servidor.
    function normalizarHorario(texto) {
        var m = /^(\d{1,2}):(\d{1,2})$/.exec(texto);
        if (!m) return texto;
        var hh = Math.min(parseInt(m[1], 10), 99);
        var mm = Math.min(parseInt(m[2], 10), 99);
        return ("0" + hh).slice(-2) + ":" + ("0" + mm).slice(-2);
    }

    function iniciarTagInput(carrier) {
        if (!carrier || carrier.dataset.tagReady) return;
        carrier.dataset.tagReady = "1";

        var placeholder = carrier.getAttribute("placeholder") || "";
        carrier.type = "hidden";

        var wrap = document.createElement("div");
        wrap.className = "taginput";
        var entry = document.createElement("input");
        entry.type = "text";
        entry.className = "taginput__entry";
        entry.setAttribute("placeholder", placeholder);
        entry.setAttribute("autocomplete", "off");
        wrap.appendChild(entry);
        carrier.parentNode.insertBefore(wrap, carrier.nextSibling);

        function tokens() {
            return carrier.value.split(",").map(function (s) {
                return s.trim();
            }).filter(Boolean);
        }
        function salvar(arr) {
            carrier.value = arr.join(", ");
            render();
        }
        function render() {
            wrap.querySelectorAll(".taginput__chip").forEach(function (c) {
                c.remove();
            });
            tokens().forEach(function (t, i) {
                var chip = document.createElement("span");
                chip.className = "taginput__chip";
                chip.textContent = t;
                var x = document.createElement("button");
                x.type = "button";
                x.className = "taginput__remove";
                x.setAttribute("aria-label", "Remover " + t);
                x.innerHTML = "&times;";
                x.addEventListener("click", function () {
                    var arr = tokens();
                    arr.splice(i, 1);
                    salvar(arr);
                    entry.focus();
                });
                chip.appendChild(x);
                wrap.insertBefore(chip, entry);
            });
        }
        function commit() {
            var bruto = entry.value.trim().replace(/,$/, "").trim();
            if (!bruto) { entry.value = ""; return; }
            var valor = normalizarHorario(bruto);
            var arr = tokens();
            if (arr.indexOf(valor) === -1) {
                arr.push(valor);
                salvar(arr);
            }
            entry.value = "";
        }

        entry.addEventListener("keydown", function (e) {
            if (e.key === " " || e.key === "," || e.key === "Enter") {
                e.preventDefault();
                commit();
            } else if (e.key === "Backspace" && entry.value === "") {
                var arr = tokens();
                arr.pop();
                salvar(arr);
            }
        });
        entry.addEventListener("blur", commit);
        wrap.addEventListener("click", function (e) {
            if (e.target === wrap) entry.focus();
        });

        // Permite reconstruir os chips quando o valor muda via JS (edição).
        carrier.atualizarTags = render;
        render();
    }

    document.querySelectorAll(".js-taginput").forEach(iniciarTagInput);

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

        // O servidor pode ter reaberto o modal por erro de validação.
        if (!modal.hidden) document.body.style.overflow = "hidden";

        return { abrir: abrir, fechar: fechar };
    }

    // ---------- Popup "Adicionar remédio à rotina" ----------
    var modalNovo = configurarModal(document.getElementById("modal-rotina"));
    var abrirNovo = document.getElementById("abrir-rotina");
    if (modalNovo && abrirNovo) {
        abrirNovo.addEventListener("click", modalNovo.abrir);
    }

    // ---------- Popup "Editar rotina" ----------
    var modalEditarEl = document.getElementById("modal-rotina-editar");
    var modalEditar = configurarModal(modalEditarEl);
    if (modalEditar && modalEditarEl) {
        var form = document.getElementById("form-rotina-editar");

        function preencher(id, valor) {
            var campo = document.getElementById(id);
            if (campo) campo.value = valor || "";
        }
        function marcar(id, valor) {
            var campo = document.getElementById(id);
            if (campo) campo.checked = valor === "1";
        }

        document.querySelectorAll(".dose__editar").forEach(function (botao) {
            botao.addEventListener("click", function () {
                if (form) form.action = botao.getAttribute("data-action") || "";
                var rotulo = document.getElementById("ed_remedio");
                if (rotulo) {
                    var nome = botao.getAttribute("data-nome") || "";
                    var dosagem = botao.getAttribute("data-dosagem") || "";
                    rotulo.textContent = dosagem ? nome + " — " + dosagem : nome;
                }
                preencher("ed_quantidade", botao.getAttribute("data-quantidade"));
                preencher("ed_horarios", botao.getAttribute("data-horarios"));
                var horariosEl = document.getElementById("ed_horarios");
                if (horariosEl && horariosEl.atualizarTags) horariosEl.atualizarTags();
                preencher("ed_inicio", botao.getAttribute("data-inicio"));
                preencher("ed_fim", botao.getAttribute("data-fim"));
                preencher("ed_obs", botao.getAttribute("data-obs"));
                marcar("ed_seg", botao.getAttribute("data-seg"));
                marcar("ed_ter", botao.getAttribute("data-ter"));
                marcar("ed_qua", botao.getAttribute("data-qua"));
                marcar("ed_qui", botao.getAttribute("data-qui"));
                marcar("ed_sex", botao.getAttribute("data-sex"));
                marcar("ed_sab", botao.getAttribute("data-sab"));
                marcar("ed_dom", botao.getAttribute("data-dom"));
                modalEditar.abrir();
            });
        });
    }
})();
