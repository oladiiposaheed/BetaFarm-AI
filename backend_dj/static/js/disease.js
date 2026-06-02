/**
 * DISEASE DETECTION - Complete Working Version
 */

// ============================================================
// DOM ELEMENTS
// ============================================================

const video = document.getElementById('cameraPreview');
const canvas = document.getElementById('photoCanvas');
const imagePreview = document.getElementById('imagePreview');
const startCameraBtn = document.getElementById('startCameraBtn');
const captureBtn = document.getElementById('captureBtn');
const detectBtn = document.getElementById('detectBtn');
const resetBtn = document.getElementById('resetBtn');
const galleryInput = document.getElementById('galleryInput');

// Results elements
const diseaseName = document.getElementById('diseaseName');
const confidenceBar = document.getElementById('confidenceBar');
const confidenceText = document.getElementById('confidencText'); // Keep as is or change to confidenceText
const healthStatus = document.getElementById('healthStatus');
const solution = document.getElementById('solution');
const resultsSection = document.getElementById('resultsSection');
const loadingSpinner = document.getElementById('loadingSpinner');

// Variables
let capturedPhoto = null;
let mediaStream = null;

// ============================================================
// FUNCTION 1: START CAMERA
// ============================================================

async function startCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: { exact: "environment" } }
        });
        
        mediaStream = stream;
        video.srcObject = stream;
        video.style.display = 'block';
        
        startCameraBtn.style.display = 'none';
        captureBtn.style.display = 'inline-block';
        
        showToast('Camera started. Position the leaf and tap Capture', 'success');
    } catch (error) {
        console.error('Camera error:', error);
        showToast('Could not start camera. Please use Upload Photo option.', 'error');
    }
}

// ============================================================
// FUNCTION 2: CAPTURE PHOTO
// ============================================================

function capturePhoto() {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    const imageUrl = canvas.toDataURL('image/jpeg', 0.9);
    imagePreview.src = imageUrl;
    imagePreview.style.display = 'block';
    video.style.display = 'none';
    
    // Stop camera
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        mediaStream = null;
    }
    
    // Convert to file
    fetch(imageUrl)
        .then(res => res.blob())
        .then(blob => {
            capturedPhoto = new File([blob], 'leaf-photo.jpg', { type: 'image/jpeg' });
        });
    
    captureBtn.style.display = 'none';
    detectBtn.style.display = 'inline-block';
    resetBtn.style.display = 'inline-block';
    
    showToast('Photo captured! Click Detect Disease', 'success');
}

// ============================================================
// FUNCTION 3: GALLERY UPLOAD
// ============================================================

function handleGalleryUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    if (!file.type.startsWith('image/')) {
        showToast('Please select an image file', 'error');
        return;
    }
    
    capturedPhoto = file;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        imagePreview.src = e.target.result;
        imagePreview.style.display = 'block';
        
        if (video.style.display === 'block') {
            video.style.display = 'none';
            if (mediaStream) {
                mediaStream.getTracks().forEach(track => track.stop());
                mediaStream = null;
            }
        }
        
        startCameraBtn.style.display = 'inline-block';
        captureBtn.style.display = 'none';
        detectBtn.style.display = 'inline-block';
        resetBtn.style.display = 'inline-block';
        
        showToast('Image loaded! Click Detect Disease', 'success');
    };
    reader.readAsDataURL(file);
}

// ============================================================
// FUNCTION 4: RESET
// ============================================================

function reset() {
    resultsSection.style.display = 'none';
    imagePreview.style.display = 'none';
    imagePreview.src = '';
    capturedPhoto = null;
    
    detectBtn.style.display = 'none';
    resetBtn.style.display = 'none';
    startCameraBtn.style.display = 'inline-block';
    captureBtn.style.display = 'none';
    
    if (galleryInput) galleryInput.value = '';
    
    if (mediaStream) {
        video.style.display = 'block';
    } else {
        video.style.display = 'none';
    }
}

// ============================================================
// FUNCTION 5: DETECT DISEASE
// ============================================================

async function detectDisease() {
    if (!capturedPhoto) {
        showToast('Please take or upload a photo first', 'warning');
        return;
    }
    
    loadingSpinner.style.display = 'block';
    resultsSection.style.display = 'none';
    
    const formData = new FormData();
    formData.append('image', capturedPhoto);
    
    const token = localStorage.getItem('access_token');
    
    if (!token) {
        showToast('Please login again', 'error');
        window.location.href = 'index.html';
        return;
    }
    
    try {
        const response = await fetch('http://localhost:8000/api/predict/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Display results
            diseaseName.textContent = result.disease_name || 'Unknown';
            const confidencePercent = (result.confidence || 0) * 100;
            confidenceBar.style.width = `${confidencePercent}%`;
            confidenceText.textContent = `${confidencePercent.toFixed(1)}%`;
            healthStatus.textContent = result.health_status || 'Unknown';
            solution.textContent = result.solution || 'No treatment information available.';
            
            resultsSection.style.display = 'block';
            showToast('Detection complete!', 'success');
        } else {
            showToast(result.error || 'Detection failed', 'error');
        }
    } catch (error) {
        console.error('Detection error:', error);
        showToast('Network error. Please try again.', 'error');
    } finally {
        loadingSpinner.style.display = 'none';
    }
}

// ============================================================
// HELPER: Show Toast
// ============================================================

function showToast(message, type = 'info') {
    const toastEl = document.getElementById('liveToast');
    const toastBody = document.getElementById('toastMessage');
    if (!toastEl || !toastBody) return;
    
    let icon = '<i class="fas fa-info-circle me-2"></i>';
    if (type === 'success') icon = '<i class="fas fa-check-circle text-success me-2"></i>';
    if (type === 'error') icon = '<i class="fas fa-exclamation-circle text-danger me-2"></i>';
    
    toastBody.innerHTML = icon + message;
    const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
    toast.show();
}

// ============================================================
// EVENT LISTENERS
// ============================================================

if (startCameraBtn) startCameraBtn.addEventListener('click', startCamera);
if (captureBtn) captureBtn.addEventListener('click', capturePhoto);
if (detectBtn) detectBtn.addEventListener('click', detectDisease);
if (resetBtn) resetBtn.addEventListener('click', reset);
if (galleryInput) galleryInput.addEventListener('change', handleGalleryUpload);

// ============================================================
// CHECK LOGIN
// ============================================================

if (!localStorage.getItem('access_token')) {
    window.location.href = 'index.html';
}

// Set user name
const userNameSpan = document.getElementById('userName');
if (userNameSpan) {
    userNameSpan.textContent = localStorage.getItem('userName') || 'Farmer';
}

// Logout button
const logoutBtn = document.getElementById('logoutBtn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
        localStorage.clear();
        window.location.href = 'index.html';
    });
}