document.getElementById('chat-form').addEventListener('submit', function(e) {
    e.preventDefault();
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value;
    const chatBox = document.getElementById('chat-box');
    
    const messageElement = document.createElement('p');
    messageElement.textContent = message;
    chatBox.appendChild(messageElement);
    
    messageInput.value = '';
    chatBox.scrollTop = chatBox.scrollHeight;
});
