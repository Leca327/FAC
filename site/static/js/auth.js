/* =====================================================
   CuidaCare — auth.js
   Interações das telas de login e cadastro:
   - mostrar/ocultar senha (ícone de olho)
   - campos numéricos (CPF/CEP) só aceitam dígitos
   ===================================================== */

(function () {
    "use strict";

    var EYE =
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7Z"/><circle cx="12" cy="12" r="3"/></svg>';
    var EYE_OFF =
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20C5 20 1 13 1 13a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 7 11 7a18.5 18.5 0 0 1-2.16 3.19M1 1l22 22"/><path d="M9.88 9.88a3 3 0 0 0 4.24 4.24"/></svg>';

    // ---- Mostrar / ocultar senha ----
    document.querySelectorAll(".js-password").forEach(function (input) {
        var wrap = input.closest(".password-wrap");
        if (!wrap) return;

        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "password-toggle";
        btn.setAttribute("aria-label", "Mostrar senha");
        btn.innerHTML = EYE;
        wrap.appendChild(btn);

        btn.addEventListener("click", function () {
            var mostrar = input.type === "password";
            input.type = mostrar ? "text" : "password";
            btn.innerHTML = mostrar ? EYE_OFF : EYE;
            btn.setAttribute("aria-label", mostrar ? "Ocultar senha" : "Mostrar senha");
            input.focus();
        });
    });

    // ---- CPF / CEP: apenas dígitos ----
    document.querySelectorAll(".js-digits").forEach(function (input) {
        input.addEventListener("input", function () {
            var limpo = input.value.replace(/\D/g, "");
            if (input.value !== limpo) {
                input.value = limpo;
            }
        });
        // Bloqueia tecla não numérica (mantém teclas de controle)
        input.addEventListener("keypress", function (e) {
            if (e.key.length === 1 && /\D/.test(e.key)) {
                e.preventDefault();
            }
        });
    });

    // ---- Popup: recuperar senha ----
    var modal = document.getElementById("modal-recuperar");
    var abrir = document.getElementById("abrir-recuperar");

    if (modal && abrir) {
        var form = document.getElementById("form-recuperar");
        var feedback = document.getElementById("rec-feedback");
        var submit = document.getElementById("rec-submit");
        var emailInput = document.getElementById("rec-email");

        function abrirModal(e) {
            if (e) e.preventDefault();
            modal.hidden = false;
            document.body.style.overflow = "hidden";
            setTimeout(function () { emailInput.focus(); }, 50);
        }

        function fecharModal() {
            modal.hidden = true;
            document.body.style.overflow = "";
        }

        function mostrarFeedback(texto, tipo) {
            feedback.hidden = false;
            feedback.textContent = texto;
            feedback.className = "modal__feedback modal__feedback--" + tipo;
        }

        abrir.addEventListener("click", abrirModal);

        modal.querySelectorAll("[data-close]").forEach(function (el) {
            el.addEventListener("click", fecharModal);
        });

        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape" && !modal.hidden) fecharModal();
        });

        form.addEventListener("submit", function (e) {
            e.preventDefault();
            submit.disabled = true;
            submit.textContent = "Enviando...";

            fetch(form.dataset.url, {
                method: "POST",
                headers: { "X-Requested-With": "XMLHttpRequest" },
                body: new FormData(form),
            })
                .then(function (r) { return r.json().then(function (d) { return { status: r.status, data: d }; }); })
                .then(function (res) {
                    if (res.data.ok) {
                        mostrarFeedback(res.data.mensagem, "ok");
                        form.querySelector(".field").style.display = "none";
                        submit.style.display = "none";
                    } else {
                        mostrarFeedback(res.data.erro || "Não foi possível enviar.", "erro");
                        submit.disabled = false;
                        submit.textContent = "Enviar nova senha";
                    }
                })
                .catch(function () {
                    mostrarFeedback("Erro de conexão. Tente novamente.", "erro");
                    submit.disabled = false;
                    submit.textContent = "Enviar nova senha";
                });
        });
    }
})();
