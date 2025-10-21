// profile.js - pequeños efectos
document.addEventListener('DOMContentLoaded', function(){
  // efecto: simple fadein del card
  const card = document.querySelector('.card.rounded-4');
  if (card) {
    card.style.opacity = 0;
    card.style.transform = "translateY(6px)";
    setTimeout(()=> {
      card.style.transition = "opacity .4s ease, transform .35s ease";
      card.style.opacity = 1;
      card.style.transform = "translateY(0)";
    }, 80);
  }
});
