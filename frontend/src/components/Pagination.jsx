import React from 'react'
import { Pagination as BootstrapPagination } from 'react-bootstrap'
import { useTranslation } from 'react-i18next'

const Pagination = ({ currentPage, totalPages, onPageChange }) => {
  const { t } = useTranslation()

  if (totalPages <= 1) return null

  const items = []
  const maxVisible = 5
  let start = Math.max(1, currentPage - Math.floor(maxVisible / 2))
  let end = Math.min(totalPages, start + maxVisible - 1)
  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1)
  }

  for (let i = start; i <= end; i++) {
    items.push(
      <BootstrapPagination.Item
        key={i}
        active={i === currentPage}
        onClick={() => onPageChange(i)}
      >
        {i}
      </BootstrapPagination.Item>
    )
  }

  return (
    <div className="d-flex justify-content-between align-items-center mt-3">
      <div>
        {t('page')} {currentPage} / {totalPages}
      </div>
      <BootstrapPagination>
        <BootstrapPagination.Prev
          disabled={currentPage === 1}
          onClick={() => onPageChange(currentPage - 1)}
        />
        {start > 1 && <BootstrapPagination.Ellipsis onClick={() => onPageChange(Math.max(1, start - 1))} />}
        {items}
        {end < totalPages && <BootstrapPagination.Ellipsis onClick={() => onPageChange(Math.min(totalPages, end + 1))} />}
        <BootstrapPagination.Next
          disabled={currentPage === totalPages}
          onClick={() => onPageChange(currentPage + 1)}
        />
      </BootstrapPagination>
    </div>
  )
}

export default Pagination
