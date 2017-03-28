var FancyWebSocket = function(url){
  // https://gist.github.com/ismasan/299789
  var conn = new WebSocket(url)

  var callbacks = {}

  this.bind = function(event_name, callback){
    callbacks[event_name] = callbacks[event_name] || []
    callbacks[event_name].push(callback)
  }

  this.send = function(event_data){
    conn.send(JSON.stringify(event_data))
  }

  conn.onmessage = function(evt){
    dispatch('message', JSON.parse(evt.data))
  }

  conn.onclose = function(){dispatch('close',null)}
  conn.onopen = function(){dispatch('open',null)}

  var dispatch = function(event_name, message){
    var chain = callbacks[event_name]
    if(typeof chain === 'undefined') return
    for(var i = 0; i < chain.length; i++){
      chain[i](message)
    }
  }
}

var events_elm = document.querySelector('#events')
var status_elm = document.querySelector('#status')
var form_elm = document.querySelector('form')
var message_elm = document.querySelector('input#message')
var username_elm = document.querySelector('input#username')
var socket = new FancyWebSocket(document.body.getAttribute('data-ws-url'))

if (localStorage.username) {
  username_elm.value = localStorage.username
}

socket.bind('open', function (msg) {
  status_elm.innerHTML = 'Active'
  socket.send({action: 'connected', username: username_elm.value})
})

socket.bind('close', function () {
  status_elm.innerHTML = 'Closed.'
})

socket.bind('message', function (event) {
  var new_el = document.createElement('p')
  new_el.innerHTML = `
<span>${event.action}: ${event.message || ''}</span> 
<span class="right">
${event.username || ''}
<label>${event.ts}</label>
</span>`
  events_elm.appendChild(new_el)
})

form_elm.addEventListener('submit', function(evt){
  evt.preventDefault()
  localStorage.username = username_elm.value
  socket.send({action: 'message', username: username_elm.value, message: message_elm.value})
  message_elm.value = ''
})

