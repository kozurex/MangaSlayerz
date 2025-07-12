from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import requests
import json
import uuid
from datetime import datetime
import aiofiles
import aiohttp
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
import asyncio
import hashlib
from urllib.parse import urljoin, urlparse
import re

# MongoDB setup
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(MONGO_URL)
db = client.manga_slayer

app = FastAPI(title="Manga Slayer API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create downloads directory
DOWNLOADS_DIR = "/app/downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# Pydantic models
class MangaSource(BaseModel):
    id: str
    name: str
    url: str
    type: str = "custom"  # built-in or custom
    enabled: bool = True
    added_date: datetime = None

class MangaInfo(BaseModel):
    id: str
    title: str
    title_ar: str = ""
    description: str = ""
    description_ar: str = ""
    cover_image: str = ""
    source: str
    chapters: List[Dict] = []
    total_size: int = 0  # in bytes
    download_status: str = "not_downloaded"  # not_downloaded, downloading, completed

class ChapterInfo(BaseModel):
    id: str
    manga_id: str
    chapter_number: float
    title: str
    title_ar: str = ""
    pages: List[str] = []
    size: int = 0  # in bytes
    download_status: str = "not_downloaded"
    download_path: str = ""

class DownloadStats(BaseModel):
    total_manga: int
    total_chapters: int
    total_size: int
    available_space: int

class AutoScrollSettings(BaseModel):
    speed: int = 3  # 1-10 scale
    enabled: bool = False
    pause_on_tap: bool = True

class UserPreferences(BaseModel):
    auto_scroll: AutoScrollSettings = AutoScrollSettings()
    language: str = "ar"
    reading_direction: str = "rtl"
    auto_translate: bool = True

# Built-in manga sources
BUILT_IN_SOURCES = [
    {
        "id": "mangadex",
        "name": "MangaDex",
        "url": "https://api.mangadex.org",
        "type": "built-in"
    },
    {
        "id": "mangakakalot",
        "name": "MangaKakalot",
        "url": "https://mangakakalot.com",
        "type": "built-in"
    },
    {
        "id": "manganato",
        "name": "Manganato", 
        "url": "https://manganato.com",
        "type": "built-in"
    }
]

# Translation service (placeholder for Google Translate API)
async def translate_text(text: str, target_lang: str = "ar") -> str:
    """Translate text to Arabic using Google Translate API"""
    try:
        # This is a placeholder - in production you'd use Google Translate API
        # For now, returning the original text with [AR] prefix
        return f"[مترجم] {text}"
    except Exception as e:
        return text

# Helper functions
def calculate_directory_size(path: str) -> int:
    """Calculate total size of directory in bytes"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total_size += os.path.getsize(fp)
    except:
        pass
    return total_size

async def fetch_manga_from_source(source_url: str, search_query: str = "") -> List[Dict]:
    """Fetch manga list from a source"""
    try:
        # This is a placeholder implementation
        # In production, you'd implement specific parsers for each source
        sample_manga = [
            {
                "id": f"manga_{uuid.uuid4().hex[:8]}",
                "title": "One Piece",
                "title_ar": "قطعة واحدة",
                "cover_image": "https://via.placeholder.com/300x400",
                "chapters_count": 1000,
                "source": source_url
            },
            {
                "id": f"manga_{uuid.uuid4().hex[:8]}",
                "title": "Naruto",
                "title_ar": "ناروتو",
                "cover_image": "https://via.placeholder.com/300x400",
                "chapters_count": 700,
                "source": source_url
            }
        ]
        return sample_manga
    except Exception as e:
        return []

# API Routes

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/api/sources")
async def get_sources():
    """Get all manga sources (built-in + custom)"""
    # Get custom sources from database
    custom_sources = await db.sources.find({"type": "custom"}).to_list(length=None)
    
    # Combine with built-in sources
    all_sources = BUILT_IN_SOURCES.copy()
    all_sources.extend(custom_sources)
    
    return {"sources": all_sources}

@app.post("/api/sources")
async def add_custom_source(source: dict):
    """Add a custom manga source"""
    # Create MangaSource object with generated ID
    manga_source = MangaSource(
        id=str(uuid.uuid4()),
        name=source.get("name", ""),
        url=source.get("url", ""),
        type="custom",
        enabled=source.get("enabled", True),
        added_date=datetime.now()
    )
    
    # Validate URL
    try:
        response = requests.head(manga_source.url, timeout=5)
        if response.status_code >= 400:
            raise HTTPException(status_code=400, detail="URL is not accessible")
    except:
        raise HTTPException(status_code=400, detail="Invalid or inaccessible URL")
    
    # Save to database
    await db.sources.insert_one(manga_source.dict())
    return {"message": "Source added successfully", "source": manga_source.dict()}

@app.delete("/api/sources/{source_id}")
async def delete_source(source_id: str):
    """Delete a custom source"""
    result = await db.sources.delete_one({"id": source_id, "type": "custom"})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Source not found or cannot be deleted")
    return {"message": "Source deleted successfully"}

@app.get("/api/manga/search")
async def search_manga(query: str = "", source_id: str = ""):
    """Search manga across sources"""
    results = []
    
    if source_id:
        # Search in specific source
        source = await db.sources.find_one({"id": source_id})
        if source:
            manga_list = await fetch_manga_from_source(source["url"], query)
            results.extend(manga_list)
    else:
        # Search in all sources
        sources = await db.sources.find({}).to_list(length=None)
        for source in BUILT_IN_SOURCES + sources:
            manga_list = await fetch_manga_from_source(source["url"], query)
            results.extend(manga_list)
    
    return {"results": results, "count": len(results)}

@app.get("/api/manga/{manga_id}")
async def get_manga_details(manga_id: str):
    """Get detailed manga information"""
    manga = await db.manga.find_one({"id": manga_id})
    if not manga:
        raise HTTPException(status_code=404, detail="Manga not found")
    
    # Get chapters
    chapters = await db.chapters.find({"manga_id": manga_id}).sort("chapter_number", ASCENDING).to_list(length=None)
    manga["chapters"] = chapters
    
    return manga

@app.get("/api/manga/{manga_id}/chapters")
async def get_manga_chapters(manga_id: str):
    """Get manga chapters"""
    chapters = await db.chapters.find({"manga_id": manga_id}).sort("chapter_number", ASCENDING).to_list(length=None)
    return {"chapters": chapters}

@app.get("/api/chapter/{chapter_id}")
async def get_chapter_pages(chapter_id: str):
    """Get chapter pages for reading"""
    chapter = await db.chapters.find_one({"id": chapter_id})
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    return chapter

@app.post("/api/download/manga/{manga_id}")
async def download_manga(manga_id: str):
    """Download entire manga"""
    # This would implement the actual download logic
    # For now, return a placeholder response
    return {"message": "Download started", "manga_id": manga_id, "status": "downloading"}

@app.post("/api/download/chapter/{chapter_id}")
async def download_chapter(chapter_id: str):
    """Download specific chapter"""
    chapter = await db.chapters.find_one({"id": chapter_id})
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Placeholder download logic
    chapter_dir = os.path.join(DOWNLOADS_DIR, chapter["manga_id"], f"chapter_{chapter['chapter_number']}")
    os.makedirs(chapter_dir, exist_ok=True)
    
    # Update download status
    await db.chapters.update_one(
        {"id": chapter_id},
        {"$set": {"download_status": "downloading", "download_path": chapter_dir}}
    )
    
    return {"message": "Chapter download started", "chapter_id": chapter_id}

@app.get("/api/downloads/stats")
async def get_download_stats():
    """Get download statistics"""
    total_manga = await db.manga.count_documents({"download_status": "completed"})
    total_chapters = await db.chapters.count_documents({"download_status": "completed"})
    total_size = calculate_directory_size(DOWNLOADS_DIR)
    
    # Get available disk space (simplified)
    import shutil
    _, _, available_space = shutil.disk_usage(DOWNLOADS_DIR)
    
    return {
        "total_manga": total_manga,
        "total_chapters": total_chapters,
        "total_size": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "available_space": available_space,
        "available_space_gb": round(available_space / (1024 * 1024 * 1024), 2)
    }

@app.get("/api/downloads")
async def get_downloads():
    """Get all downloaded manga"""
    downloaded_manga = await db.manga.find({"download_status": {"$in": ["downloading", "completed"]}}).to_list(length=None)
    return {"downloads": downloaded_manga}

@app.post("/api/translate")
async def translate_chapter(chapter_id: str, target_lang: str = "ar"):
    """Translate chapter text to Arabic"""
    chapter = await db.chapters.find_one({"id": chapter_id})
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Translate title if not already in Arabic
    if not chapter.get("title_ar"):
        translated_title = await translate_text(chapter["title"], target_lang)
        await db.chapters.update_one(
            {"id": chapter_id},
            {"$set": {"title_ar": translated_title}}
        )
    
    return {"message": "Translation completed", "chapter_id": chapter_id}

@app.get("/api/preferences")
async def get_user_preferences():
    """Get user preferences"""
    try:
        prefs = await db.preferences.find_one({"user": "default"})
        if not prefs:
            # Return default preferences
            default_prefs = UserPreferences()
            await db.preferences.insert_one({
                "user": "default",
                **default_prefs.dict()
            })
            return default_prefs.dict()
        return prefs
    except Exception as e:
        # Return default preferences if database error
        default_prefs = UserPreferences()
        return default_prefs.dict()

@app.post("/api/preferences")
async def update_user_preferences(preferences: UserPreferences):
    """Update user preferences"""
    await db.preferences.update_one(
        {"user": "default"},
        {"$set": preferences.dict()},
        upsert=True
    )
    return {"message": "Preferences updated successfully"}

@app.post("/api/reading-progress")
async def update_reading_progress(manga_id: str, chapter_id: str, page: int):
    """Update reading progress"""
    progress = {
        "manga_id": manga_id,
        "chapter_id": chapter_id,
        "page": page,
        "timestamp": datetime.now()
    }
    
    await db.reading_progress.update_one(
        {"manga_id": manga_id},
        {"$set": progress},
        upsert=True
    )
    
    return {"message": "Progress updated"}

@app.get("/api/reading-progress/{manga_id}")
async def get_reading_progress(manga_id: str):
    """Get reading progress for manga"""
    progress = await db.reading_progress.find_one({"manga_id": manga_id})
    if not progress:
        return {"manga_id": manga_id, "chapter_id": None, "page": 0}
    return progress

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)