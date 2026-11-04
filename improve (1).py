"""
LibraTrack - Console-Based Library Management System
----------------------------------------------------
Everything is stored in Python lists (memory only), so data is lost
when the program closes.

Data layouts (each record is a list):
    book        = [book_id, title, author, isbn, total_qty, available_qty]
    borrower    = [borrower_id, name, school_id, course, contact]
    transaction = [transaction_id, book_id, borrower_id, quantity,
                   borrow_date, due_date, return_date, status,
                   borrow_librarian, return_librarian]

Transaction status is one of: "Borrowed", "Overdue", "Returned".
"""

from datetime import datetime, timedelta
import re

# ---------------------------------------------------------------
# Global data and settings
# ---------------------------------------------------------------
librarian_on_duty = ""
shift_start = ""
next_book_id = 1
next_borrower_id = 1
next_transaction_id = 1
BORROW_DAYS = 7

books = []
borrowers = []
transactions = []

# Positions inside a transaction list (makes the code easier to read)
T_ID = 0
T_BOOK = 1
T_BORROWER = 2
T_QTY = 3
T_BORROW_DATE = 4
T_DUE_DATE = 5
T_RETURN_DATE = 6
T_STATUS = 7
T_LIBRARIAN = 8
T_RETURN_LIBRARIAN = 9


# ---------------------------------------------------------------
# Input validation helpers
# ---------------------------------------------------------------
def get_nonblank(prompt):
    """Keep asking until the user types something that is not blank."""
    value = input(prompt).strip()
    while value == "":
        print("Error: This field cannot be blank.")
        value = input(prompt).strip()
    return value


def get_name(prompt):
    """Name must be non-blank and contain at least one letter."""
    while True:
        name = get_nonblank(prompt)
        if any(ch.isalpha() for ch in name):
            return name
        print("Error: A name must contain letters.")


def get_isbn(prompt):
    """ISBN must be 10 or 13 digits (hyphens allowed). Returns digits only."""
    while True:
        isbn = get_nonblank(prompt)
        digits = isbn.replace("-", "")
        if digits.isdigit() and len(digits) in (10, 13):
            return digits
        print("Error: Invalid ISBN. Enter 10 or 13 digits (hyphens allowed).")


def get_school_id(prompt):
    """School ID must follow format XX-XXXX-XXXXXX (digits and dashes only)."""
    pattern = re.compile(r'^\d{2}-\d{4}-\d{6}$')
    while True:
        school_id = get_nonblank(prompt)
        if pattern.match(school_id):
            return school_id
        print("Error: School ID must be in format XX-XXXX-XXXXXX (e.g., 02-2627-011303).")


def get_positive_int(prompt):
    """Keep asking until the user enters a whole number of 1 or more."""
    while True:
        value = get_nonblank(prompt)
        if value.isdigit() and int(value) >= 1:
            return int(value)
        print("Error: Enter a whole number of 1 or more.")


def get_yes_no(prompt):
    """Ask for yes/no and return True for yes, False for no."""
    while True:
        value = input(prompt).strip().lower()
        if value in ("y", "yes"):
            return True
        if value in ("n", "no"):
            return False
        print("Error: Please enter 'y' or 'n'.")


# ---------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------
def find_book_by_id(book_id):
    for book in books:
        if book[0] == book_id:
            return book
    return None


def find_book_by_isbn(isbn):
    for book in books:
        if book[3] == isbn:
            return book
    return None


def find_borrower_by_id(borrower_id):
    for borrower in borrowers:
        if borrower[0] == borrower_id:
            return borrower
    return None


def find_borrower_by_school_id(school_id):
    for borrower in borrowers:
        if borrower[2].lower() == school_id.lower():
            return borrower
    return None


def find_transaction_by_id(transaction_id):
    for t in transactions:
        if t[T_ID] == transaction_id:
            return t
    return None


def get_book_title(book_id):
    book = find_book_by_id(book_id)
    if book is None:
        return "Unknown"
    return book[1]


def get_borrower_name(borrower_id):
    borrower = find_borrower_by_id(borrower_id)
    if borrower is None:
        return "Unknown"
    return borrower[1]


def is_active(t):
    """A loan is active if it has not been returned yet."""
    return t[T_STATUS] == "Borrowed" or t[T_STATUS] == "Overdue"


def mark_overdue():
    """Update the status of any active loan that is past its due date."""
    today = datetime.now().strftime("%Y-%m-%d")
    for t in transactions:
        if t[T_STATUS] == "Borrowed" and t[T_DUE_DATE] < today:
            t[T_STATUS] = "Overdue"


def get_active_transactions():
    """Return a list of all loans that have not been returned yet."""
    mark_overdue()
    active = []
    for t in transactions:
        if is_active(t):
            active.append(t)
    return active


# ---------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------
def print_book_table(book_list):
    """Print the given books in a table."""
    print()
    print(f"{'ID':<5}{'Title':<24}{'Author':<20}{'ISBN':<15}"
          f"{'Total':<7}{'Avail':<7}{'Borrowed'}")
    print("-" * 85)
    for book in book_list:
        borrowed = book[4] - book[5]
        print(f"{book[0]:<5}{book[1][:22]:<24}{book[2][:18]:<20}{book[3]:<15}"
              f"{book[4]:<7}{book[5]:<7}{borrowed}")
    print()


def print_borrower_table(borrower_list=None):
    """Print borrowers in a table. Defaults to all borrowers."""
    if borrower_list is None:
        borrower_list = borrowers
    print()
    print(f"{'ID':<5}{'Name':<24}{'School ID':<16}{'Course':<12}{'Contact'}")
    print("-" * 75)
    for b in borrower_list:
        print(f"{b[0]:<5}{b[1][:22]:<24}{b[2]:<16}{b[3][:10]:<12}{b[4]}")
    print()


def print_transaction_table(transaction_list):
    """Print the given transactions in a table (used by several menus)."""
    print()
    print(f"{'TxID':<6}{'Book':<20}{'Borrower':<16}{'Qty':<5}"
          f"{'Borrowed':<12}{'Due':<12}{'Returned':<12}{'Status':<10}"
          f"{'Librarian'}")
    print("-" * 105)
    for t in transaction_list:
        returned = t[T_RETURN_DATE]
        if returned is None:
            returned = "-"
        librarian = t[T_LIBRARIAN]
        if t[T_RETURN_LIBRARIAN] is not None:
            librarian = f"{t[T_LIBRARIAN]} / ret: {t[T_RETURN_LIBRARIAN]}"
        print(f"{t[T_ID]:<6}{get_book_title(t[T_BOOK])[:18]:<20}"
              f"{get_borrower_name(t[T_BORROWER])[:14]:<16}{t[T_QTY]:<5}"
              f"{t[T_BORROW_DATE]:<12}{t[T_DUE_DATE]:<12}{returned:<12}"
              f"{t[T_STATUS]:<10}{librarian}")
    print()


# ---------------------------------------------------------------
# Main features
# ---------------------------------------------------------------
def login():
    """Ask for the librarian's name at the start of the shift."""
    global librarian_on_duty, shift_start

    print("=" * 50)
    print("  LibraTrack - Librarian Shift Login")
    print("=" * 50)

    librarian_on_duty = get_name("Librarian name: ")
    shift_start = datetime.now().strftime("%Y-%m-%d %I:%M %p")

    print(f"\nLogged in as: {librarian_on_duty}")
    print(f"Shift started: {shift_start}\n")
    input("Press Enter to continue...")


# --- Book Management ---
def add_book():
    """Feature 1: add a new book (duplicate ISBNs are not allowed)."""
    global next_book_id

    print("\n--- Add Book ---")
    title = get_nonblank("Title: ")
    author = get_name("Author: ")
    isbn = get_isbn("ISBN: ")

    if find_book_by_isbn(isbn) is not None:
        print("Error: A book with that ISBN already exists.\n")
        return

    copies = get_positive_int("Total quantity: ")

    books.append([next_book_id, title, author, isbn, copies, copies])
    print(f"Added '{title}' (Book ID {next_book_id}) with {copies} copy(ies).\n")
    next_book_id += 1


def edit_book():
    """Feature 2: edit an existing book record."""
    print("\n--- Edit Book ---")
    if not books:
        print("No books in the catalog yet.\n")
        return

    print_book_table(books)
    book = find_book_by_id(get_positive_int("Enter Book ID to edit: "))
    if book is None:
        print("Error: Book ID not found.\n")
        return

    print(f"\nSelected: {book[1]} by {book[2]}")
    print("Leave blank and press Enter to keep the current value.\n")

    new_title = input(f"New Title [{book[1]}]: ").strip()
    new_author = input(f"New Author [{book[2]}]: ").strip()
    new_isbn = input(f"New ISBN [{book[3]}]: ").strip()
    new_total_str = input(f"New Total Quantity [{book[4]}]: ").strip()

    if new_title:
        book[1] = new_title
    if new_author:
        if any(ch.isalpha() for ch in new_author):
            book[2] = new_author
        else:
            print("Error: Author name must contain letters. Change ignored.\n")
    if new_isbn:
        digits = new_isbn.replace("-", "")
        if not (digits.isdigit() and len(digits) in (10, 13)):
            print("Error: ISBN must be 10 or 13 digits. Change ignored.\n")
        elif new_isbn != book[3] and find_book_by_isbn(digits):
            print("Error: Another book already uses that ISBN. Change ignored.\n")
        else:
            book[3] = digits
    if new_total_str:
        if not (new_total_str.isdigit() and int(new_total_str) > 0):
            print("Error: Total quantity must be a positive whole number. Change ignored.\n")
        else:
            new_total = int(new_total_str)
            borrowed = book[4] - book[5]
            if new_total < borrowed:
                print(f"Error: Cannot set total to {new_total} because {borrowed} copy(ies) are currently borrowed.\n")
            else:
                book[4] = new_total
                book[5] = new_total - borrowed

    print("Book record updated successfully.\n")


def search_book():
    """Feature 3: search and show details plus the book's full history."""
    print("\n--- Search Book ---")
    keyword = get_nonblank("Search by title, author, or ISBN: ")
    mark_overdue()

    results = []
    keyword_lower = keyword.lower()
    keyword_digits = keyword_lower.replace("-", "")

    for book in books:
        in_title = keyword_lower in book[1].lower()
        in_author = keyword_lower in book[2].lower()
        in_isbn = keyword_digits != "" and keyword_digits in book[3]
        if in_title or in_author or in_isbn:
            results.append(book)

    if len(results) == 0:
        print("No matching books found.\n")
        return

    for book in results:
        borrowed = book[4] - book[5]
        print("\n" + "=" * 50)
        print(f"Book ID          : {book[0]}")
        print(f"Title            : {book[1]}")
        print(f"Author           : {book[2]}")
        print(f"ISBN             : {book[3]}")
        print(f"Total copies     : {book[4]}")
        print(f"Available copies : {book[5]}")
        print(f"Borrowed copies  : {borrowed}")

        history = [t for t in transactions if t[T_BOOK] == book[0]]
        print("\nBorrowing and return history:")
        if len(history) == 0:
            print("  This book has never been borrowed.")
        else:
            print_transaction_table(history)
    print()


def view_all_books():
    """Feature 4: show every book in a table."""
    print("\n--- All Books ---")
    if not books:
        print("No books in the catalog yet.\n")
        return
    print_book_table(books)


def remove_book():
    """Feature 5: remove a book record from the catalog."""
    print("\n--- Remove Book ---")
    if not books:
        print("No books in the catalog yet.\n")
        return

    print_book_table(books)
    book = find_book_by_id(get_positive_int("Enter Book ID to remove: "))
    if book is None:
        print("Error: Book ID not found.\n")
        return

    active_for_book = [t for t in transactions if t[T_BOOK] == book[0] and is_active(t)]
    if active_for_book:
        print(f"Error: Cannot remove '{book[1]}' because it has active borrowing transactions.\n")
        return

    if get_yes_no(f"Are you sure you want to remove '{book[1]}'? (y/n): "):
        books.remove(book)
        print("Book removed successfully.\n")
    else:
        print("Removal cancelled.\n")


# --- Borrower Management ---
def register_borrower():
    """Feature 6: register a borrower (duplicate school IDs not allowed)."""
    global next_borrower_id

    print("\n--- Register Borrower ---")
    name = get_name("Borrower name: ")
    school_id = get_school_id("School ID number: ")
    course = get_nonblank("Course: ")
    contact = get_nonblank("Contact number: ")

    if find_borrower_by_school_id(school_id) is not None:
        print("Error: A borrower with that school ID already exists.\n")
        return

    borrowers.append([next_borrower_id, name, school_id, course, contact])
    print(f"Registered {name} (Borrower ID {next_borrower_id}).\n")
    next_borrower_id += 1


def edit_borrower():
    """Feature 7: edit an existing borrower record."""
    print("\n--- Edit Borrower ---")
    if not borrowers:
        print("No borrowers registered yet.\n")
        return

    print_borrower_table()
    borrower = find_borrower_by_id(get_positive_int("Enter Borrower ID to edit: "))
    if borrower is None:
        print("Error: Borrower ID not found.\n")
        return

    print(f"\nSelected: {borrower[1]}")
    print("Leave blank and press Enter to keep the current value.\n")

    new_name = input(f"New Name [{borrower[1]}]: ").strip()
    new_school_id = input(f"New School ID [{borrower[2]}]: ").strip()
    new_course = input(f"New Course [{borrower[3]}]: ").strip()
    new_contact = input(f"New Contact [{borrower[4]}]: ").strip()

    if new_name:
        if any(ch.isalpha() for ch in new_name):
            borrower[1] = new_name
        else:
            print("Error: Name must contain letters. Change ignored.\n")

    if new_school_id:
        if not re.match(r'^\d{2}-\d{4}-\d{6}$', new_school_id):
            print("Error: School ID must be in format XX-XXXX-XXXXXX. Change ignored.\n")
        elif new_school_id.lower() != borrower[2].lower() and find_borrower_by_school_id(new_school_id):
            print("Error: Another borrower already uses that School ID. Change ignored.\n")
        else:
            borrower[2] = new_school_id

    if new_course:
        borrower[3] = new_course
    if new_contact:
        borrower[4] = new_contact

    print("Borrower record updated successfully.\n")


def search_borrowers():
    """Feature 8: search for borrowers by keyword."""
    print("\n--- Search Borrowers ---")
    if not borrowers:
        print("No borrowers registered yet.\n")
        return

    keyword = get_nonblank("Enter keyword (name, school ID, course, or contact): ").strip().lower()
    if not keyword:
        print("Error: Keyword cannot be blank.\n")
        return

    results = []
    for b in borrowers:
        if (keyword in b[1].lower() or
            keyword in b[2].lower() or
            keyword in b[3].lower() or
            keyword in b[4].lower()):
            results.append(b)

    if results:
        print(f"\nFound {len(results)} result(s):")
        print_borrower_table(results)
    else:
        print("No matching borrowers found.\n")


def view_all_borrowers():
    """Feature 9: show every registered borrower."""
    print("\n--- All Borrowers ---")
    if not borrowers:
        print("No borrowers registered yet.\n")
        return
    print_borrower_table()


def remove_borrower():
    """Feature 10: remove a borrower record."""
    print("\n--- Remove Borrower ---")
    if not borrowers:
        print("No borrowers registered yet.\n")
        return

    print_borrower_table()
    borrower = find_borrower_by_id(get_positive_int("Enter Borrower ID to remove: "))
    if borrower is None:
        print("Error: Borrower ID not found.\n")
        return

    active_for_borrower = [t for t in transactions if t[T_BORROWER] == borrower[0] and is_active(t)]
    if active_for_borrower:
        print(f"Error: Cannot remove '{borrower[1]}' because they have unreturned books.\n")
        return

    if get_yes_no(f"Are you sure you want to remove '{borrower[1]}'? (y/n): "):
        borrowers.remove(borrower)
        print("Borrower removed successfully.\n")
    else:
        print("Removal cancelled.\n")


# --- Borrowing and Returning ---
def borrow_book():
    """Feature 11: lend one or more copies of a book to a borrower."""
    global next_transaction_id

    print("\n--- Borrow Book ---")
    if not books:
        print("Error: No books in the catalog yet.\n")
        return
    if not borrowers:
        print("Error: No borrowers registered yet.\n")
        return

    print_book_table(books)
    book = find_book_by_id(get_positive_int("Enter Book ID: "))
    if book is None:
        print("Error: Book ID not found.\n")
        return
    if book[5] == 0:
        print(f"Error: '{book[1]}' has no available copies right now.\n")
        return

    print_borrower_table()
    borrower = find_borrower_by_id(get_positive_int("Enter Borrower ID: "))
    if borrower is None:
        print("Error: Borrower ID not found.\n")
        return

    quantity = get_positive_int("Number of copies to borrow: ")
    if quantity > book[5]:
        print(f"Error: Only {book[5]} copy(ies) available. "
              "Request a smaller quantity.\n")
        return

    borrow_date = datetime.now()
    due_date = borrow_date + timedelta(days=BORROW_DAYS)

    transactions.append([
        next_transaction_id,
        book[0],
        borrower[0],
        quantity,
        borrow_date.strftime("%Y-%m-%d"),
        due_date.strftime("%Y-%m-%d"),
        None,
        "Borrowed",
        librarian_on_duty,
        None
    ])
    book[5] = book[5] - quantity

    print(f"\nTransaction ID : {next_transaction_id}")
    print(f"Book           : {book[1]}")
    print(f"Borrower       : {borrower[1]}")
    print(f"Quantity       : {quantity}")
    print(f"Borrow date    : {borrow_date.strftime('%Y-%m-%d')}")
    print(f"Due date       : {due_date.strftime('%Y-%m-%d')}")
    print(f"Processed by   : {librarian_on_duty}\n")
    next_transaction_id += 1


def return_book():
    """Feature 12: return all copies of one active loan."""
    print("\n--- Return Book ---")
    active = get_active_transactions()

    if not active:
        print("There are no active loans to return.\n")
        return

    print_transaction_table(active)
    t = find_transaction_by_id(get_positive_int("Enter Transaction ID to return: "))

    if t is None:
        print("Error: Transaction ID not found.\n")
        return
    if t[T_STATUS] == "Returned":
        print("Error: That transaction was already returned.\n")
        return

    book = find_book_by_id(t[T_BOOK])

    t[T_RETURN_DATE] = datetime.now().strftime("%Y-%m-%d")
    t[T_STATUS] = "Returned"
    t[T_RETURN_LIBRARIAN] = librarian_on_duty
    book[5] = book[5] + t[T_QTY]

    print(f"Returned {t[T_QTY]} copy(ies) of '{book[1]}' "
          f"from {get_borrower_name(t[T_BORROWER])}.")
    print(f"Return date: {t[T_RETURN_DATE]}")
    print(f"Processed by: {librarian_on_duty}\n")


# --- Tracking and Reports ---
def view_borrowed_books():
    """Feature 13: show every active loan (Borrowed and Overdue)."""
    print("\n--- Currently Borrowed Books ---")
    active = get_active_transactions()
    if not active:
        print("No borrowed books right now.\n")
        return
    print_transaction_table(active)


def view_returned_books():
    """Feature 14: show all returned transactions."""
    print("\n--- Returned Books ---")
    returned = [t for t in transactions if t[T_STATUS] == "Returned"]
    if not returned:
        print("No returned book records to display.\n")
        return
    print_transaction_table(returned)


def view_overdue_books():
    """Feature 15: show all overdue transactions."""
    print("\n--- Overdue Books ---")
    mark_overdue()
    overdue = [t for t in transactions if t[T_STATUS] == "Overdue"]
    if not overdue:
        print("No overdue books right now.\n")
        return
    print_transaction_table(overdue)


def generate_report():
    """Feature 16: show library totals."""
    mark_overdue()

    total_copies = sum(book[4] for book in books)
    available_copies = sum(book[5] for book in books)
    borrowed_copies = total_copies - available_copies

    active_loans = len([t for t in transactions if t[T_STATUS] == "Borrowed"])
    overdue_loans = len([t for t in transactions if t[T_STATUS] == "Overdue"])
    returned_count = len([t for t in transactions if t[T_STATUS] == "Returned"])

    print("\n" + "=" * 50)
    print("          LIBRATRACK SUMMARY REPORT")
    print("=" * 50)
    print(f"Librarian on duty : {librarian_on_duty}")
    print(f"Shift started at  : {shift_start}")
    print(f"Report generated  : {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")
    print("-" * 50)
    print(f"Book titles              : {len(books)}")
    print(f"Total physical copies    : {total_copies}")
    print(f"Available copies         : {available_copies}")
    print(f"Borrowed copies          : {borrowed_copies}")
    print("-" * 50)
    print(f"Registered borrowers     : {len(borrowers)}")
    print("-" * 50)
    print(f"Total transactions       : {len(transactions)}")
    print(f"  - Borrowed (on time)   : {active_loans}")
    print(f"  - Returned             : {returned_count}")
    print(f"  - Overdue              : {overdue_loans}")
    print("=" * 50 + "\n")


# ---------------------------------------------------------------
# Menu
# ---------------------------------------------------------------
def show_menu():
    print("=" * 45)
    print("        LibraTrack Main Menu")
    print(f"        On duty: {librarian_on_duty}")
    print("=" * 45)
    print("  [1]  Add Book")
    print("  [2]  Edit Book")
    print("  [3]  Search Books")
    print("  [4]  View All Books")
    print("  [5]  Remove Book")
    print("  [6]  Register Borrower")
    print("  [7]  Edit Borrower")
    print("  [8]  Search Borrowers")
    print("  [9]  View All Borrowers")
    print("  [10] Remove Borrower")
    print("  [11] Borrow Book")
    print("  [12] Return Book")
    print("  [13] View Borrowed Books")
    print("  [14] View Returned Books")
    print("  [15] View Overdue Books")
    print("  [16] Summary Report")
    print("  [0]  Exit")
    print("=" * 45)


def main_menu():
    running = True

    while running:
        show_menu()
        choice = input("Choose an option: ").strip()

        if choice == "1":
            add_book()
        elif choice == "2":
            edit_book()
        elif choice == "3":
            search_book()
        elif choice == "4":
            view_all_books()
        elif choice == "5":
            remove_book()
        elif choice == "6":
            register_borrower()
        elif choice == "7":
            edit_borrower()
        elif choice == "8":
            search_borrowers()
        elif choice == "9":
            view_all_borrowers()
        elif choice == "10":
            remove_borrower()
        elif choice == "11":
            borrow_book()
        elif choice == "12":
            return_book()
        elif choice == "13":
            view_borrowed_books()
        elif choice == "14":
            view_returned_books()
        elif choice == "15":
            view_overdue_books()
        elif choice == "16":
            generate_report()
        elif choice == "0":
            running = False
            print(f"\nEnding shift for {librarian_on_duty}. Goodbye!")
        else:
            print("Error: Invalid choice. Enter a number from 0 to 16.\n")


if __name__ == "__main__":
    login()
    main_menu()
