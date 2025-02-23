// Global variables for voice recording
let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let visualizerInterval;

// Global state management
let isAuthenticated = false;
let selectedImage = null;

// Authentication Functions
async function handleLogin() {
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);

    try {
        const response = await fetch('/login', {
            method: 'POST',
            body: formData,
        });

        if (response.ok) {
            const data = await response.json();
            await handleLoginSuccess(data);
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Login failed');
        }
    } catch (error) {
        showStatus('Login failed: ' + error.message, false);
    }
}

// Voice Assistant Functions
async function toggleRecording() {
    const recordButton = document.getElementById('recordButton');
    
    if (!isRecording) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            
            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };
            
            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                await processAudio(audioBlob);
            };
            
            mediaRecorder.start();
            isRecording = true;
            recordButton.classList.add('recording');
            recordButton.querySelector('span').textContent = 'Stop';
            startVisualizer();
            
        } catch (error) {
            showStatus('Microphone access denied', false);
        }
    } else {
        mediaRecorder.stop();
        isRecording = false;
        recordButton.classList.remove('recording');
        recordButton.querySelector('span').textContent = 'Start';
        stopVisualizer();
    }
}

async function processAudio(audioBlob) {
    try {
        const formData = new FormData();
        formData.append('audio', audioBlob);
        
        const response = await authenticatedFetch('/voice/process', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error('Failed to process audio');
        
        const data = await response.json();
        addChatMessage('user', 'Audio message sent');
        
        // Handle the AI response
        if (data.audio_response) {
            const audio = new Audio(data.audio_response);
            await audio.play();
        }
        
        addChatMessage('assistant', data.text_response);
        
    } catch (error) {
        showStatus('Failed to process audio: ' + error.message, false);
    }
}

function startVisualizer() {
    const visualizer = document.getElementById('audioVisualizer');
    visualizer.innerHTML = '';
    
    for (let i = 0; i < 20; i++) {
        const bar = document.createElement('div');
        bar.className = 'visualizer-bar';
        visualizer.appendChild(bar);
    }
    
    visualizerInterval = setInterval(() => {
        const bars = visualizer.getElementsByClassName('visualizer-bar');
        for (let bar of bars) {
            const height = Math.random() * 50;
            bar.style.height = `${height}px`;
        }
    }, 100);
}

function stopVisualizer() {
    clearInterval(visualizerInterval);
    const visualizer = document.getElementById('audioVisualizer');
    visualizer.innerHTML = '';
}

// Social Media Platform Authentication
async function authenticateFacebook() {
    try {
        const response = await authenticatedFetch('/auth/facebook');
        if (!response.ok) throw new Error('Failed to get auth URL');
        
        const data = await response.json();
        window.open(data.auth_url, 'FacebookAuth', 'width=600,height=700');
        
    } catch (error) {
        showStatus('Facebook authentication failed: ' + error.message, false);
    }
}

async function authenticateInstagram() {
    try {
        const response = await authenticatedFetch('/auth/instagram');
        if (!response.ok) throw new Error('Failed to get auth URL');
        
        const data = await response.json();
        window.open(data.auth_url, 'InstagramAuth', 'width=600,height=700');
        
    } catch (error) {
        showStatus('Instagram authentication failed: ' + error.message, false);
    }
}

// Utility Functions
async function authenticatedFetch(url, options = {}) {
    const token = localStorage.getItem('access_token');
    if (!token) throw new Error('No authentication token found');
    
    return fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            'Authorization': `Bearer ${token}`
        }
    });
}

function showStatus(message, isSuccess) {
    const toast = document.getElementById('statusToast');
    if (toast) {
        toast.textContent = message;
        toast.className = `status-toast ${isSuccess ? 'success' : 'error'}`;
        toast.style.display = 'block';
        setTimeout(() => {
            toast.style.display = 'none';
        }, 3000);
    }
}

function addChatMessage(sender, message) {
    const chatContainer = document.getElementById('chatContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}`;
    messageDiv.innerHTML = `
        <div class="message-content">
            <i class="fas fa-${sender === 'user' ? 'user' : 'robot'}"></i>
            <p>${message}</p>
        </div>
    `;
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Navigation
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded'); // Debug log
    
    // Check authentication status
    const token = localStorage.getItem('access_token');
    if (token) {
        isAuthenticated = true;
        showMainContent();
        checkPlatformStatus();
    }

    // Add click handler for create post button
    const createPostBtn = document.getElementById('createPostBtn');
    if (createPostBtn) {
        console.log('Create Post button found'); // Debug log
        createPostBtn.addEventListener('click', () => {
            console.log('Create Post button clicked'); // Debug log
            showCreatePostModal();
        });
    } else {
        console.log('Create Post button not found'); // Debug log
    }

    // Add navigation listeners
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = e.target.closest('.nav-link').dataset.page;
            showPage(page);
        });
    });

    // loadScheduledPosts();

    // Add event listener for logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }

    // Check authentication status and update UI
    updateUIForAuthState(!!token);
});

function showPage(pageId) {
    const pages = document.querySelectorAll('.page');
    const links = document.querySelectorAll('.nav-link');
    
    pages.forEach(page => page.classList.remove('active'));
    links.forEach(link => link.classList.remove('active'));
    
    const targetPage = document.getElementById(`${pageId}Page`);
    const targetLink = document.querySelector(`[data-page="${pageId}"]`);
    
    if (targetPage) targetPage.classList.add('active');
    if (targetLink) targetLink.classList.add('active');
}

function showMainContent() {
    const authForms = document.getElementById('authForms');
    const mainContent = document.getElementById('mainContent');
    
    if (authForms && mainContent) {
        authForms.classList.add('hidden');
        mainContent.classList.remove('hidden');
    }
}

// Modal Functions
function showCreatePostModal() {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3><i class="fas fa-pencil-alt"></i> Create Post</h3>
                <button class="btn-close" onclick="closeModal()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            
            <textarea id="postContent" placeholder="What's on your mind?"></textarea>
            
            <div class="image-search-container">
                <div class="image-search-header">
                    <h4>Add Image</h4>
                    <div class="search-input-group">
                        <input type="text" id="imageSearchInput" placeholder="Search for images...">
                        <button class="btn-primary" onclick="searchImages()">
                            <i class="fas fa-search"></i> Search
                        </button>
                    </div>
                </div>
                <div id="imageSearchResults" class="image-search-results"></div>
            </div>
            
            <div class="modal-footer">
                <button class="btn-secondary" onclick="closeModal()">Cancel</button>
                <button class="btn-primary" onclick="createPost()">
                    <i class="fas fa-paper-plane"></i> Post
                </button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    
    // Reset selected image
    selectedImage = null;
    
    // Add event listener for the image search input
    const searchInput = document.getElementById('imageSearchInput');
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            searchImages();
        }
    });
}

function closeModal() {
    const modal = document.querySelector('.modal');
    if (modal) {
        modal.remove();
    }
}

// Image Upload Handler
function handleImageUpload(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById('imagePreview');
            if (preview) {
                preview.style.display = 'block';
                preview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
            }
        };
        reader.readAsDataURL(file);
    }
}

// Post Creation
async function searchImages() {
    const query = document.getElementById('imageSearchInput').value;
    if (!query) return;

    const token = localStorage.getItem('access_token'); // Ensure this matches the token name used during login
    console.log("Token for image search:", token); // Debug log

    try {
        const response = await fetch(`/social_post/search_images?query=${encodeURIComponent(query)}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.status === 401) {
            showToast('Please log in again to continue', 'error');
            return;
        }

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        const resultsContainer = document.getElementById('imageSearchResults');
        resultsContainer.innerHTML = '';
        
        if (!Array.isArray(data) || data.length === 0) {
            resultsContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-image"></i>
                    <p>No images found for "${query}"</p>
                </div>
            `;
            return;
        }

        data.forEach(image => {
            const imageElement = document.createElement('div');
            imageElement.className = 'image-result';
            imageElement.innerHTML = `
                <img src="${image.thumb}" alt="${image.description || 'Image thumbnail'}">
                <div class="photographer-credit">Photo by ${image.photographer}</div>
            `;
            
            imageElement.onclick = () => {
                document.querySelectorAll('.image-result').forEach(el => 
                    el.classList.remove('selected'));
                imageElement.classList.add('selected');
                selectedImage = {
                    id: image.id,
                    url: image.url
                };
            };
            
            resultsContainer.appendChild(imageElement);
        });
    } catch (error) {
        console.error('Error searching images:', error);
        showToast('Error searching for images', 'error');
    }
}

async function createPost() {
    const content = document.getElementById('postContent').value;
    if (!content) {
        showToast('Please enter some content for your post', 'error');
        return;
    }

    try {
        const token = localStorage.getItem('access_token');
        
        if (!token) {
            showToast('Please log in to create posts', 'error');
            return;
        }

        const postData = {
            content: content,
            unsplash_image_id: selectedImage?.id,
            image_url: selectedImage?.url
        };

        const response = await fetch('/social_post/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(postData)
        });

        const result = await response.json();

        if (result.success) {
            // Show success message with optimization details
            let message = `Post created successfully!`;
            
            if (result.optimized_content) {
                message += `
                    <div class="optimization-details">
                        <p><strong>SEO Optimized:</strong> Content has been enhanced for better reach</p>
                        <p><strong>Hashtags:</strong> ${result.optimized_content.hashtags.join(' ')}</p>
                    </div>
                `;
            }
            
            if (result.post_url) {
                message += `<a href="${result.post_url}" target="_blank" class="toast-link">View Post</a>`;
            }
            
            showToast(message, 'success', true);
            closeModal();
            // await loadScheduledPosts();
        } else {
            showToast(result.fb_status || 'Error creating post', 'error');
        }
    } catch (error) {
        console.error('Error creating post:', error);
        showToast('Error creating post', 'error');
    }
}

// Updated showToast function to support HTML content
function showToast(message, type = 'success', isHTML = false) {
    const toast = document.getElementById('statusToast');
    if (toast) {
        // Clear any existing timeout
        if (toast.timeoutId) {
            clearTimeout(toast.timeoutId);
        }
        
        // Add close button if it's a success message with a link
        const hasLink = message.includes('View Post');
        const closeButton = hasLink ? '<button class="toast-close"><i class="fas fa-times"></i></button>' : '';
        
        if (isHTML) {
            toast.innerHTML = `
                <div class="toast-content">
                    ${message}
                </div>
                ${closeButton}
            `;
        } else {
            toast.textContent = message;
        }
        
        toast.className = `status-toast ${type}`;
        toast.style.display = 'block';
        
        // Add click handler for close button if it exists
        const closeBtn = toast.querySelector('.toast-close');
        if (closeBtn) {
            closeBtn.onclick = () => {
                toast.style.display = 'none';
            };
        }
        
        // Set timeout only for non-link messages or error messages
        if (!hasLink || type === 'error') {
            toast.timeoutId = setTimeout(() => {
                toast.style.display = 'none';
            }, 3000);
        }
    }
}

// Platform Status Check
async function checkPlatformStatus() {
    try {
        const fbStatus = document.getElementById('fbStatus');
        const igStatus = document.getElementById('igStatus');
        
        if (fbStatus) fbStatus.textContent = 'Not Connected';
        if (igStatus) igStatus.textContent = 'Not Connected';
        
        // You can implement actual platform status check here
    } catch (error) {
        console.error('Error checking platform status:', error);
    }
}

// async function loadScheduledPosts() {
//     try {
//         const token = localStorage.getItem('access_token');
//         console.log("Token for scheduled posts:", token); // Debug log
        
//         if (!token) {
//             console.log('No authentication token found');
//             return;
//         }

//         const response = await fetch('/social_post/scheduled', {
//             headers: {
//                 'Authorization': `Bearer ${token}`
//             }
//         });
        
//         if (response.status === 401) {
//             showToast('Please log in to view scheduled posts', 'error');
//             return;
//         }

//         if (!response.ok) {
//             throw new Error(`HTTP error! status: ${response.status}`);
//         }
        
//         const data = await response.json();
//         const posts = data.posts || [];
//         const postsContainer = document.getElementById('scheduledPostsList');
        
//         if (!postsContainer) {
//             console.log('Posts container not found');
//             return;
//         }
        
//         postsContainer.innerHTML = '';
        
//         if (posts.length === 0) {
//             postsContainer.innerHTML = `
//                 <div class="empty-state">
//                     <i class="fas fa-calendar-times"></i>
//                     <p>No scheduled posts yet</p>
//                 </div>
//             `;
//             return;
//         }

//         posts.forEach(post => {
//             const postElement = document.createElement('div');
//             postElement.className = 'scheduled-post';
//             postElement.innerHTML = `
//                 <div class="post-content">
//                     <div class="post-text">${post.content}</div>
//                     ${post.image_url ? `
//                         <div class="post-image">
//                             <img src="${post.image_url}" alt="Post image">
//                         </div>
//                     ` : ''}
//                     ${post.post_url ? `
//                         <div class="post-link">
//                             <a href="${post.post_url}" target="_blank" class="btn-view-post">
//                                 <i class="fas fa-external-link-alt"></i> View Post
//                             </a>
//                         </div>
//                     ` : ''}
//                 </div>
//                 <div class="post-meta">
//                     <div class="post-platforms">
//                         ${post.facebook_status ? '<i class="fab fa-facebook"></i>' : ''}
//                     </div>
//                     <div class="post-time">
//                         <i class="fas fa-clock"></i>
//                         ${new Date(post.scheduled_time).toLocaleString()}
//                     </div>
//                 </div>
//             `;
//             postsContainer.appendChild(postElement);
//         });
//     } catch (error) {
//         console.error('Error loading scheduled posts:', error);
//         showToast('Error loading scheduled posts', 'error');
//     }
// }


// Update the logout function to prevent page reload
async function logout() {
    try {
        console.log("Logout initiated"); // Debug log
        
        // Clear authentication
        localStorage.removeItem('access_token'); // Ensure this matches the token name used during login
        isAuthenticated = false;

        // Clear any existing posts
        const postsContainer = document.getElementById('scheduledPostsList');
        if (postsContainer) {
            postsContainer.innerHTML = '';
        }

        // Show login form
        showLoginForm();

        // Hide authenticated elements
        document.querySelectorAll('.authenticated-only').forEach(el => {
            el.style.display = 'none';
        });

        // Show login elements
        document.querySelectorAll('.login-only').forEach(el => {
            el.style.display = 'block';
        });

        showStatus('Logged out successfully', 'success');
        
        console.log("Logout completed"); // Debug log
    } catch (error) {
        console.error('Error during logout:', error);
        showStatus('Error during logout', 'error');
    }
}

// Update the UI based on authentication state
function updateUIForAuthState(isAuthenticated) {
    const authenticatedElements = document.querySelectorAll('.authenticated-only');
    const loginElements = document.querySelectorAll('.login-only');
    const mainContent = document.getElementById('mainContent');
    const authForms = document.getElementById('authForms');
    const logoutBtn = document.getElementById('logoutBtn');

    if (isAuthenticated) {
        // Show authenticated elements
        authenticatedElements.forEach(el => el.style.display = 'block');
        loginElements.forEach(el => el.style.display = 'none');
        if (mainContent) mainContent.style.display = 'block';
        if (authForms) authForms.style.display = 'none';
        if (logoutBtn) logoutBtn.style.display = 'block';
    } else {
        // Show login elements
        authenticatedElements.forEach(el => el.style.display = 'none');
        loginElements.forEach(el => el.style.display = 'block');
        if (mainContent) mainContent.style.display = 'none';
        if (authForms) authForms.style.display = 'block';
        if (logoutBtn) logoutBtn.style.display = 'none';
    }
}

// Update login success handler
async function handleLoginSuccess(data) {
    if (data.access_token) {
        localStorage.setItem('access_token', data.access_token);
        isAuthenticated = true;
        showToast('Login successful!', 'success');
        updateUIForAuthState(true);
        showMainContent()
        // await loadScheduledPosts();
    }
}

// Add CSS class helpers
function addClass(element, className) {
    if (element && !element.classList.contains(className)) {
        element.classList.add(className);
    }
}

function removeClass(element, className) {
    if (element && element.classList.contains(className)) {
        element.classList.remove(className);
    }
}

// Initialize everything when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM Content Loaded"); // Debug log
    
    // Add logout button listener
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    }

    // Check initial auth state
    const token = localStorage.getItem('token');
    if (token) {
        isAuthenticated = true;
        document.querySelectorAll('.authenticated-only').forEach(el => {
            el.style.display = 'block';
        });
        document.querySelectorAll('.login-only').forEach(el => {
            el.style.display = 'none';
        });
    } else {
        showLoginForm();
    }
});

function showLoginForm() {
    console.log("Showing login form"); // Debug log
    const authForms = document.getElementById('authForms');
    const mainContent = document.getElementById('mainContent');
    
    if (authForms) {
        console.log("Auth forms found"); // Debug log
        authForms.style.display = 'block';
        authForms.classList.remove('hidden');
    } else {
        console.error("Auth forms not found"); // Debug log
    }
    
    if (mainContent) {
        mainContent.style.display = 'none';
        mainContent.classList.add('hidden');
    }
}

async function handleLogout() {
    try {
        console.log("Logout initiated"); // Debug log
        
        // Clear authentication
        localStorage.removeItem('access_token'); // Ensure this matches the token name used during login
        isAuthenticated = false;

        // Clear any existing posts
        const postsContainer = document.getElementById('scheduledPostsList');
        if (postsContainer) {
            postsContainer.innerHTML = '';
        }

        // Show login form
        showLoginForm();

        // Hide authenticated elements
        document.querySelectorAll('.authenticated-only').forEach(el => {
            el.style.display = 'none';
        });

        // Show login elements
        document.querySelectorAll('.login-only').forEach(el => {
            el.style.display = 'block';
        });

        showStatus('Logged out successfully', 'success');
        
        console.log("Logout completed"); // Debug log
    } catch (error) {
        console.error('Error during logout:', error);
        showStatus('Error during logout', 'error');
    }
}

function toggleAuthForm(form) {
    const loginSection = document.getElementById('loginSection');
    const signupSection = document.getElementById('signupSection');

    if (form === 'signup') {
        loginSection.classList.remove('active');
        signupSection.classList.add('active');
    } else {
        signupSection.classList.remove('active');
        loginSection.classList.add('active');
    }
}

async function handleSignup() {
    const name = document.getElementById('signupName').value; // Assuming you have an input with this ID
    const email = document.getElementById('signupEmail').value; // Assuming you have an input with this ID
    const password = document.getElementById('signupPassword').value; // Assuming you have an input with this ID

    // Basic validation
    if (!name || !email || !password) {
        showToast('Please fill in all fields', 'error');
        return;
    }

    try {
        const response = await fetch('/users/', { // Change this line to match the correct endpoint
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, email, password }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            showToast(errorData.detail || 'Signup failed', 'error');
            return;
        }

        const data = await response.json();
        showToast('Signup successful! Please log in.', 'success');
        // Optionally, redirect to login or perform other actions
    } catch (error) {
        console.error('Error during signup:', error);
        showToast('An error occurred during signup', 'error');
    }
}