var events_elm = document.querySelector('#events')
var status_elm = document.querySelector('#status')
var users_elm = document.querySelector('#users')
var username_elm = document.querySelector('#username')
var form_elm = document.querySelector('form')
var message_elm = document.querySelector('input#message')

function set_username () {
  localStorage.username = prompt('Enter username:', localStorage.username || '')
}

while (!localStorage.username) {
  set_username()
}
username_elm.innerHTML = localStorage.username
var restart

function clear() {
  while(events_elm.firstChild) {
    events_elm.removeChild(events_elm.firstChild)
  }
  users_elm.innerHTML = '-'
}


function Client () {
  clear()
  var conn = new WebSocket(document.body.getAttribute('data-ws-url'))
  var close_intended = false

  function add_message(message) {
    var new_el = document.createElement('p')
    new_el.innerHTML = `
<span> ${message.username || 'unknown'}: ${message.message || ''}</span> 
<span class="right"><label>${message.ts}</label>
</span>`
    events_elm.appendChild(new_el)
  }

  function set_user_count(users) {
    users_elm.innerHTML = users.join(', ') + ` (count: ${users.length})`
  }

  conn.onmessage = function(evt){
    var event = JSON.parse(evt.data)
    if (event.users !== undefined) {
      set_user_count(event.users)
    } else {
      add_message(event)
    }
  }

  function send(event_data){
    conn.send(JSON.stringify(event_data))
  }

  this.send = send
  conn.onclose = function () {
    status_elm.innerHTML = 'Disconnected'
    clear()
    if (!close_intended){
      clearInterval(restart)
      restart = setInterval(start, 2000)
    }
  }

  this.close = function (intended) {
    close_intended = Boolean(intended)
    conn.close()
  }

  conn.onopen = function () {
    clearInterval(restart)
    status_elm.innerHTML = 'Connected'
    // setTimeout(this.connected, 100)
    send({action: 'connected', username: localStorage.username})
  }
}
var client

function start() {
  client = new Client()
}
start()

form_elm.addEventListener('submit', function (evt) {
  evt.preventDefault()
  client.send({action: 'message', message: message_elm.value})
  message_elm.value = ''
})

document.querySelector('#connect').addEventListener('click', function (evt) {
  start()
})

document.querySelector('#disconnect').addEventListener('click', function (evt) {
  client.close(true)
})
