"""
Department ID to English slug mapping configuration

This file maps department IDs from the rag_departments table to readable English slugs
for use as Qdrant collection names. This avoids encoding issues with Korean department names.
"""

# Department ID to English slug mapping
# Based on rag_departments table data as of 2025-09-19
DEPARTMENT_SLUGS = {
    1: "1",        # WM 현장팀
    2: "2",        # LEAN 현장팀 (inactive)
    3: "3",        # 외부 연계
    4: "4",        # 품질관리팀 (inactive)
    5: "5",        # 안전관리팀
    6: "6",        # 정비관리팀
    7: "7",        # 보고관리팀
    9: "9",        # asdaskdknjk (test entry)
    10: "10",      # general
    11: "11",      # pcp
    12: "12",      # PCP
}

# Reverse mapping for lookup
SLUG_TO_DEPARTMENT_ID = {slug: dept_id for dept_id, slug in DEPARTMENT_SLUGS.items()}


def get_slug_for_department_id(department_id: int) -> str:
    """
    Get English slug for a department ID

    Args:
        department_id: Department ID from rag_departments table

    Returns:
        English slug for collection naming

    Raises:
        KeyError: If department ID is not found in mapping
    """
    if department_id not in DEPARTMENT_SLUGS:
        raise KeyError(f"No slug mapping found for department ID {department_id}")

    return DEPARTMENT_SLUGS[department_id]


def get_department_id_for_slug(slug: str) -> int:
    """
    Get department ID for an English slug

    Args:
        slug: English slug

    Returns:
        Department ID from rag_departments table

    Raises:
        KeyError: If slug is not found in mapping
    """
    if slug not in SLUG_TO_DEPARTMENT_ID:
        raise KeyError(f"No department ID found for slug '{slug}'")

    return SLUG_TO_DEPARTMENT_ID[slug]


def get_all_slugs() -> list[str]:
    """Get list of all available slugs"""
    return list(DEPARTMENT_SLUGS.values())


def get_all_department_ids() -> list[int]:
    """Get list of all mapped department IDs"""
    return list(DEPARTMENT_SLUGS.keys())