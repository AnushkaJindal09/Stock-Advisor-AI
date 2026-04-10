



export async function fetchNewsData(company) {
  try {
    const res = await fetch(`https://stock-backend-gsyw.onrender.com/news?company=${company}`);
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
