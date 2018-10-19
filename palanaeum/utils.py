from django.http import HttpRequest


def is_contributor(request: HttpRequest) -> bool:
    """
    Defines is a user from given request should see non-approved things.
    """
    return hasattr(request, 'user') and request.user.is_authenticated

def page_numbers_to_show(paginator, page):
    """
    page_numbers_to_show is a pagination utility function intended to replace
    the vanilla 'paginator.page_range()'. It is used when paginating very large
    result sets, to limit the displayed pages to be within a few pages of the
    current/active page.

    Returns a sequence of page numbers to be displayed. Uses '-1' as a sentinel
    value to indicate a break in the sequence, when a '...' (ellipse) is
    intended be displayed.
    """
    # implementation from https://www.technovelty.org/web/skipping-pages-with-djangocorepaginator.html

    # pages_wanted stores the pages we want to see, e.g.
    #  - first and second page always
    #  - two pages before selected page
    #  - the selected page
    #  - two pages after selected page
    #  - last two pages always
    #
    # Turning the pages into a set removes duplicates for edge
    # cases where the "context pages" (before and after the
    # selected) overlap with the "always show" pages.
    pages_wanted = set([1,2,
                        page-2, page-1,
                        page,
                        page+1, page+2,
                        paginator.num_pages-1, paginator.num_pages])

    # The intersection with the page_range trims off the invalid
    # pages outside the total number of pages we actually have.
    # Note that includes invalid negative and >page_range "context
    # pages" which we added above.
    to_show = set(paginator.page_range).intersection(pages_wanted)
    to_show = sorted(to_show)

    # skip_pages will keep a list of page numbers from
    # pages_to_show that should have a skip-marker inserted
    # after them.  For flexibility this is done by looking for
    # anywhere in the list that doesn't increment by 1 over the
    # last entry.
    skip_pages = [ x[1] for x in zip(to_show[:-1],
                                     to_show[1:])
                   if (x[1] - x[0] != 1) ]

    # Each page in skip_pages should be follwed by a skip-marker
    # sentinel (e.g. -1).
    for i in skip_pages:
        to_show.insert(to_show.index(i), -1)

    return to_show
