/**
 * YouTube Innertube API - Extract comments, transcripts, and channel data
 * No API key needed. No quota limits.
 * 
 * Full toolkit: https://github.com/spinov001-art/youtube-data-tools
 * Pre-built tools: https://github.com/spinov001-art/awesome-web-scraping-2026
 * Tutorial: https://dev.to/0012303/youtubes-secret-innertube-api-extract-comments-transcripts-channel-data-without-api-keys-mil
 */

const INNERTUBE_CONTEXT = {
  client: { clientName: 'WEB', clientVersion: '2.20240101.00.00', hl: 'en', gl: 'US' }
};

// Extract video ID from any YouTube URL format
function extractVideoId(url) {
  if (/^[a-zA-Z0-9_-]{11}$/.test(url)) return url;
  try {
    const u = new URL(url);
    if (u.hostname.includes('youtube.com') && u.searchParams.has('v')) return u.searchParams.get('v');
    if (u.hostname === 'youtu.be') return u.pathname.slice(1);
    if (u.pathname.startsWith('/shorts/')) return u.pathname.split('/')[2];
  } catch {}
  return null;
}

// Fetch comments via Innertube API
async function getComments(videoId, maxComments = 50) {
  const page = await fetch(`https://www.youtube.com/watch?v=${videoId}`, {
    headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0' }
  });
  const html = await page.text();
  const data = JSON.parse(html.match(/var ytInitialData\s*=\s*({.+?});\s*<\/script>/s)[1]);
  const apiKey = (html.match(/"INNERTUBE_API_KEY":"([^"]+)"/) || [])[1];
  
  // Find comments continuation token
  const contents = data?.contents?.twoColumnWatchNextResults?.results?.results?.contents;
  let token = null;
  for (const item of contents || []) {
    const sc = item?.itemSectionRenderer?.contents;
    for (const c of sc || []) {
      if (c.continuationItemRenderer?.continuationEndpoint?.continuationCommand?.token) {
        token = c.continuationItemRenderer.continuationEndpoint.continuationCommand.token;
        break;
      }
    }
  }
  
  if (!token) return [];
  
  const res = await fetch(`https://www.youtube.com/youtubei/v1/next?key=${apiKey}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ context: INNERTUBE_CONTEXT, continuation: token })
  });
  const json = await res.json();
  
  const comments = [];
  const mutations = json?.frameworkUpdates?.entityBatchUpdate?.mutations || [];
  for (const m of mutations) {
    const p = m?.payload?.commentEntityPayload;
    if (!p) continue;
    comments.push({
      author: p.properties?.authorButtonA11y || '',
      text: p.properties?.content?.content || '',
      likes: parseInt(p.toolbar?.likeCountNotliked || '0') || 0,
      publishedAt: p.properties?.publishedTime || ''
    });
    if (comments.length >= maxComments) break;
  }
  
  return comments;
}

// Usage
const videoId = extractVideoId('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
getComments(videoId, 20).then(comments => {
  console.log(`Found ${comments.length} comments`);
  comments.forEach(c => console.log(`[${c.likes} likes] ${c.author}: ${c.text.slice(0, 80)}`));
});
