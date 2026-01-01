/*import axios from 'axios';

export const fetchNewsData = async (keyword) => {
    try {
     const res = await axios.get(`https://gnews.io/api/v4/search?q=${keyword}&token=${import.meta.env.VITE_GNEWS_API_KEY}&lang=en`
    );   
    return res.data.articles;
    }catch (error){
        console.log("error in fetching gnews" , error.message);
        return [];

    }
};




export const filterNewsByCompany = (articles, symbol) => {
  const lowerSymbol = symbol.toLowerCase();

  return articles.filter(article =>
    (article.title && article.title.toLowerCase().includes(lowerSymbol)) ||
    (article.description && article.description.toLowerCase().includes(lowerSymbol)) ||
    (article.content && article.content.toLowerCase().includes(lowerSymbol))
  );
};

*//*
import axios from 'axios';
export async function fetchNewsData(company) {
  let res = await fetch(`http://localhost:5000/news?company=${company}`);
  let data = await res.json();

  // Agar result empty hai, to fallback try karo
  if (!data || data.length === 0) {
    if (company.toLowerCase() === "tcs") {
      res = await fetch(`http://localhost:5000/news?company=Tata Consultancy Services`);
      data = await res.json();
    }
  }
  return data;
}

export function filterNewsByCompany(articles, query) {
  const q = query.toLowerCase();
  return articles.filter(a =>
    a.title?.toLowerCase().includes(q) ||
    a.description?.toLowerCase().includes(q) ||
    a.content?.toLowerCase().includes(q) ||
    // ✅ extra check for TCS shortcut
    (q.includes("tcs") && a.title?.toLowerCase().includes("tata consultancy"))
  );
}*/




export async function fetchNewsData(company) {
  try {
    const res = await fetch(`http://localhost:5000/news?company=${company}`);
    const data = await res.json();
    return data.articles || [];  // ✅ Always return array
  } catch (e) {
    console.error("News fetch failed", e);
    return [];
  }
}

export function filterNewsByCompany(articles, query) {
  if (!Array.isArray(articles)) return [];  // ✅ avoid filter crash
  return articles.filter(a =>
    a.title?.toLowerCase().includes(query.toLowerCase()) ||
    a.description?.toLowerCase().includes(query.toLowerCase())
  );
}
