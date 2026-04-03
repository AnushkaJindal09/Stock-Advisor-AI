/*
import { useEffect, useState } from "react";
import { Link } from 'react-router-dom';

function NewsFeed() {
  const [news, setNews] = useState([]);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [menuOpen, setMenuOpen] = useState(false);
  const finnhubApiKey = import.meta.env.VITE_FINNHUB_API_KEY;
  const gnewsApiKey = import.meta.env.VITE_GNEWS_API_KEY;

  const QUICK_TOPICS = ["Nifty 50", "Sensex", "Reliance", "TCS", "HDFC", "IPO", "RBI"];

  useEffect(() => {
    const fetchNews = async () => {
      setLoading(true); 
      try {
        let response, data;
        if (query.trim() === "") {
          response = await fetch(`https://finnhub.io/api/v1/news?category=general&token=${finnhubApiKey}`);
          data = await response.json();
          setNews(Array.isArray(data) ? data : []);
        } else {
          response = await fetch(`https://gnews.io/api/v4/search?q=${encodeURIComponent(query)}&lang=en&country=in&max=10&token=${gnewsApiKey}`);
          data = await response.json();
          setNews(Array.isArray(data.articles) ? data.articles : []);
        }
      } catch (error) {
        console.error("Error fetching news:", error);
        setNews([]);
      }
      setLoading(false);
    };
    fetchNews();
  }, [query]);

  const handleSearch = () => setQuery(search.trim());
  const handleKeyDown = (e) => { if (e.key === "Enter") handleSearch(); };

  const formatTime = (item) => {
    try {
      const d = item.datetime ? new Date(item.datetime * 1000) : new Date(item.publishedAt);
      const now = new Date();
      const diff = Math.floor((now - d) / 60000);
      if (diff < 60) return `${diff}m ago`;
      if (diff < 1440) return `${Math.floor(diff / 60)}h ago`;
      return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
    } catch { return ""; }
  };

  const getSource = (item) => {
    if (item.source) return typeof item.source === 'object' ? item.source.name : item.source;
    return "News";
  };

  const hasGoodImage = (item) => {
    const img = item.image || item.urlToImage;
    if (!img) return false;
    const skipDomains = ['reuters.com/pf/resources', 'placeholder', 'logo'];
    return !skipDomains.some(d => img.includes(d));
  };

  const NewsCard = ({ item, featured = false }) => {
    const title = item.headline || item.title || "";
    const summary = item.summary || item.description || "";
    const image = hasGoodImage(item) ? (item.image || item.urlToImage) : null;
    const url = item.url;
    const source = getSource(item);
    const time = formatTime(item);

    if (featured) {
      return (
        <a href={url} target="_blank" rel="noopener noreferrer"
          className="group bg-gray-900 rounded-2xl border border-white/10 overflow-hidden hover:border-cyan-500/30 transition-all duration-300 flex flex-col md:flex-row"
        >
          {image ? (
            <div className="md:w-2/5 h-48 md:h-auto overflow-hidden bg-gray-800 flex-shrink-0">
              <img src={image} alt={title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                onError={(e) => e.target.parentElement.style.display = 'none'} />
            </div>
          ) : (
            <div className="md:w-2/5 h-48 md:h-auto bg-gradient-to-br from-blue-900/40 to-cyan-900/40 flex items-center justify-center flex-shrink-0">
              <span className="text-5xl">📈</span>
            </div>
          )}
          <div className="p-4 md:p-6 flex flex-col justify-between flex-1">
            <div>
              <div className="flex items-center gap-2 mb-3 flex-wrap">
                <span className="text-xs px-2 py-1 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-medium">Top Story</span>
                <span className="text-xs px-2 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">{source}</span>
                <span className="text-xs text-gray-600 ml-auto">{time}</span>
              </div>
              <h2 className="text-white font-bold text-lg md:text-xl leading-snug mb-3 group-hover:text-cyan-400 transition line-clamp-3">{title}</h2>
              {summary && <p className="text-gray-500 text-sm leading-relaxed line-clamp-2 md:line-clamp-3">{summary}</p>}
            </div>
            <div className="mt-4 text-sm text-cyan-600 group-hover:text-cyan-400 transition font-medium">Read full article →</div>
          </div>
        </a>
      );
    }

    return (
      <a href={url} target="_blank" rel="noopener noreferrer"
        className="group bg-gray-900 rounded-2xl border border-white/10 overflow-hidden hover:border-cyan-500/30 transition-all duration-300 flex flex-col"
      >
        {image ? (
          <div className="h-36 overflow-hidden bg-gray-800">
            <img src={image} alt={title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
              onError={(e) => e.target.parentElement.style.display = 'none'} />
          </div>
        ) : (
          <div className="h-36 bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center border-b border-white/5">
            <span className="text-3xl opacity-40">📰</span>
          </div>
        )}
        <div className="p-4 flex flex-col flex-1">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">{source}</span>
            <span className="text-xs text-gray-600">{time}</span>
          </div>
          <h2 className="text-white font-semibold text-sm leading-snug mb-2 group-hover:text-cyan-400 transition line-clamp-2">{title}</h2>
          {summary && <p className="text-gray-500 text-xs leading-relaxed line-clamp-2 flex-1">{summary}</p>}
          <div className="mt-3 text-xs text-cyan-600 group-hover:text-cyan-400 transition font-medium">Read full article →</div>
        </div>
      </a>
    );
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">

    
      <div className="border-b border-white/10 bg-gray-950/80 backdrop-blur sticky top-0 z-50">
        <div className="px-4 md:px-8 py-4 flex items-center justify-between">
          <div className="text-2xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-cyan-400 to-emerald-400">FinTrack</div>

         
          <div className="hidden md:flex gap-8 text-sm text-gray-400">
            <Link to="/home" className="hover:text-white transition">Home</Link>
            <Link to="/graph" className="hover:text-white transition">Forecast</Link>
            <Link to="/news" className="text-white font-semibold">News</Link>
            <Link to="/portfolio" className="hover:text-white transition">Portfolio</Link>
          </div>

          
          <button className="md:hidden text-gray-300 hover:text-white" onClick={() => setMenuOpen(!menuOpen)}>
            {menuOpen ? '✕' : '☰'}
          </button>
        </div>

       
        {menuOpen && (
          <div className="md:hidden bg-black/90 border-t border-white/10 px-6 py-4 flex flex-col gap-4">
            {[
              { label: "Home", to: "/home" },
              { label: "Forecast", to: "/graph" },
              { label: "News", to: "/news" },
              { label: "Portfolio", to: "/portfolio" },
            ].map((link) => (
              <Link key={link.to} to={link.to} onClick={() => setMenuOpen(false)}
                className="text-gray-300 hover:text-white text-sm font-medium transition">
                {link.label}
              </Link>
            ))}
          </div>
        )}
      </div>

      <div className="max-w-6xl mx-auto px-4 md:px-6 py-6 md:py-10">

        <div className="mb-6 md:mb-8">
          <div className="text-xs text-cyan-500 tracking-widest uppercase mb-2">Live Updates</div>
          <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">Market News</h1>
          <p className="text-gray-400 text-sm">Latest stock market news — India & Global</p>
        </div>

      
        <div className="mb-6">
          <div className="flex gap-2 md:gap-3 mb-4">
            <div className="flex-1 relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">🔍</span>
              <input type="text" placeholder="Search company, sector, topic..."
                value={search} onChange={(e) => setSearch(e.target.value)} onKeyDown={handleKeyDown}
                className="w-full bg-gray-900 border border-white/10 rounded-xl pl-10 pr-4 py-3 text-white text-sm placeholder-gray-600 focus:outline-none focus:border-cyan-500/50 transition"
              />
            </div>
            <button onClick={handleSearch} className="px-4 md:px-6 py-3 rounded-xl font-semibold text-sm bg-gradient-to-r from-blue-600 via-cyan-600 to-emerald-600 hover:opacity-90 transition">
              Search
            </button>
            {query && (
              <button onClick={() => { setQuery(""); setSearch(""); }} className="px-3 md:px-4 py-3 rounded-xl text-sm border border-white/10 text-gray-400 hover:text-white transition">
                ✕
              </button>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            {QUICK_TOPICS.map((topic) => (
              <button key={topic} onClick={() => { setSearch(topic); setQuery(topic); }}
                className={`px-3 py-1.5 rounded-full text-xs font-medium border transition ${query === topic ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-400' : 'bg-gray-900 border-white/10 text-gray-400 hover:text-white hover:border-white/30'}`}>
                {topic}
              </button>
            ))}
          </div>
        </div>

     
        {!loading && news.length > 0 && (
          <div className="text-xs text-gray-600 mb-5">{query ? `${news.length} results for "${query}"` : `${news.length} latest articles`}</div>
        )}

        
        {loading && (
          <div className="flex items-center justify-center py-24">
            <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
        )}

       
        {!loading && news.length === 0 && (
          <div className="text-center py-24 text-gray-600">
            <div className="text-4xl mb-3">📭</div>
            <p>No news found</p>
            <p className="text-xs mt-1">Try a different search term</p>
          </div>
        )}

      
        {!loading && news.length > 0 && (
          <div className="space-y-4">
           
            <NewsCard item={news[0]} featured={true} />
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {news.slice(1, 19).map((item, index) => (
                <NewsCard key={index} item={item} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default NewsFeed;
*/


import { useEffect, useState } from "react";
import { Link } from 'react-router-dom';

function NewsFeed() {
  const [news, setNews] = useState([]);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [menuOpen, setMenuOpen] = useState(false);

  const QUICK_TOPICS = ["Nifty 50", "Sensex", "Reliance", "TCS", "HDFC", "IPO", "RBI"];

  useEffect(() => {
    const fetchNews = async () => {
      setLoading(true);
      try {
        let response, data;
        if (query.trim() === "") {
          response = await fetch(`https://stock-backend-gsyw.onrender.com/news?company=Nifty`);
          data = await response.json();
          setNews(Array.isArray(data.articles) ? data.articles : []);
        } else {
          response = await fetch(`https://stock-backend-gsyw.onrender.com/news?company=${encodeURIComponent(query)}`);
          data = await response.json();
          setNews(Array.isArray(data.articles) ? data.articles : []);
        }
      } catch (error) {
        console.error("Error fetching news:", error);
        setNews([]);
      }
      setLoading(false);
    };
    fetchNews();
  }, [query]);

  const handleSearch = () => setQuery(search.trim());
  const handleKeyDown = (e) => { if (e.key === "Enter") handleSearch(); };

  const formatTime = (item) => {
    try {
      const d = item.datetime ? new Date(item.datetime * 1000) : new Date(item.publishedAt);
      const now = new Date();
      const diff = Math.floor((now - d) / 60000);
      if (diff < 60) return `${diff}m ago`;
      if (diff < 1440) return `${Math.floor(diff / 60)}h ago`;
      return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
    } catch { return ""; }
  };

  const getSource = (item) => {
    if (item.source) return typeof item.source === 'object' ? item.source.name : item.source;
    return "News";
  };

  const hasGoodImage = (item) => {
    const img = item.image || item.urlToImage;
    if (!img) return false;
    const skipDomains = ['reuters.com/pf/resources', 'placeholder', 'logo'];
    return !skipDomains.some(d => img.includes(d));
  };

  const NewsCard = ({ item, featured = false }) => {
    const title = item.headline || item.title || "";
    const summary = item.summary || item.description || "";
    const image = hasGoodImage(item) ? (item.image || item.urlToImage) : null;
    const url = item.url;
    const source = getSource(item);
    const time = formatTime(item);

    if (featured) {
      return (
        <a href={url} target="_blank" rel="noopener noreferrer"
          className="group bg-gray-900 rounded-2xl border border-white/10 overflow-hidden hover:border-cyan-500/30 transition-all duration-300 flex flex-col md:flex-row"
        >
          {image ? (
            <div className="md:w-2/5 h-48 md:h-auto overflow-hidden bg-gray-800 flex-shrink-0">
              <img src={image} alt={title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                onError={(e) => e.target.parentElement.style.display = 'none'} />
            </div>
          ) : (
            <div className="md:w-2/5 h-48 md:h-auto bg-gradient-to-br from-blue-900/40 to-cyan-900/40 flex items-center justify-center flex-shrink-0">
              <span className="text-5xl">📈</span>
            </div>
          )}
          <div className="p-4 md:p-6 flex flex-col justify-between flex-1">
            <div>
              <div className="flex items-center gap-2 mb-3 flex-wrap">
                <span className="text-xs px-2 py-1 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-medium">Top Story</span>
                <span className="text-xs px-2 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">{source}</span>
                <span className="text-xs text-gray-600 ml-auto">{time}</span>
              </div>
              <h2 className="text-white font-bold text-lg md:text-xl leading-snug mb-3 group-hover:text-cyan-400 transition line-clamp-3">{title}</h2>
              {summary && <p className="text-gray-500 text-sm leading-relaxed line-clamp-2 md:line-clamp-3">{summary}</p>}
            </div>
            <div className="mt-4 text-sm text-cyan-600 group-hover:text-cyan-400 transition font-medium">Read full article →</div>
          </div>
        </a>
      );
    }

    return (
      <a href={url} target="_blank" rel="noopener noreferrer"
        className="group bg-gray-900 rounded-2xl border border-white/10 overflow-hidden hover:border-cyan-500/30 transition-all duration-300 flex flex-col"
      >
        {image ? (
          <div className="h-36 overflow-hidden bg-gray-800">
            <img src={image} alt={title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
              onError={(e) => e.target.parentElement.style.display = 'none'} />
          </div>
        ) : (
          <div className="h-36 bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center border-b border-white/5">
            <span className="text-3xl opacity-40">📰</span>
          </div>
        )}
        <div className="p-4 flex flex-col flex-1">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">{source}</span>
            <span className="text-xs text-gray-600">{time}</span>
          </div>
          <h2 className="text-white font-semibold text-sm leading-snug mb-2 group-hover:text-cyan-400 transition line-clamp-2">{title}</h2>
          {summary && <p className="text-gray-500 text-xs leading-relaxed line-clamp-2 flex-1">{summary}</p>}
          <div className="mt-3 text-xs text-cyan-600 group-hover:text-cyan-400 transition font-medium">Read full article →</div>
        </div>
      </a>
    );
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="border-b border-white/10 bg-gray-950/80 backdrop-blur sticky top-0 z-50">
        <div className="px-4 md:px-8 py-4 flex items-center justify-between">
          <div className="text-2xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-cyan-400 to-emerald-400">FinTrack</div>
          <div className="hidden md:flex gap-8 text-sm text-gray-400">
            <Link to="/home" className="hover:text-white transition">Home</Link>
            <Link to="/graph" className="hover:text-white transition">Forecast</Link>
            <Link to="/news" className="text-white font-semibold">News</Link>
            <Link to="/portfolio" className="hover:text-white transition">Portfolio</Link>
          </div>
          <button className="md:hidden text-gray-300 hover:text-white" onClick={() => setMenuOpen(!menuOpen)}>
            {menuOpen ? '✕' : '☰'}
          </button>
        </div>
        {menuOpen && (
          <div className="md:hidden bg-black/90 border-t border-white/10 px-6 py-4 flex flex-col gap-4">
            {[
              { label: "Home", to: "/home" },
              { label: "Forecast", to: "/graph" },
              { label: "News", to: "/news" },
              { label: "Portfolio", to: "/portfolio" },
            ].map((link) => (
              <Link key={link.to} to={link.to} onClick={() => setMenuOpen(false)}
                className="text-gray-300 hover:text-white text-sm font-medium transition">
                {link.label}
              </Link>
            ))}
          </div>
        )}
      </div>

      <div className="max-w-6xl mx-auto px-4 md:px-6 py-6 md:py-10">
        <div className="mb-6 md:mb-8">
          <div className="text-xs text-cyan-500 tracking-widest uppercase mb-2">Live Updates</div>
          <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">Market News</h1>
          <p className="text-gray-400 text-sm">Latest stock market news — India & Global</p>
        </div>

        <div className="mb-6">
          <div className="flex gap-2 md:gap-3 mb-4">
            <div className="flex-1 relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">🔍</span>
              <input type="text" placeholder="Search company, sector, topic..."
                value={search} onChange={(e) => setSearch(e.target.value)} onKeyDown={handleKeyDown}
                className="w-full bg-gray-900 border border-white/10 rounded-xl pl-10 pr-4 py-3 text-white text-sm placeholder-gray-600 focus:outline-none focus:border-cyan-500/50 transition"
              />
            </div>
            <button onClick={handleSearch} className="px-4 md:px-6 py-3 rounded-xl font-semibold text-sm bg-gradient-to-r from-blue-600 via-cyan-600 to-emerald-600 hover:opacity-90 transition">
              Search
            </button>
            {query && (
              <button onClick={() => { setQuery(""); setSearch(""); }} className="px-3 md:px-4 py-3 rounded-xl text-sm border border-white/10 text-gray-400 hover:text-white transition">
                ✕
              </button>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            {QUICK_TOPICS.map((topic) => (
              <button key={topic} onClick={() => { setSearch(topic); setQuery(topic); }}
                className={`px-3 py-1.5 rounded-full text-xs font-medium border transition ${query === topic ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-400' : 'bg-gray-900 border-white/10 text-gray-400 hover:text-white hover:border-white/30'}`}>
                {topic}
              </button>
            ))}
          </div>
        </div>

        {!loading && news.length > 0 && (
          <div className="text-xs text-gray-600 mb-5">{query ? `${news.length} results for "${query}"` : `${news.length} latest articles`}</div>
        )}

        {loading && (
          <div className="flex items-center justify-center py-24">
            <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
        )}

        {!loading && news.length === 0 && (
          <div className="text-center py-24 text-gray-600">
            <div className="text-4xl mb-3">📭</div>
            <p>No news found</p>
            <p className="text-xs mt-1">Try a different search term</p>
          </div>
        )}

        {!loading && news.length > 0 && (
          <div className="space-y-4">
            <NewsCard item={news[0]} featured={true} />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {news.slice(1, 19).map((item, index) => (
                <NewsCard key={index} item={item} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default NewsFeed;