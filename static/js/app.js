(function(){
  function qs(id){ return document.getElementById(id); }

  function initNotifications(){
    var btn = qs('notifBtn');
    var panel = qs('notifPanel');
    var list = qs('notifList');
    var badge = qs('notifBadge');
    if(!btn || !panel) return;
    function fetchRecent(){
      fetch('/activity/notifications/recent/')
        .then(function(r){ return r.ok ? r.json() : {unread:0,results:[]}; })
        .then(function(d){
          badge.textContent = d.unread ? '(' + d.unread + ')' : '';
          list.innerHTML = '';
          (d.results || []).forEach(function(n){
            var li = document.createElement('li');
            li.textContent = n.message;
            list.appendChild(li);
          });
          if((d.results||[]).length === 0){
            var li = document.createElement('li'); li.textContent = 'No notifications'; list.appendChild(li);
          }
        })
        .catch(function(){});
    }
    btn.addEventListener('click', function(ev){
      try { ev.preventDefault(); ev.stopPropagation(); } catch(e) {}
      var isOpen = panel.classList.contains('open');
      if (isOpen) {
        try { btn.setAttribute('aria-expanded', 'false'); } catch(e) {}
        // Navigate to full notifications page on second click while open
        try { window.location.href = '/activity/notifications/'; } catch(e) {}
        return;
      }
      panel.classList.add('open');
      try { btn.setAttribute('aria-expanded', 'true'); } catch(e) {}
      fetchRecent();
    });
    // Prevent clicks inside panel from bubbling to document and closing it
    panel.addEventListener('click', function(ev){
      try { ev.stopPropagation(); } catch(e) {}
    });
    document.addEventListener('click', function(e){
      // Close if click is outside both the panel and the button (including its children)
      var clickedInsidePanel = panel.contains(e.target);
      var clickedOnButton = btn.contains ? btn.contains(e.target) : (e.target === btn);
      if(!clickedInsidePanel && !clickedOnButton){
        panel.classList.remove('open');
        try { btn.setAttribute('aria-expanded', 'false'); } catch(e) {}
      }
    });
    document.addEventListener('keydown', function(e){
      if(e.key === 'Escape'){
        panel.classList.remove('open');
        try { btn.setAttribute('aria-expanded', 'false'); } catch(err) {}
      }
    });
  }

  function initMaterials(){
    var fi = qs('id_file');
    var ti = qs('id_title');
    if(fi && ti){
      fi.addEventListener('change', function(){
        try {
          if (!ti.value && fi.files && fi.files[0] && fi.files[0].name) {
            var n = fi.files[0].name;
            var base = n.replace(/\.[^.]+$/, '');
            ti.value = base;
          }
        } catch (e) {}
      });
    }
  }

  function initChat(){
    var log = qs('chat-log');
    var form = qs('chat-form');
    var input = qs('chat-input');
    var holder = log && log.closest('[data-chat-course-id]');
    if(!log || !form || !input || !holder) return;
    try{
      // Remove any legacy inline styles to satisfy strict CSP and apply classes instead
      input.classList.add('input','w-80');
      input.removeAttribute('style');
    }catch(e){}
    var courseId = holder.getAttribute('data-chat-course-id');
    function add(msg){
      var d = document.createElement('div');
      d.textContent = msg;
      log.appendChild(d);
      log.scrollTop = log.scrollHeight;
    }
    // History
    fetch('/messaging/course/' + courseId + '/history/')
      .then(function(r){return r.ok ? r.json() : {results:[]};})
      .then(function(data){ (data.results || []).forEach(function(m){ add((m.sender || 'anon') + ': ' + m.message); }); })
      .catch(function(){});
    // WS
    var scheme = (location.protocol === 'https:') ? 'wss' : 'ws';
    var ws = new WebSocket(scheme + '://' + location.host + '/ws/chat/course/' + courseId + '/');
    ws.onmessage = function(ev){
      try{ var data = JSON.parse(ev.data); add((data.sender || 'anon') + ': ' + data.message); }catch(e){}
    };
    form.addEventListener('submit', function(e){
      e.preventDefault();
      var txt = (input.value || '').trim();
      if(!txt) return;
      try { ws.send(JSON.stringify({message: txt})); } catch(e) {}
      input.value='';
    });
  }

  document.addEventListener('DOMContentLoaded', function(){
    initNotifications();
    initMaterials();
    initChat();
  });
})();
