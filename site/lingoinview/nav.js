"use strict";
const picker=document.querySelector("[data-promo-root]");
if(picker)picker.addEventListener("change",()=>{const lang=picker.value;const allowed=["en","ru","uk","de","es","fr","pt-BR","zh-CN"];if(allowed.includes(lang))location.href=picker.dataset.promoRoot+(lang==="en"?"":lang+"/");});
