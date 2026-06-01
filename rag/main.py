from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import chat, health
import uvicorn
import os
from huggingface_hub import snapshot_download

# ============================================================
# DOWNLOAD PDFs FROM HUGGING FACE (FIRST TIME ONLY)
# ============================================================

def download_pdfs_if_needed():
    """Download ALL PDFs from Hugging Face if not present locally."""
    
    data_folder = "data"
    
    # Create folder if it doesn't exist
    if not os.path.exists(data_folder):
        os.makedirs(data_folder, exist_ok=True)
        print(f"Created {data_folder} folder")
    
    # Check if there are PDF files
    pdf_files = [f for f in os.listdir(data_folder) if f.endswith('.pdf')]
    
    # If no PDFs, download from Hugging Face
    if len(pdf_files) == 0:
        print("=" * 60)
        print("📚 Downloading ALL PDFs from Hugging Face...")
        print("=" * 60)
        
        try:
            # YOUR ACTUAL REPO ID - FIXED!
            repo_id = "oladiiposaheed/betafarm-pdfs"
            
            print(f"Downloading from: {repo_id}")
            print("This may take a few minutes depending on PDF sizes...")
            
            # Download ALL files from the repository
            snapshot_download(
                repo_id=repo_id,
                repo_type="dataset",
                local_dir=data_folder,
                local_dir_use_symlinks=False,
                resume_download=True,
                ignore_patterns=["*.git*", "*.md", ".gitattributes"]
            )
            
            # Count downloaded PDFs
            pdf_count = len([f for f in os.listdir(data_folder) if f.endswith('.pdf')])
            print(f"✅ Successfully downloaded {pdf_count} PDF files!")
            
            # List downloaded PDFs
            if pdf_count > 0:
                print("\n📄 Downloaded PDFs:")
                for pdf in sorted([f for f in os.listdir(data_folder) if f.endswith('.pdf')])[:5]:
                    print(f"   - {pdf}")
                if pdf_count > 5:
                    print(f"   ... and {pdf_count - 5} more")
            
        except Exception as e:
            print(f"⚠️ Failed to download PDFs: {e}")
            print("   You can manually add PDFs to the 'data' folder")
    else:
        print(f"✅ Found {len(pdf_files)} PDF files already in data folder")
        
        # Show what PDFs are available
        if len(pdf_files) > 0:
            print("\n📄 Available PDFs:")
            for pdf in sorted(pdf_files)[:5]:
                print(f"   - {pdf}")
            if len(pdf_files) > 5:
                print(f"   ... and {len(pdf_files) - 5} more")

# Run the download check on startup
download_pdfs_if_needed()

# ============================================================
# CREATE FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title='BetaFarm AI - RAG Service',
    description='Retrieval-Augmented Generation for Nigerian farmers',
    version='1.0.0'
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Register routes
app.include_router(chat.router)
app.include_router(health.router)


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get('/')
async def root():
    """Root endpoint - shows service information with PDF count."""
    
    # Count PDF files in data folder
    data_folder = "data"
    pdf_files = []
    pdf_count = 0
    
    if os.path.exists(data_folder):
        pdf_files = [f for f in os.listdir(data_folder) if f.endswith('.pdf')]
        pdf_count = len(pdf_files)
    
    return {
        "service": "BetaFarm AI - RAG Service",
        "version": "1.0.0",
        "status": "running",
        "pdf_count": pdf_count,
        "pdf_files": pdf_files[:10],
        "endpoints": {
            "chat": "/api/v1/chat (POST)",
            "ask": "/api/v1/ask (GET)",
            "health": "/api/v1/health (GET)",
            "ready": "/api/v1/ready (GET)"
        },
        "docs": "/docs (Swagger UI)"
    }


# ============================================================
# HEALTH CHECK ENDPOINT
# ============================================================

@app.get('/health')
async def health_check():
    """Simple health check for Railway."""
    data_folder = "data"
    pdf_count = 0
    if os.path.exists(data_folder):
        pdf_count = len([f for f in os.listdir(data_folder) if f.endswith('.pdf')])
    
    return {
        "status": "healthy",
        "pdf_count": pdf_count,
        "service": "BetaFarm AI - RAG Service"
    }


# ============================================================
# READY CHECK ENDPOINT (For Kubernetes/Railway)
# ============================================================

@app.get('/ready')
async def ready_check():
    """Ready check for Railway."""
    data_folder = "data"
    pdf_count = 0
    if os.path.exists(data_folder):
        pdf_count = len([f for f in os.listdir(data_folder) if f.endswith('.pdf')])
    
    return {
        "ready": pdf_count > 0,
        "pdf_count": pdf_count
    }


# ============================================================
# RUN THE SERVER
# ============================================================

if __name__ == '__main__':
    # Get port from environment variable (Railway sets this)
    port = int(os.environ.get("PORT", 8002))
    
    print("=" * 60)
    print("🚀 Starting BetaFarm AI - RAG Service")
    print("=" * 60)
    print(f"📡 Server will run on port: {port}")
    print(f"📚 PDF folder: data/")
    print(f"📦 Hugging Face Repo: oladiiposaheed/betafarm-pdfs")
    print("=" * 60)
    
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=port,
        reload=False
    )