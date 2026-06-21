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

    function avancar() {
        if (etapaValida() && atual < total - 1) mostrar(atual + 1);
    }

    btnProximo.addEventListener("click", avancar);
    btnVoltar.addEventListener("click", function () {
        if (atual > 0) mostrar(atual - 1);
    });

    // O form usa novalidate, então um Enter num campo dispara o submit nativo
    // (que iria direto ao servidor e revelaria todas as etapas). Enquanto não
    // estiver na última etapa, o Enter age como "Próximo": valida a etapa atual
    // e avança — ou aponta o erro e fica onde está. Só na última etapa o envio
    // ao servidor acontece de fato (e mesmo assim só se a etapa estiver válida).
    form.addEventListener("submit", function (e) {
        if (atual < total - 1) {
            e.preventDefault();
            avancar();
        } else if (!etapaValida()) {
            e.preventDefault();
        }
    });

    // Se o servidor devolveu erros (validações que só existem no backend, ex.:
    // CPF/e-mail já cadastrados), em vez de revelar tudo, leva o usuário à
    // PRIMEIRA etapa que contém um campo com erro — mantendo o passo a passo.
    if (form.hasAttribute("data-tem-erros")) {
        var passoComErro = 0;
        for (var i = 0; i < steps.length; i++) {
            if (steps[i].querySelector(".field__error")) {
                passoComErro = i;
                break;
            }
        }
        mostrar(passoComErro);
    } else {
        mostrar(0);
    }
})();
