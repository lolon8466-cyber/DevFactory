const burger = document.getElementById("burger");
const menu = document.getElementById("menu");
const dropdownBtn = document.querySelector(".dropdown-btn");
const dropdown = document.querySelector(".dropdown");

burger.addEventListener("click", ()=>{menu.classList.toggle("active");});
dropdownBtn.addEventListener("click", ()=>{dropdown.classList.toggle("active");});