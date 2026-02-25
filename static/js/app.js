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
    btn.addEventListener('click', function(){
      var show = panel.style.display === 'none';
      panel.style.display = show ? 'block' : 'none';
      if(show){ fetchRecent(); }
    });
    document.addEventListener('click', function(e){
      if(!panel.contains(e.target) && e.target !== btn){ panel.style.display='none'; }
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

