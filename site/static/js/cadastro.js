/* =====================================================
   CuidaCare — cadastro.js
   Cadastro em etapas: mostra uma etapa por vez e só avança
   quando os campos da etapa atual estão válidos.
   ===================================================== */

(function () {
    "use strict";

    var form = document.getElementById("cadastro-form");
    if (!form || !form.hasAttribute("data-wizard")) return;

    var steps = Array.prototype.slice.call(form.querySelectorAll(".wizard-step"));
    var dots = Array.prototype.slice.call(document.querySelectorAll(".wizard-progress__dot"));
    var btnVoltar = form.querySelector("[data-voltar]");
    var btnProximo = form.querySelector("[data-proximo]");
    var btnFinalizar = form.querySelector("[data-finalizar]");
    var total = steps.length;
    var atual = 0;

    function mostrar(i) {
        atual = i;
        steps.forEach(function (s, idx) { s.hidden = idx !== i; });
        dots.forEach(function (d, idx) {
            d.classList.toggle("is-active", idx <= i);
        });
        btnVoltar.hidden = i === 0;
        btnProximo.hidden = i === total - 1;
        btnFinalizar.hidden = i !== total - 1;
        var foco = steps[i].querySelector("input, select");
        if (foco) foco.focus();
    }

    // Valida só os campos da etapa atual (HTML5 + match de senha).
    function etapaValida() {
        var campos = steps[atual].querySelectorAll("input, select");
        for (var k = 0; k < campos.length; k++) {
            if (!campos[k].checkValidity()) {
                campos[k].reportValidity();
                return false;
            }
        }
        var senha = steps[atual].querySelector('input[name="password"]');
        var conf = steps[atual].querySelector('input[name="confirmar_senha"]');
        if (senha && conf && senha.value !== conf.value) {
            conf.setCustomValidity("As senhas não coincidem.");
            conf.reportValidity();
            conf.setCustomValidity("");
            return false;
        }
        return true;
    }

    btnProximo.addEventListener("click", function () {
        if (etapaValida() && atual < total - 1) mostrar(atual + 1);
    });
    btnVoltar.addEventListener("click", function () {
        if (atual > 0) mostrar(atual - 1);
    });

    // Se o servidor devolveu erros, revela todas as etapas para o usuário
    // ver/corrigir, sem o passo a passo.
    if (form.hasAttribute("data-tem-erros")) {
        steps.forEach(function (s) { s.hidden = false; });
        btnProximo.hidden = true;
        btnVoltar.hidden = true;
        btnFinalizar.hidden = false;
        dots.forEach(function (d) { d.classList.add("is-active"); });
    } else {
        mostrar(0);
    }
})();
