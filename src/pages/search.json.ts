import { getCollection } from 'astro:content';

export async function GET() {
  const posts = await getCollection('blog');

  const searchData = posts
    .filter((post) => !post.data.draft)
    .sort((a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf())
    .map((post) => ({
      title: post.data.title,
      description: post.data.description || '',
      url: `/blog/${post.id.replace(/\.md$/, '')}`,
      tags: post.data.tags || [],
      category: post.data.category || '',
      date: post.data.pubDate.toISOString().slice(0, 10),
    }));

  return new Response(JSON.stringify(searchData), {
    headers: {
      'Content-Type': 'application/json',
    },
  });
}
