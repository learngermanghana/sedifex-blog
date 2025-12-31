(function () {
  document.querySelectorAll('[data-tabs]').forEach((wrap) => {
    const list = wrap.querySelector('.fx-tabs__list');
    const tabs = [...wrap.querySelectorAll('[role="tab"]')];
    const panels = tabs.map(t => document.getElementById(t.getAttribute('aria-controls')));
    const indicator = wrap.querySelector('.fx-tab__indicator');

    function moveIndicator(el){
      if(!indicator) return;
      const left = el.offsetLeft - list.scrollLeft + 6; // compensate for list padding
      indicator.style.transform = `translateX(${left}px)`;
      indicator.style.width = el.offsetWidth + 'px';
    }

    function setActive(idx){
      tabs.forEach((t,i)=>{
        const on = i === idx;
        t.classList.toggle('is-active', on);
        t.setAttribute('aria-selected', on);
        t.tabIndex = on ? 0 : -1;
        panels[i].hidden = !on;
      });
      moveIndicator(tabs[idx]);
    }

    // init
    const start = Math.max(0, tabs.findIndex(t => t.classList.contains('is-active')));
    setActive(start);

    tabs.forEach((t,i)=> t.addEventListener('click', ()=> setActive(i)));

    // keyboard support
    list.addEventListener('keydown', (e)=>{
      const i = tabs.findIndex(t => t.getAttribute('aria-selected') === 'true');
      if(['ArrowRight','ArrowLeft','Home','End'].includes(e.key)){
        e.preventDefault();
        let n = i;
        if(e.key==='ArrowRight') n = (i+1)%tabs.length;
        if(e.key==='ArrowLeft')  n = (i-1+tabs.length)%tabs.length;
        if(e.key==='Home') n = 0;
        if(e.key==='End')  n = tabs.length-1;
        tabs[n].focus(); setActive(n);
      }
    });

    // keep pill aligned
    window.addEventListener('resize', ()=> moveIndicator(wrap.querySelector('.fx-tab.is-active')));
    list.addEventListener('scroll', ()=> moveIndicator(wrap.querySelector('.fx-tab.is-active')));
  });
})();
