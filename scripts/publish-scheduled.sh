#!/bin/bash
# 예약 발행 스크립트 — draft: true → false 후 git push
# cron/launchd에서 자정에 실행

set -e

BLOG_DIR="/Users/wonderit/workplace/wonderx/wonderx-blog"
LOG_FILE="$BLOG_DIR/scripts/publish.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

cd "$BLOG_DIR"
log "=== 예약 발행 시작 ==="

# 오늘 날짜 (pubDate가 오늘인 draft 찾기)
TODAY=$(date '+%Y-%m-%d')
log "오늘 날짜: $TODAY"

PUBLISHED=0

for file in src/content/blog/*.md; do
    [ -f "$file" ] || continue

    # draft: true인 파일 중 pubDate가 오늘이거나 과거인 것만
    if grep -q "^draft: true" "$file"; then
        PUB_DATE=$(grep "^pubDate:" "$file" | sed "s/pubDate: *['\"]*//" | sed "s/['\"].*//")

        if [ -n "$PUB_DATE" ] && [ "$PUB_DATE" \<= "$TODAY" ]; then
            log "발행: $file (pubDate: $PUB_DATE)"

            # draft: true → draft: false
            sed -i '' 's/^draft: true/draft: false/' "$file"

            TITLE=$(grep "^title:" "$file" | sed "s/title: *['\"]*//" | sed "s/['\"].*//")
            git add "$file"
            PUBLISHED=$((PUBLISHED + 1))

            log "  → draft: false 변경 완료 ($TITLE)"
        fi
    fi
done

if [ $PUBLISHED -gt 0 ]; then
    git commit -m "publish: 예약 발행 ${PUBLISHED}개 포스트 ($TODAY)"
    git push origin main
    log "git push 완료 (${PUBLISHED}개 발행)"
else
    log "발행할 포스트 없음"
fi

log "=== 예약 발행 완료 ==="
