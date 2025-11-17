(function () {
  const isAjax = (element) =>
    element && element.hasAttribute("data-no-spinner");

  document.addEventListener("DOMContentLoaded", function () {
    const overlay = document.getElementById("global-spinner-overlay");
    if (!overlay) return;

    const show = () => overlay.classList.add("active");
    const hide = () => overlay.classList.remove("active");

    // Cuando la página termina de cargar, ocultamos el spinner inicial
    window.addEventListener("load", function () {
      hide();
    });

    // Mostrar spinner al enviar formularios (salvo que marquemos data-no-spinner)
    document.querySelectorAll("form").forEach((form) => {
      form.addEventListener("submit", function () {
        if (isAjax(form)) return;
        show();
      });
    });

    // Mostrar spinner al hacer clic en enlaces o botones con data-spinner
    document
      .querySelectorAll("a[data-spinner], button[data-spinner]")
      .forEach((el) => {
        el.addEventListener("click", function () {
          show();
        });
      });
  });
})();
