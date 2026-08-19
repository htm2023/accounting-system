import pytest
from rest_framework.test import APIClient
from apps.journal_entries.models import JournalEntry, JournalEntryLine
from apps.journal_entries.services import create_journal_entry
from apps.fiscal.models import FiscalPeriod

@pytest.mark.django_db
def test_post_balanced_journal_entry(base_data, admin_user):
    entry = create_journal_entry(
        fiscal_period=base_data['period'],
        date='2026-01-10',
        description='Test entry',
        lines_data=[
            {'account': base_data['accounts']['cash'], 'debit': 1000, 'credit': 0},
            {'account': base_data['accounts']['revenue'], 'debit': 0, 'credit': 1000},
        ],
        created_by=admin_user,
        auto_post=True,
        approved_by=admin_user
    )
    assert entry.is_posted == True
    assert entry.total_debit == 1000
    assert entry.total_credit == 1000

@pytest.mark.django_db
def test_cannot_post_unbalanced_entry(base_data, admin_user):
    with pytest.raises(Exception):
        create_journal_entry(
            fiscal_period=base_data['period'],
            date='2026-01-10',
            description='Unbalanced',
            lines_data=[
                {'account': base_data['accounts']['cash'], 'debit': 1000, 'credit': 0},
            ],
            created_by=admin_user,
            auto_post=True
        )

@pytest.mark.django_db
def test_cannot_modify_posted_entry(base_data, admin_user):
    entry = create_journal_entry(
        fiscal_period=base_data['period'],
        date='2026-01-10',
        description='Posted',
        lines_data=[
            {'account': base_data['accounts']['cash'], 'debit': 500, 'credit': 0},
            {'account': base_data['accounts']['revenue'], 'debit': 0, 'credit': 500},
        ],
        created_by=admin_user,
        auto_post=True,
        approved_by=admin_user
    )
    with pytest.raises(Exception):
        entry.description = 'Changed'
        entry.save()


@pytest.mark.django_db
def test_reverse_entry_via_api_accepts_explicit_date(base_data, admin_user, accountant_user):
    entry = create_journal_entry(
        fiscal_period=base_data['period'],
        date='2026-01-10',
        description='To be reversed',
        lines_data=[
            {'account': base_data['accounts']['cash'], 'debit': 700, 'credit': 0},
            {'account': base_data['accounts']['revenue'], 'debit': 0, 'credit': 700},
        ],
        created_by=admin_user,
        auto_post=True,
        approved_by=admin_user
    )
    client = APIClient()
    client.force_authenticate(user=accountant_user)
    # بدون تمرير date صراحة، كانت create_reversal تستخدم تاريخ اليوم الفعلي
    # دائمًا، فيفشل التحقق كلما كان تاريخ اليوم الحقيقي خارج الفترة المحاسبية
    # التي يقع فيها القيد الأصلي (وهو الحال دائمًا هنا لأن الفترة 2026-01).
    resp = client.post(f'/api/journal-entries/entries/{entry.id}/reverse/', {
        'date': '2026-01-15',
    }, format='json')
    assert resp.status_code == 201, resp.data
    reversal = JournalEntry.objects.get(id=resp.data['id'])
    assert str(reversal.date) == '2026-01-15'
    assert reversal.reversed_entry_id == entry.id
