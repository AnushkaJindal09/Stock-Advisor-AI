import { useEffect, useState } from "react";
import { Link } from 'react-router-dom';

function NewsFeed() {
  const [news, setNews] = useState([]);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
    const finnhubApiKey = import.meta.env.VITE_FINNHUB_API_KEY;
  const gnewsApiKey = import.meta.env.VITE_GNEWS_API_KEY;

  useEffect(() => {
    const fetchNews = async () => {
      try {
        let response;
        let data;

        if (query.trim() === "") {
          // Default load: FINNHUB
          response = await fetch(
            `https://finnhub.io/api/v1/news?category=general&token=${finnhubApiKey}`
          );
          data = await response.json();
          if (Array.isArray(data)) {
            setNews(data); // Use directly from Finnhub
          } else {
            console.error("Finnhub format error:", data);
            setNews([]);
          }
        } else {
          // Search-based: GNEWS
          response = await fetch(
            `https://gnews.io/api/v4/search?q=${encodeURIComponent(query)}&lang=en&country=in&max=10&token=${gnewsApiKey}`
          );
          data = await response.json();
          if (Array.isArray(data.articles)) {
            setNews(data.articles); // GNews returns { articles: [...] }
          } else {
            console.error("GNews format error:", data);
            setNews([]);
          }
        }
      } catch (error) {
        console.error("Error fetching news:", error);
        setNews([]);
      }
    };

    fetchNews();
  }, [query]);

  const handleSearch = () => {
    setQuery(search.trim());
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

/*function NewsFeed() {
  const [news, setNews] = useState([]);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState(""); 
  const finnhubApiKey = import.meta.env.VITE_FINNHUB_API_KEY;
  const gnewsApiKey = import.meta.env.VITE_GNEWS_API_KEY;

  useEffect(() => {
    async function fetchNews() {
      try {
        let response;
        if (query.trim() === "") {
          
          response = await fetch(
            `https://finnhub.io/api/v1/news?category=general&token=${finnhubApiKey}`
          );
        } else {
         
          response = await fetch(
            `https://gnews.io/api/v4/search?q=${encodeURIComponent(
              query
            )}&lang=en&country=in&max=10&token=${gnewsApiKey}`
          );
        }

        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();

        
        if (Array.isArray(data.articles)) {
          setNews(data.articles); // GNews
        } else if (Array.isArray(data)) {
          setNews(data); // Finnhub
        } else {
          setNews([]);
          console.error("Unexpected format", data);
        }
      } catch (error) {
        console.error("Error fetching news:", error);
        setNews([]);
      }
    }

    fetchNews();
  }, [query]); 

  
  const handleSearch = () => {
    setQuery(search.trim()); 
  };


  const handleKeyDown = (event) => {
    if (event.key === "Enter") {
      handleSearch();
    }
  };
*/
  return (
    <div className="bg-black text-white  px-1 min-h-screen">
      <div className="sticky top-0 z-50 backdrop-blur-md bg-black/20 shadow-md">
      <div className="w-full mb-9 px-6 py-4 bg-white/10 flex items-center justify-between">
        {/* Logo */}
        <div className="text-2xl sm:text-3xl  font-extrabold tracking-wide text-transparent bg-clip-text bg-gradient-to-r from-blue-500 via-cyan-400 to-green-400 select-none">
          FinTrack
        </div>

        {/* Nav Links */}
        <div className="space-x-6 text-sm sm:text-base font-medium tracking-wide text-white">
          <Link
            to="/home"
            className="relative group hover:text-cyan-400 transition"
          >
            Home
            <span className="absolute left-0 -bottom-0.5 w-0 h-0.5 bg-cyan-400 transition-all duration-300 group-hover:w-full"></span>
          </Link>
          <Link
            to="/graph"
            className="relative group hover:text-cyan-400 transition"
          >
            Forecast
            <span className="absolute left-0 -bottom-0.5 w-0 h-0.5 bg-cyan-400 transition-all duration-300 group-hover:w-full"></span>
          </Link>

          <Link
            to="/news"
            className="relative group hover:text-cyan-400 transition"
          >
            News
            <span className="absolute left-0 -bottom-0.5 w-0 h-0.5 bg-cyan-400 transition-all duration-300 group-hover:w-full"></span>
          </Link>
          <Link
            to="/portfolio"
            className="relative group hover:text-cyan-400 transition"
          >
            Portfolio
            <span className="absolute left-0 -bottom-0.5 w-0 h-0.5 bg-cyan-400 transition-all duration-300 group-hover:w-full"></span>
          </Link>
        </div>
      </div>
    </div>


      <h1 className="text-2xl mb-6 font-bold mt-10">📰 Latest Stock News </h1>

      {/* Search Bar */}
      <input
        type="text"
        placeholder="Search for company, sector, or topic..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        onKeyDown={handleKeyDown}
        className="text-black bg-white p-2 rounded mb-6 w-full max-w-96"
      />
      <button
        onClick={handleSearch}
        className="bg-blue-500 m-4 border-2 p-2 rounded-md hover:bg-blue-900"
      >
        Search
      </button>

      {news.length === 0 ? (
        <p className="text-gray-400">Loading news...</p>
      ) : (
        news.slice(0, 900).map((item, index) => (
          <div
            key={index}
            className="mb-4 bg-gray-900 p-4 rounded-xl shadow-lg"
          >
            <h2 className="text-lg font-semibold mb-1">
              {item.headline || item.title}
            </h2>
            <p className="text-sm text-gray-400 mb-2">
              {item.datetime
                ? new Date(item.datetime * 1000).toLocaleString()
                : new Date(item.publishedAt).toLocaleString()}
            </p>
            <p className="text-sm">{item.summary || item.description}</p>
            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 underline text-sm mt-1 inline-block"
            >
              Read full article
            </a>
          </div>
        ))
      )}
    </div>
  );
}

export default NewsFeed;
