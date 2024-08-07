from pydantic import BaseModel


class PagePaginationInfo(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int

    @classmethod
    def build(cls, page: int, page_size: int, total: int) -> "PagePaginationInfo":
        return cls(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=(total + page_size - 1) // page_size,
        )
