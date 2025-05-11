from doudesu import Doujindesu

# Search for manga
results = Doujindesu.search("manga name")
for manga in results.results:
    print(f"Title: {manga.name}")
    print(f"URL: {manga.url}")

manga = Doujindesu("https://doujindesu.tv/manga/your-manga-url")
details = manga.get_details()
chapters = manga.get_all_chapters()

# Get chapter images
manga.url = chapters[1]  # Set to specific chapter
images = manga.get_all_images()