def getDbConnection():
    pass


def getUpdatedStoreIds(conn):
    pass


def getAllReviews(conn, store):
    pass


def summarizeReviews(reviews):
    pass


def update(conn, store, summary):
    pass


def main():
    conn = getDbConnection()

    try:
        stores = getUpdatedStoreIds(conn)
        for store in stores:
            reviews = getAllReviews(conn, store)
            summary = summarizeReviews(reviews)
            update(conn, store, summary)

    finally:
        conn.close()


if __name__ == "__main__":
    main()