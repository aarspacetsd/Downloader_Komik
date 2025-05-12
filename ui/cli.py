"""
Command-line interface for the Doudesu.
"""
from inputimeout import inputimeout, TimeoutOccurred
from rich.console import Console
from rich.prompt import IntPrompt, Prompt
from rich.table import Table

from ..core.doudesu import Doujindesu
from ..utils.converter import ImageToPDFConverter


import boto3
from botocore.exceptions import NoCredentialsError
import os

console = Console()


def get_int_input(prompt: str, min_val: int, max_val: int, default: int | None = None) -> int:
    """Get integer input with validation."""
    while True:
        try:
            if default:
                value = IntPrompt.ask(f"{prompt} [{default}]", default=default)
            else:
                value = IntPrompt.ask(prompt)

            if min_val <= value <= max_val:
                return value
            console.print(f"[red]Please enter a number between {min_val} and {max_val}[/red]")
        except ValueError:
            console.print("[red]Please enter a valid number[/red]")


def get_status_color(status: str) -> str:
    """Get color based on manga status."""
    status_colors = {"finished": "green", "publishing": "yellow"}
    return status_colors.get(status.lower(), "white")


def display_manga_details(details):
    """Display manga details in a formatted table."""
    type_color = get_type_color(details.type)
    status_color = get_status_color(details.status)
    score_color = get_score_color(details.score)

    table = Table(
        show_header=False,
        box=None,
        title="[bold cyan]Manga Details[/bold cyan]",
        title_style="bold cyan",
        border_style="blue",
    )

    table.add_column("Field", style="cyan", justify="right")
    table.add_column("Value", style="white")

    table.add_row("Title", f"[bold]{details.name}[/bold]")
    table.add_row("Author", f"[yellow]{details.author}[/yellow]")
    table.add_row("Series", f"[blue]{details.series}[/blue]")
    table.add_row("Score", f"[{score_color}]★ {details.score}[/{score_color}]")
    table.add_row("Status", f"[{status_color}]{details.status}[/{status_color}]")
    table.add_row("Type", f"[{type_color}]{details.type}[/{type_color}]")

    genres = []
    for genre in details.genre:
        color = "blue" if len(genres) % 2 == 0 else "cyan"
        genres.append(f"[{color}]{genre}[/{color}]")

    table.add_row("Genre", ", ".join(genres))
    table.add_row("Chapters", f"[green]{len(details.chapter_urls)}[/green]")

    console.print()
    console.print(table)
    console.print()


# def select_chapters(total_chapters: int) -> list[int]:
#     """Prompt user to select chapters."""
#     while True:
#         console.print("\n[cyan]Chapter Selection Options:[/cyan]")
#         console.print("1. Download all chapters")
#         console.print("2. Download specific chapter")
#         console.print("3. Download range of chapters")

#         choice = get_int_input("Select an option", 1, 3, default=1)

#         if choice == 1:
#             return list(range(total_chapters))
#         elif choice == 2:
#             chapter = get_int_input("Enter chapter number", 1, total_chapters)
#             return [chapter - 1]
#         else:
#             start = get_int_input("Enter start chapter", 1, total_chapters)
#             end = get_int_input("Enter end chapter", start, total_chapters)
#             return list(range(start - 1, end))

def upload_to_s3(file_path, bucket_name, s3_key):
    s3 = boto3.client("s3")
    try:
        s3.upload_file(file_path, bucket_name, s3_key)
        print(f"[green]Uploaded to S3: s3://{bucket_name}/{s3_key}[/green]")
        return True  # Upload successful
    except NoCredentialsError:
        print("[red]S3 upload failed: No AWS credentials found[/red]")
        return False  # Upload failed due to missing credentials
    except Exception as e:
        print(f"[red]S3 upload error: {e}[/red]")
        return False  # Upload failed due to other errors


def select_chapters(total_chapters: int) -> list[int]:
    """Prompt user to select chapters with a timeout of 10 seconds."""
    while True:
        console.print("\n[cyan]Chapter Selection Options:[/cyan]")
        console.print("1. Download all chapters")
        console.print("2. Download specific chapter")
        console.print("3. Download range of chapters")

        try:
            # Set a timeout of 10 seconds for user input
            choice = inputimeout(prompt="Select an option: ", timeout=3)

            # Convert input to an integer and check if it's valid
            choice = int(choice)
            if choice < 1 or choice > 3:
                console.print("[red]Invalid option. Please select a number between 1 and 3.[/red]")
                continue

        except TimeoutOccurred:
            console.print("\n[red]Timeout reached. Defaulting to option 1: Download all chapters.[/red]")
            choice = 1  # Default to option 1 if timeout occurs

        if choice == 1:
            return list(range(total_chapters))
        elif choice == 2:
            chapter = get_int_input("Enter chapter number", 1, total_chapters)
            return [chapter - 1]
        else:
            start = get_int_input("Enter start chapter", 1, total_chapters)
            end = get_int_input("Enter end chapter", start, total_chapters)
            return list(range(start - 1, end))

def truncate_text(text: str, max_length: int = 30) -> str:
    """Truncate text to max_length and add ellipsis if needed."""
    return text[:max_length] + "..." if len(text) > max_length else text


def get_type_color(type_str: str) -> str:
    """Get color based on manga type."""
    type_colors = {
        "doujinshi": "blue",
        "manhwa": "yellow",
    }

    type_lower = type_str.lower()
    return type_colors.get(type_lower, "white")


def get_score_color(score: float) -> str:
    """Get color based on score value."""
    score_ranges = [(9.0, "bright_green"), (8.0, "green"), (7.0, "yellow"), (6.0, "red")]

    for threshold, color in score_ranges:
        if score >= threshold:
            return color

    return "bright_red"


def run_cli():
    """Run the CLI version of the application."""
    console.print("[bold cyan]Doujindesu Downloader CLI[/bold cyan]")

    while True:
        console.print("1. Search manga")
        console.print("2. Download by URL")
        console.print("3. Exit")
        console.print("4. Auto Download All Manga from All Pages")


        choice = get_int_input("Select an option", 1, 4, default=1)
        
        if choice == 1:
            current_results = None
            while True:
                if current_results is None:
                    query = Prompt.ask("Enter search query")
                    current_results = Doujindesu.search(query)

                if not current_results or not current_results.results:
                    console.print("[red]No results found[/red]")
                    break

                table = Table(
                    show_header=True,
                    header_style="bold cyan",
                    border_style="blue",
                    title="Search Results",
                    title_style="bold cyan",
                    box=None,
                )

                table.add_column("#", justify="right", style="cyan", width=4)
                table.add_column("Title", width=35)
                table.add_column("Type", justify="center", width=12)
                table.add_column("Score", justify="center", width=8)

                for i, manga in enumerate(current_results.results, 1):
                    type_style = f"[{get_type_color(manga.type)}]{manga.type}[/]"
                    score_style = f"[{get_score_color(manga.score)}]{manga.score}[/]"

                    table.add_row(
                        f"[cyan]{i}[/]",
                        truncate_text(manga.name, 30),
                        type_style,
                        score_style,
                    )

                console.print("\n")
                console.print(table)

                console.print("\n[cyan]Navigation:[/cyan]")
                nav_options = []
                                # Menambahkan opsi untuk mendownload semua manga
                nav_options.append(("[green]Download all manga[/green]", "Download all manga"))
                nav_options.append(("[green]Select manga[/green]", "Select manga"))

                if current_results.previous_page_url:
                    nav_options.append(("[yellow]Previous page[/yellow]", "Previous page"))
                if current_results.next_page_url:
                    nav_options.append(("[yellow]Next page[/yellow]", "Next page"))

                nav_options.append(("[blue]New search[/blue]", "New search"))
                nav_options.append(("[red]Back to main menu[/red]", "Back to main menu"))

                for i, (display_text, _) in enumerate(nav_options, 1):
                    console.print(f"{i}. {display_text}")

                nav_choice = get_int_input("Select option", 1, len(nav_options))
                selected_option = nav_options[nav_choice - 1][1]

                if selected_option == "Previous page":
                    current_results = Doujindesu.get_search_by_url(current_results.previous_page_url)
                    continue
                elif selected_option == "Next page":
                    current_results = Doujindesu.get_search_by_url(current_results.next_page_url)
                    continue
                elif selected_option == "New search":
                    current_results = None
                    continue
                elif selected_option == "Back to main menu":
                    break
                elif selected_option == "Download all manga":
                    for manga_info in current_results.results:
                        try:
                            manga = Doujindesu(manga_info.url)
                            details = manga.get_details()
                            console.print(f"\n[cyan]Downloading: {details.name}[/cyan]")

                            chapters = manga.get_all_chapters()
                            if not chapters:
                                console.print("[red]No chapters found[/red]")
                                continue

                            for idx, chapter_url in enumerate(chapters):
                                console.print(f"\n[cyan]Downloading Chapter {idx + 1}...[/cyan]")

                                manga.url = chapter_url
                                images = manga.get_all_images()

                                if images:
                                    console.print(f"Found {len(images)} images")
                                    title = f"{details.name} - Chapter {idx + 1}"

                                    pdf_path = f"result/{title}.pdf"
                                    ImageToPDFConverter(images, pdf_path).convert_images_to_pdf(images, pdf_path)
                                    console.print(f"[green]Saved as: {pdf_path}[/green]")
                                    # Tambahkan bagian ini:
                                    bucket_name = "savetestingec2"
                                    s3_key = f"doujindesu/{title}.pdf"
                                    upload_to_s3(pdf_path, bucket_name, s3_key)

                                    # Optional: hapus file lokal
                                    os.remove(pdf_path)
                                else:
                                    console.print("[red]No images found in chapter[/red]")
                        except Exception as e:
                            console.print(f"[red]Error while downloading {manga_info.name}: {e!s}[/red]")
                    continue  # Kembali ke menu search setelah selesai download semua

                else:
                    selection = get_int_input(
                        "Select manga number (0 to cancel)",
                        0,
                        len(current_results.results),
                    )

                    if selection == 0:
                        continue

                    selected_manga = current_results.results[selection - 1]
                    manga = Doujindesu(selected_manga.url)

                    try:
                        details = manga.get_details()
                        console.print("\n[cyan]Manga Details:[/cyan]")
                        display_manga_details(details)

                        chapters = manga.get_all_chapters()
                        if not chapters:
                            console.print("[red]No chapters found[/red]")
                            continue

                        if len(chapters) == 1:
                            console.print("\n[cyan]Found 1 chapter[/cyan]")
                            if (
                                not Prompt.ask(
                                    "Download this chapter?",
                                    choices=["y", "n"],
                                    default="y",
                                )
                                == "y"
                            ):
                                continue

                            console.print("\n[cyan]Downloading chapter...[/cyan]")
                            chapter_url = chapters[0]
                            manga.url = chapter_url
                            images = manga.get_all_images()

                            if images:
                                console.print(f"Found {len(images)} images")
                                title = f"{details.name}"

                                pdf_path = f"result/{title}.pdf"
                                ImageToPDFConverter(images, pdf_path).convert_images_to_pdf(images, pdf_path)
                                console.print(f"[green]Saved as: {pdf_path}[/green]")
                            else:
                                console.print("[red]No images found in chapter[/red]")
                        else:
                            selected_indices = select_chapters(len(chapters))

                            for idx in selected_indices:
                                chapter_url = chapters[idx]
                                console.print(f"\n[cyan]Downloading Chapter {idx + 1}...[/cyan]")

                                manga.url = chapter_url
                                images = manga.get_all_images()

                                if images:
                                    console.print(f"Found {len(images)} images")
                                    title = f"{details.name} - Chapter {idx + 1}"

                                    pdf_path = f"result/{title}.pdf"
                                    ImageToPDFConverter(images, pdf_path).convert_images_to_pdf(images, pdf_path)
                                    console.print(f"[green]Saved as: {pdf_path}[/green]")
                                else:
                                    console.print("[red]No images found in chapter[/red]")

                    except Exception as e:
                        console.print(f"[red]Error: {e!s}[/red]")

                    break

        elif choice == 2:
            url = Prompt.ask("Enter manga URL")
            manga = Doujindesu(url)

            try:
                details = manga.get_details()
                console.print("\n[cyan]Manga Details:[/cyan]")
                display_manga_details(details)

                chapters = manga.get_all_chapters()
                if not chapters:
                    console.print("[red]No chapters found[/red]")
                    continue

                if len(chapters) == 1:
                    console.print("\n[cyan]Found 1 chapter[/cyan]")
                    if not Prompt.ask("Download this chapter?", choices=["y", "n"], default="y") == "y":
                        continue

                    console.print("\n[cyan]Downloading chapter...[/cyan]")
                    chapter_url = chapters[0]
                    manga.url = chapter_url
                    images = manga.get_all_images()

                    if images:
                        console.print(f"Found {len(images)} images")
                        title = f"{details.name}"

                        pdf_path = f"result/{title}.pdf"
                        ImageToPDFConverter(images, pdf_path).convert_images_to_pdf(images, pdf_path)
                        console.print(f"[green]Saved as: {pdf_path}[/green]")
                    else:
                        console.print("[red]No images found in chapter[/red]")
                else:
                    selected_indices = select_chapters(len(chapters))

                    for idx in selected_indices:
                        chapter_url = chapters[idx]
                        console.print(f"\n[cyan]Downloading Chapter {idx + 1}...[/cyan]")

                        manga.url = chapter_url
                        images = manga.get_all_images()

                        if images:
                            console.print(f"Found {len(images)} images")
                            title = f"{details.name} - Chapter {idx + 1}"

                            pdf_path = f"result/{title}.pdf"
                            ImageToPDFConverter(images, pdf_path).convert_images_to_pdf(images, pdf_path)
                            console.print(f"[green]Saved as: {pdf_path}[/green]")
                        else:
                            console.print("[red]No images found in chapter[/red]")

            except Exception as e:
                console.print(f"[red]Error: {e!s}[/red]")
        elif choice == 4:
            query = Prompt.ask("Enter search query for auto download")
            current_results = Doujindesu.search(query)

            while current_results and current_results.results:
                for manga_info in current_results.results:
                    try:
                        manga = Doujindesu(manga_info.url)
                        details = manga.get_details()
                        console.print(f"\n[cyan]Downloading: {details.name}[/cyan]")

                        chapters = manga.get_all_chapters()
                        if not chapters:
                            console.print("[red]No chapters found[/red]")
                            continue

                        for idx, chapter_url in enumerate(chapters):
                            console.print(f"\n[cyan]Downloading Chapter {idx + 1}...[/cyan]")

                            manga.url = chapter_url
                            images = manga.get_all_images()

                            if images:
                                console.print(f"Found {len(images)} images")
                                title = f"{details.name} - Chapter {idx + 1}"

                                pdf_path = f"result/{title}.pdf"
                                ImageToPDFConverter(images, pdf_path).convert_images_to_pdf(images, pdf_path)
                                console.print(f"[green]Saved as: {pdf_path}[/green]")

                                bucket_name = "savetestingec2"
                                s3_key = f"doujindesu/{title}.pdf"
                                
                                # Upload to S3
                                upload_success = upload_to_s3(pdf_path, bucket_name, s3_key)

                                # Only delete file if upload was successful
                                if upload_success:
                                    os.remove(pdf_path)
                                    console.print(f"[cyan]File uploaded successfully. Retaining local file for further use.[/cyan]")
                                else:
                                    console.print(f"[red]Failed to upload. Keeping local file for retry.[/red]")

                            else:
                                console.print("[red]No images found in chapter[/red]")
                    except Exception as e:
                        console.print(f"[red]Error while downloading {manga_info.name}: {e!s}[/red]")

        
        else:
            break

        if not Prompt.ask("\nDownload another manga?", choices=["y", "n"], default="y") == "y":
            break
        

    console.print("\n[cyan]Thank you for using Doujindesu Downloader![/cyan]")