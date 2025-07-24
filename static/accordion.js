document.addEventListener("DOMContentLoaded", function () {
   const accordions = document.querySelectorAll(".accordion");

    accordions.forEach((accordion) => {
      accordion.addEventListener("click", function () {
        const isActive = this.classList.contains("active");

        // Close all panels
        document.querySelectorAll(".accordion").forEach((acc) => acc.classList.remove("active"));
        document.querySelectorAll(".panel").forEach((panel) => panel.style.maxHeight = null);

        // If not already active, open this one
        if (!isActive) {
          this.classList.add("active");
          const panel = this.nextElementSibling;
          panel.style.maxHeight = panel.scrollHeight + "px";
        }
      });
    });
 });




