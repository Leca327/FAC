/* =====================================================
   CuidaCare — ponto.js
   - Relógio ao vivo no cartão de "Meu Ponto".
   - Captura da localização (GPS) no check-in (RN01).
   - Popup de "Editar ponto de hoje".
   ===================================================== */

(function () {
    "use strict";

    // ---------- Relógio ao vivo ----------
    var clock = document.querySelector("[data-clock]");
    if (clock) {
        var tick = function () {
            var agora = new Date();
            var hh = String(agora.getHours()).padStart(2, "0");
            var mm = String(agora.getMinutes()).padStart(2, "0");
            clock.textContent = hh + ":" + mm;
        };
        tick();
        setInterval(tick, 1000 * 15);
    }

    // ---------- Check-in com localização (GPS) ----------
    var geoForm = document.querySelector("[data-geo-form]");
    if (geoForm) {
        var status = document.querySelector("[data-geo-status]");
        var enviando = false;

        geoForm.addEventListener("submit", function (e) {
            if (enviando) return;            // segunda passada: deixa enviar
            e.preventDefault();

            if (!navigator.geolocation) {
                enviando = true;
                geoForm.submit();            // sem suporte a GPS → servidor decide
                return;
            }
            if (status) status.textContent = "Obtendo sua localização…";
            navigator.geolocation.getCurrentPosition(
                function (pos) {
                    geoForm.querySelector("input[name=lat]").value = pos.coords.latitude;
                    geoForm.querySelector("input[name=lng]").value = pos.coords.longitude;
                    enviando = true;
                    geoForm.submit();
                },
                function () {
                    // Permissão negada/indisponível: envia sem coords; o
                    // servidor bloqueia se o paciente exigir GPS.
                    if (status) status.textContent = "Localização indisponível.";
                    enviando = true;
                    geoForm.submit();
                },
                { enableHighAccuracy: true, timeout: 10000 }
            );
        });
    }

    // ---------- Popup de editar ponto ----------
    var modal = document.getElementById("modal-editar-ponto");
    var abrir = document.getElementById("abrir-editar-ponto");
    if (modal && abrir) {
        var fechar = function () {
            modal.hidden = true;
            document.body.style.overflow = "";
        };
        abrir.addEventListener("click", function () {
            modal.hidden = false;
            document.body.style.overflow = "hidden";
        });
        modal.querySelectorAll("[data-close]").forEach(function (el) {
            el.addEventListener("click", fechar);
        });
        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape" && !modal.hidden) fechar();
        });
    }
})();
