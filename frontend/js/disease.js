// Disease Detection JavaScript

const API_BASE_URL = '/api';

// DOM Elements
let video, canvas, imagePreview, startCameraBtn, captureBtn, detectBtn, resetBtn, galleryInput;
let resultsSection, diseaseNameSpan, confidenceBar, confidenceText, healthStatusSpan, solutionDiv, loadingSpinner;

let capturedPhoto = null;
let mediaStream = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Get elements
    video = document.getElementById('cameraPreview');
    canvas = document.getElementById('photoCanvas');
    imagePreview = document.getElementById('imagePreview');
    startCameraBtn = document.getElementById('startCameraBtn');
    captureBtn = document.getElementById('captureBtn');
    detectBtn = document.getElementById('detectBtn');
    resetBtn = document.getElementById('resetBtn');
    galleryInput = document.getElementById('galleryInput');
    resultsSection = document.getElementById('resultSection');
    diseaseNameSpan = document.getElementById('diseaseName');
    confidenceBar = document.getElementById('confidenceBar');
    confidenceText = document.getElementById('confidenceText');
    healthStatusSpan = document.getElementById('healthStatus');
    solutionDiv = document.getElementById('solution');
    loadingSpinner = document.getElementById('spinner');
    
    // Add event listeners
    if (startCameraBtn) startCameraBtn.addEventListener('click', startCamera);
    if (captureBtn) captureBtn.addEventListener('click', capturePhoto);
        if (detectBtn) detectBtn.addEventListener('click', detectDisease);
    if (resetBtn) resetBtn.addEventListener('click', reset);
    if (galleryInput) galleryInput.addEventListener('change', handleGalleryUpload);
});

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.style.position = 'fixed';
    toast.style.bottom = '20px';
    toast.style.left = '50%';
    toast.style.transform = 'translateX(-50%)';
    toast.style.backgroundColor = type === 'success' ? '#075e54' : type === 'error' ? '#dc3545' : '#ff9800';
    toast.style.color = 'white';
    toast.style.padding = '12px 24px';
    toast.style.borderRadius = '30px';
    toast.style.fontSize = '14px';
    toast.style.zIndex = '1000';
    toast.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    toast.innerHTML = (type === 'success' ? '✅ ' : type === 'error' ? '❌ ' : 'ℹ️ ') + message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

async function startCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: { exact: "environment" } }
        });
        
        mediaStream = stream;
        video.srcObject = stream;
        video.style.display = 'block';
        imagePreview.style.display = 'none';
        
        startCameraBtn.style.display = 'none';
        captureBtn.style.display = 'block';
        detectBtn.style.display = 'none';
        resetBtn.style.display = 'none';
        if (resultsSection) resultsSection.style.display = 'none';
        
        showToast('Camera started. Position the leaf and tap Capture', 'success');
    } catch (error) {
        console.error('Camera error:', error);
        showToast('Could not start camera. Please use Upload Photo option.', 'error');
    }
}

function capturePhoto() {
    if (!video || !canvas) return;
    
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
    detectBtn.style.display = 'block';
    resetBtn.style.display = 'block';
    if (resultsSection) resultsSection.style.display = 'none';
    
    showToast('Photo captured! Click Detect Disease', 'success');
}

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
        
        if (video && video.style.display === 'block') {
            video.style.display = 'none';
            if (mediaStream) {
                mediaStream.getTracks().forEach(track => track.stop());
                mediaStream = null;
            }
        }
        
        startCameraBtn.style.display = 'block';
        captureBtn.style.display = 'none';
        detectBtn.style.display = 'block';
        resetBtn.style.display = 'block';
        if (resultsSection) resultsSection.style.display = 'none';
        
        showToast('Image loaded! Click Detect Disease', 'success');
    };
    reader.readAsDataURL(file);
}

function reset() {
    if (resultsSection) resultsSection.style.display = 'none';
    if (imagePreview) {
        imagePreview.style.display = 'none';
        imagePreview.src = '';
    }
    capturedPhoto = null;
    
    if (detectBtn) detectBtn.style.display = 'none';
    if (resetBtn) resetBtn.style.display = 'none';
    if (startCameraBtn) startCameraBtn.style.display = 'block';
    if (captureBtn) captureBtn.style.display = 'none';
    
    if (galleryInput) galleryInput.value = '';
    
    if (mediaStream && video) {
        video.style.display = 'block';
    } else if (video) {
        video.style.display = 'none';
    }
    
    showToast('Reset complete. Take a new photo or upload.', 'info');
}

async function detectDisease() {
    if (!capturedPhoto) {
        showToast('Please take or upload a photo first', 'warning');
        return;
    }
    
    if (loadingSpinner) loadingSpinner.style.display = 'block';
    if (resultsSection) resultsSection.style.display = 'none';
    
    const formData = new FormData();
    formData.append('image', capturedPhoto);
    
    const token = localStorage.getItem('access_token');
    
    if (!token) {
        showToast('Please login again', 'error');
        window.location.href = '/';
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/predict/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            if (diseaseNameSpan) diseaseNameSpan.textContent = result.disease_name || 'Unknown';
            const confidencePercent = (result.confidence || 0);
            if (confidenceBar) confidenceBar.style.width = `${confidencePercent}%`;
            if (confidenceText) confidenceText.textContent = `${confidencePercent}%`;
            if (healthStatusSpan) healthStatusSpan.textContent = result.health_status || 'Unknown';
            
            // Display full treatment text
            if (solutionDiv) {
                solutionDiv.textContent = result.solution || 'No treatment information available.';
                solutionDiv.style.whiteSpace = 'normal';
                solutionDiv.style.wordWrap = 'break-word';
                solutionDiv.style.maxHeight = '250px';
                solutionDiv.style.overflowY = 'auto';
            }
            
            if (resultsSection) resultsSection.style.display = 'block';
            showToast('Detection complete!', 'success');
        } else {
            showToast(result.error || result.detail || 'Detection failed', 'error');
        }
    } catch (error) {
        console.error('Detection error:', error);
        showToast('Network error. Please try again.', 'error');
    } finally {
        if (loadingSpinner) loadingSpinner.style.display = 'none';
    }
}

// Check authentication
if (!localStorage.getItem('access_token')) {
    window.location.href = '/';
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
        window.location.href = '/';
    });
}