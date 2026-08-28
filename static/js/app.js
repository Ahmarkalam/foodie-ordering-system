document.addEventListener("DOMContentLoaded",()=>{document.querySelectorAll(".heart").forEach(b=>b.addEventListener("click",async e=>{e.preventDefault();if(!document.body.dataset.logged){location.href="/login";return}const r=await fetch("/favorite/"+b.dataset.food,{method:"POST"});if(r.ok){const x=await r.json();b.classList.toggle("liked",x.favorite);b.textContent=x.favorite?"♥":"♡"}}));document.querySelectorAll("[data-plus]").forEach(b=>b.onclick=()=>{let i=document.querySelector('input[name="qty_'+b.dataset.plus+'"]');i.value=Math.min(20,+i.value+1)});document.querySelectorAll("[data-minus]").forEach(b=>b.onclick=()=>{let i=document.querySelector('input[name="qty_'+b.dataset.minus+'"]');i.value=Math.max(0,+i.value-1)});document.querySelectorAll(".toast").forEach(x=>setTimeout(()=>x.remove(),3500));document.querySelectorAll('input[name="saved"]').forEach(x=>x.addEventListener("change",()=>{document.querySelector("#address").value=x.dataset.address;document.querySelector("#phone").value=x.dataset.phone||document.querySelector("#phone").value}))});/* =========================================================
   FOODIE — MOBILE SIDEBAR CONTROLLER
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    const sidebar = document.querySelector(".sidebar");

    if (!sidebar) return;


    /* Create hamburger */
    const menuButton = document.createElement("button");

    menuButton.className = "mobile-menu-button";

    menuButton.setAttribute("aria-label", "Open menu");

    menuButton.innerHTML = "☰";

    document.body.appendChild(menuButton);


    /* Create overlay */
    const overlay = document.createElement("div");

    overlay.className = "mobile-sidebar-overlay";

    document.body.appendChild(overlay);


    /* Create close button */
    const closeButton = document.createElement("button");

    closeButton.className = "mobile-sidebar-close";

    closeButton.setAttribute("aria-label", "Close menu");

    closeButton.innerHTML = "×";

    sidebar.prepend(closeButton);


    /* Open */
    function openMenu() {

        document.body.classList.add("mobile-menu-open");

        menuButton.innerHTML = "×";

        document.body.style.overflow = "hidden";
    }


    /* Close */
    function closeMenu() {

        document.body.classList.remove("mobile-menu-open");

        menuButton.innerHTML = "☰";

        document.body.style.overflow = "";
    }


    /* Hamburger */
    menuButton.addEventListener("click", function () {

        if (document.body.classList.contains("mobile-menu-open")) {
            closeMenu();
        } else {
            openMenu();
        }

    });


    /* Close button */
    closeButton.addEventListener("click", closeMenu);


    /* Overlay */
    overlay.addEventListener("click", closeMenu);


    /* Close after clicking navigation link */
    sidebar.querySelectorAll("a").forEach(function (link) {

        link.addEventListener("click", function () {

            closeMenu();

        });

    });


    /* ESC key */
    document.addEventListener("keydown", function (event) {

        if (event.key === "Escape") {

            closeMenu();

        }

    });


    /* Desktop = normal sidebar */
    function checkScreen() {

        if (window.innerWidth > 650) {

            document.body.classList.remove("mobile-menu-open");

            document.body.style.overflow = "";

        }

    }


    window.addEventListener("resize", checkScreen);

});