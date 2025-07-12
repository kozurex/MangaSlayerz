import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import './App.css';

// API Service
const API_BASE = process.env.REACT_APP_BACKEND_URL;

const api = {
  get: async (endpoint) => {
    const response = await fetch(`${API_BASE}/api${endpoint}`);
    return response.json();
  },
  post: async (endpoint, data) => {
    const response = await fetch(`${API_BASE}/api${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return response.json();
  },
  delete: async (endpoint) => {
    const response = await fetch(`${API_BASE}/api${endpoint}`, {
      method: 'DELETE'
    });
    return response.json();
  }
};

// Main App Component
function App() {
  return (
    <div className="app rtl" dir="rtl">
      <Router>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/sources" element={<SourcesPage />} />
          <Route path="/library" element={<LibraryPage />} />
          <Route path="/manga/:id" element={<MangaDetailPage />} />
          <Route path="/reader/:chapterId" element={<ReaderPage />} />
          <Route path="/downloads" element={<DownloadsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </Router>
    </div>
  );
}

// Navigation Component
const Navigation = ({ currentPage, onPageChange }) => {
  const navItems = [
    { id: 'home', label: 'الرئيسية', icon: '🏠' },
    { id: 'sources', label: 'المصادر', icon: '🔗' },
    { id: 'library', label: 'المكتبة', icon: '📚' },
    { id: 'downloads', label: 'التحميلات', icon: '⬇️' },
    { id: 'settings', label: 'الإعدادات', icon: '⚙️' }
  ];

  return (
    <nav className="bottom-nav">
      {navItems.map(item => (
        <button
          key={item.id}
          className={`nav-item ${currentPage === item.id ? 'active' : ''}`}
          onClick={() => onPageChange(item.id)}
        >
          <span className="nav-icon">{item.icon}</span>
          <span className="nav-label">{item.label}</span>
        </button>
      ))}
    </nav>
  );
};

// Home Page Component
const HomePage = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [recentManga, setRecentManga] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    loadRecentManga();
  }, []);

  const loadRecentManga = async () => {
    try {
      const response = await api.get('/manga/search?query=');
      setRecentManga(response.results.slice(0, 6));
    } catch (error) {
      console.error('Error loading recent manga:', error);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    try {
      const response = await api.get(`/manga/search?query=${encodeURIComponent(searchQuery)}`);
      setSearchResults(response.results);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div 
      className="page home-page"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <header className="page-header">
        <h1 className="app-title">مانغا سلاير</h1>
        <p className="app-subtitle">قارئ المانجا العربي المتقدم</p>
      </header>

      <div className="search-section">
        <div className="search-container">
          <input
            type="text"
            className="search-input"
            placeholder="ابحث عن المانجا..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button className="search-button" onClick={handleSearch} disabled={loading}>
            {loading ? '🔄' : '🔍'}
          </button>
        </div>
      </div>

      {searchResults.length > 0 && (
        <section className="results-section">
          <h2 className="section-title">نتائج البحث</h2>
          <div className="manga-grid">
            {searchResults.map(manga => (
              <MangaCard key={manga.id} manga={manga} onClick={() => navigate(`/manga/${manga.id}`)} />
            ))}
          </div>
        </section>
      )}

      <section className="recent-section">
        <h2 className="section-title">المانجا الحديثة</h2>
        <div className="manga-grid">
          {recentManga.map(manga => (
            <MangaCard key={manga.id} manga={manga} onClick={() => navigate(`/manga/${manga.id}`)} />
          ))}
        </div>
      </section>

      <Navigation currentPage="home" onPageChange={(page) => navigate(`/${page === 'home' ? '' : page}`)} />
    </motion.div>
  );
};

// Manga Card Component
const MangaCard = ({ manga, onClick }) => (
  <motion.div 
    className="manga-card"
    onClick={onClick}
    whileHover={{ scale: 1.05 }}
    whileTap={{ scale: 0.95 }}
  >
    <div className="manga-cover">
      <img src={manga.cover_image || '/placeholder-manga.jpg'} alt={manga.title} />
    </div>
    <div className="manga-info">
      <h3 className="manga-title">{manga.title_ar || manga.title}</h3>
      <p className="manga-chapters">{manga.chapters_count || 0} فصل</p>
    </div>
  </motion.div>
);

// Sources Page Component
const SourcesPage = () => {
  const [sources, setSources] = useState([]);
  const [newSourceUrl, setNewSourceUrl] = useState('');
  const [newSourceName, setNewSourceName] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadSources();
  }, []);

  const loadSources = async () => {
    try {
      const response = await api.get('/sources');
      setSources(response.sources);
    } catch (error) {
      console.error('Error loading sources:', error);
    }
  };

  const addSource = async () => {
    if (!newSourceUrl.trim() || !newSourceName.trim()) return;
    
    setLoading(true);
    try {
      await api.post('/sources', {
        name: newSourceName,
        url: newSourceUrl,
        enabled: true
      });
      setNewSourceUrl('');
      setNewSourceName('');
      loadSources();
    } catch (error) {
      alert('خطأ في إضافة المصدر: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const deleteSource = async (sourceId) => {
    try {
      await api.delete(`/sources/${sourceId}`);
      loadSources();
    } catch (error) {
      alert('خطأ في حذف المصدر');
    }
  };

  return (
    <motion.div 
      className="page sources-page"
      initial={{ opacity: 0, x: 300 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3 }}
    >
      <header className="page-header">
        <h1 className="page-title">مصادر المانجا</h1>
      </header>

      <div className="add-source-section">
        <h2 className="section-title">إضافة مصدر جديد</h2>
        <div className="input-group">
          <input
            type="text"
            className="text-input"
            placeholder="اسم المصدر"
            value={newSourceName}
            onChange={(e) => setNewSourceName(e.target.value)}
          />
          <input
            type="url"
            className="text-input"
            placeholder="رابط الموقع"
            value={newSourceUrl}
            onChange={(e) => setNewSourceUrl(e.target.value)}
          />
          <button 
            className="primary-button" 
            onClick={addSource}
            disabled={loading}
          >
            {loading ? 'جاري الإضافة...' : 'إضافة المصدر'}
          </button>
        </div>
      </div>

      <div className="sources-list">
        <h2 className="section-title">المصادر المتاحة</h2>
        {sources.map(source => (
          <div key={source.id} className="source-item">
            <div className="source-info">
              <h3 className="source-name">{source.name}</h3>
              <p className="source-url">{source.url}</p>
              <span className={`source-type ${source.type}`}>
                {source.type === 'built-in' ? 'مدمج' : 'مخصص'}
              </span>
            </div>
            <div className="source-actions">
              {source.type === 'custom' && (
                <button 
                  className="delete-button"
                  onClick={() => deleteSource(source.id)}
                >
                  🗑️
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      <Navigation currentPage="sources" onPageChange={(page) => navigate(`/${page === 'home' ? '' : page}`)} />
    </motion.div>
  );
};

// Downloads Page Component
const DownloadsPage = () => {
  const [downloads, setDownloads] = useState([]);
  const [stats, setStats] = useState({});
  const navigate = useNavigate();

  useEffect(() => {
    loadDownloads();
    loadStats();
  }, []);

  const loadDownloads = async () => {
    try {
      const response = await api.get('/downloads');
      setDownloads(response.downloads);
    } catch (error) {
      console.error('Error loading downloads:', error);
    }
  };

  const loadStats = async () => {
    try {
      const response = await api.get('/downloads/stats');
      setStats(response);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const formatSize = (bytes) => {
    if (bytes === 0) return '0 بايت';
    const k = 1024;
    const sizes = ['بايت', 'ك.بايت', 'م.بايت', 'ج.بايت'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <motion.div 
      className="page downloads-page"
      initial={{ opacity: 0, y: 300 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <header className="page-header">
        <h1 className="page-title">التحميلات</h1>
      </header>

      <div className="stats-section">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">📚</div>
            <div className="stat-info">
              <div className="stat-value">{stats.total_manga || 0}</div>
              <div className="stat-label">مانجا محملة</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">📄</div>
            <div className="stat-info">
              <div className="stat-value">{stats.total_chapters || 0}</div>
              <div className="stat-label">فصل محمل</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">💾</div>
            <div className="stat-info">
              <div className="stat-value">{formatSize(stats.total_size || 0)}</div>
              <div className="stat-label">الحجم المستخدم</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">📀</div>
            <div className="stat-info">
              <div className="stat-value">{formatSize(stats.available_space || 0)}</div>
              <div className="stat-label">المساحة المتاحة</div>
            </div>
          </div>
        </div>
      </div>

      <div className="downloads-list">
        <h2 className="section-title">المانجا المحملة</h2>
        {downloads.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📥</div>
            <p className="empty-text">لم يتم تحميل أي مانجا بعد</p>
          </div>
        ) : (
          downloads.map(manga => (
            <div key={manga.id} className="download-item">
              <div className="download-cover">
                <img src={manga.cover_image || '/placeholder-manga.jpg'} alt={manga.title} />
              </div>
              <div className="download-info">
                <h3 className="download-title">{manga.title_ar || manga.title}</h3>
                <p className="download-size">{formatSize(manga.total_size || 0)}</p>
                <div className="download-status">
                  <span className={`status-badge ${manga.download_status}`}>
                    {manga.download_status === 'completed' ? 'مكتمل' : 
                     manga.download_status === 'downloading' ? 'جاري التحميل' : 'غير محمل'}
                  </span>
                </div>
              </div>
              <button 
                className="read-button"
                onClick={() => navigate(`/manga/${manga.id}`)}
              >
                قراءة
              </button>
            </div>
          ))
        )}
      </div>

      <Navigation currentPage="downloads" onPageChange={(page) => navigate(`/${page === 'home' ? '' : page}`)} />
    </motion.div>
  );
};

// Settings Page Component  
const SettingsPage = () => {
  const [preferences, setPreferences] = useState({
    auto_scroll: { speed: 3, enabled: false, pause_on_tap: true },
    language: 'ar',
    reading_direction: 'rtl',
    auto_translate: true
  });
  const navigate = useNavigate();

  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    try {
      const response = await api.get('/preferences');
      setPreferences(response);
    } catch (error) {
      console.error('Error loading preferences:', error);
    }
  };

  const savePreferences = async () => {
    try {
      await api.post('/preferences', preferences);
      alert('تم حفظ الإعدادات بنجاح');
    } catch (error) {
      alert('خطأ في حفظ الإعدادات');
    }
  };

  const updatePreference = (path, value) => {
    setPreferences(prev => {
      const newPrefs = { ...prev };
      const keys = path.split('.');
      let current = newPrefs;
      for (let i = 0; i < keys.length - 1; i++) {
        current = current[keys[i]];
      }
      current[keys[keys.length - 1]] = value;
      return newPrefs;
    });
  };

  return (
    <motion.div 
      className="page settings-page"
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      <header className="page-header">
        <h1 className="page-title">الإعدادات</h1>
      </header>

      <div className="settings-sections">
        <div className="settings-section">
          <h2 className="section-title">التمرير التلقائي</h2>
          <div className="setting-item">
            <label className="setting-label">
              <input
                type="checkbox"
                checked={preferences.auto_scroll?.enabled || false}
                onChange={(e) => updatePreference('auto_scroll.enabled', e.target.checked)}
              />
              تفعيل التمرير التلقائي
            </label>
          </div>
          <div className="setting-item">
            <label className="setting-label">سرعة التمرير</label>
            <input
              type="range"
              min="1"
              max="10"
              value={preferences.auto_scroll?.speed || 3}
              onChange={(e) => updatePreference('auto_scroll.speed', parseInt(e.target.value))}
              className="speed-slider"
            />
            <span className="speed-value">{preferences.auto_scroll?.speed || 3}</span>
          </div>
          <div className="setting-item">
            <label className="setting-label">
              <input
                type="checkbox"
                checked={preferences.auto_scroll?.pause_on_tap || true}
                onChange={(e) => updatePreference('auto_scroll.pause_on_tap', e.target.checked)}
              />
              إيقاف مؤقت عند اللمس
            </label>
          </div>
        </div>

        <div className="settings-section">
          <h2 className="section-title">اللغة والترجمة</h2>
          <div className="setting-item">
            <label className="setting-label">
              <input
                type="checkbox"
                checked={preferences.auto_translate || true}
                onChange={(e) => updatePreference('auto_translate', e.target.checked)}
              />
              ترجمة الفصول الإنجليزية تلقائياً
            </label>
          </div>
        </div>

        <div className="settings-section">
          <h2 className="section-title">معلومات التطبيق</h2>
          <div className="setting-item">
            <p className="app-info">الإصدار: 1.0.0</p>
            <p className="app-info">مطور من فريق مانغا سلاير</p>
          </div>
        </div>
      </div>

      <button className="save-button" onClick={savePreferences}>
        حفظ الإعدادات
      </button>

      <Navigation currentPage="settings" onPageChange={(page) => navigate(`/${page === 'home' ? '' : page}`)} />
    </motion.div>
  );
};

// Library Page (placeholder)
const LibraryPage = () => {
  const navigate = useNavigate();
  
  return (
    <motion.div 
      className="page library-page"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <header className="page-header">
        <h1 className="page-title">المكتبة</h1>
      </header>
      <div className="empty-state">
        <div className="empty-icon">📚</div>
        <p className="empty-text">المكتبة فارغة حالياً</p>
      </div>
      <Navigation currentPage="library" onPageChange={(page) => navigate(`/${page === 'home' ? '' : page}`)} />
    </motion.div>
  );
};

// Manga Detail Page (placeholder)
const MangaDetailPage = () => {
  const navigate = useNavigate();
  
  return (
    <motion.div className="page manga-detail-page">
      <div className="back-button" onClick={() => navigate(-1)}>← العودة</div>
      <p>تفاصيل المانجا</p>
    </motion.div>
  );
};

// Reader Page (placeholder)
const ReaderPage = () => {
  const navigate = useNavigate();
  
  return (
    <motion.div className="page reader-page">
      <div className="back-button" onClick={() => navigate(-1)}>← العودة</div>
      <p>قارئ المانجا</p>
    </motion.div>
  );
};

export default App;