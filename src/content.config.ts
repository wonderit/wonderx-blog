import { defineCollection, z } from 'astro:content';

const CATEGORIES = [
  'ai-automation',    // AI 자동화
  'side-project',     // 사이드 프로젝트
  'dev-log',          // 개발 일지
  'social',           // 소셜링 / 소개팅
  'tutorial',         // 튜토리얼 / 가이드
] as const;

const blog = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    tags: z.array(z.string()).default([]),
    category: z.enum(CATEGORIES).default('dev-log'),
    heroImage: z.string().optional(),
    draft: z.boolean().default(false),
  }),
});

export const collections = { blog };
