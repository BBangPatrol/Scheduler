import os
import pymysql
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google import genai

load_dotenv()

def getDbConnection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        charset="utf8mb4"
    )


def getUpdatedStoreIds(conn):
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    start = datetime.combine(yesterday, datetime.min.time())
    end = datetime.combine(today, datetime.min.time())

    sql = """
        SELECT DISTINCT bakery_id
        FROM review
        WHERE created_at >= %s
          AND created_at < %s
          AND deleted_at IS NULL
    """

    with conn.cursor() as cursor:
        cursor.execute(sql, (start, end))
        rows = cursor.fetchall()

    return [row[0] for row in rows]


def getAllReviews(conn, store):
    sql = """
        SELECT rating, content
        FROM review
        WHERE bakery_id = %s
          AND deleted_at IS NULL
        ORDER BY created_at ASC
    """

    with conn.cursor() as cursor:
        cursor.execute(sql, (store,))
        rows = cursor.fetchall()

    return rows


def summarizeReviews(reviews):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    review_text = "\n".join(
        f"- 평점: {rating} / 리뷰: {content}"
        for rating, content in reviews
    )

    prompt = f"""
다음은 한 빵집에 작성된 사용자 리뷰들이다.

리뷰 전체를 종합하여 사용자가 이 빵집의 특징을 빠르게 파악할 수 있도록 요약해라.

조건:
- 리뷰에 실제로 등장한 내용만 사용한다.
- 긍정적인 특징과 부정적인 특징을 함께 반영한다.
- 여러 리뷰에서 반복적으로 언급된 특징을 우선한다.
- 특정 리뷰 하나의 의견을 전체 의견처럼 과장하지 않는다.
- 자연스러운 한국어 문장으로 작성한다.
- 2~3문장 이내로 작성한다.
- "리뷰를 종합하면", "사용자들은" 같은 불필요한 서두는 사용하지 않는다.

리뷰:
{review_text}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt
    )

    return response.text.strip()


def update(conn, store, summary):
    sql = """
        UPDATE bakery
        SET summary = %s
        WHERE id = %s
    """

    with conn.cursor() as cursor:
        cursor.execute(sql, (summary, store))

    conn.commit()


def main():
    conn = getDbConnection()

    try:
        stores = getUpdatedStoreIds(conn)

        for store in stores:
            try:
                reviews = getAllReviews(conn, store)

                if not reviews:
                    continue

                summary = summarizeReviews(reviews)
                update(conn, store, summary)

                print(f"[SUCCESS] store={store}")

            except Exception as e:
                conn.rollback()
                print(f"[ERROR] store={store}, error={e}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()